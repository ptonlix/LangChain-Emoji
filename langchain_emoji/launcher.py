"""FastAPI app creation, logger configuration and main API routes."""

import logging
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from injector import Injector
from langchain_emoji.paths import docs_path
from langchain_emoji.settings.settings import Settings
from langchain_emoji.server.emoji.emoji_router import emoji_router
from langchain_emoji.server.vector_store.vector_store_router import vector_store_router
from langchain_emoji.server.trace.trace_router import trace_router
from langchain_emoji.server.health.health_router import health_router
from langchain_emoji.server.config.config_router import (
    config_router_no_auth,
    config_router,
)

logger = logging.getLogger(__name__)


def create_app(root_injector: Injector) -> FastAPI:
    # Start the API
    with open(docs_path / "description.md") as description_file:
        description = description_file.read()

        tags_metadata = [
            {
                "name": "Emoji",
                "description": "AI-enabled Emoji engine",
            },
            {
                "name": "VectorStore",
                "description": "Store the emoji vectorically",
            },
            {
                "name": "Config",
                "description": "Obtain and modify project configuration files",
            },
            {
                "name": "Health",
                "description": "Simple health API to make sure the server is up and running.",
            },
        ]

        async def bind_injector_to_request(request: Request) -> None:
            request.state.injector = root_injector

        app = FastAPI(dependencies=[Depends(bind_injector_to_request)])

        def custom_openapi() -> dict[str, Any]:
            if app.openapi_schema:
                return app.openapi_schema
            openapi_schema = get_openapi(
                title="Langchain-SearXNG",
                description=description,
                version="0.1.0",
                summary="AI Emoji Argue Agent 🚀 基于LangChain的开源表情包斗图Agent",
                contact={
                    "url": "https://github.com/ptonlix",
                },
                license_info={
                    "name": "Apache 2.0",
                    "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
                },
                routes=app.routes,
                tags=tags_metadata,
            )
            openapi_schema["info"]["x-logo"] = {
                "url": "https://lh3.googleusercontent.com/drive-viewer"
                "/AK7aPaD_iNlMoTquOBsw4boh4tIYxyEuhz6EtEs8nzq3yNkNAK00xGj"
                "E1KUCmPJSk3TYOjcs6tReG6w_cLu1S7L_gPgT9z52iw=s2560"
            }

            app.openapi_schema = openapi_schema
            return app.openapi_schema

        app.openapi = custom_openapi  # type: ignore[method-assign]

        app.include_router(emoji_router)
        app.include_router(trace_router)
        app.include_router(vector_store_router)
        app.include_router(health_router)
        app.include_router(config_router_no_auth)
        app.include_router(config_router)

        settings = root_injector.get(Settings)
        if settings.server.cors.enabled:
            logger.debug("Setting up CORS middleware")
            app.add_middleware(
                CORSMiddleware,
                allow_credentials=settings.server.cors.allow_credentials,
                allow_origins=settings.server.cors.allow_origins,
                allow_origin_regex=settings.server.cors.allow_origin_regex,
                allow_methods=settings.server.cors.allow_methods,
                allow_headers=settings.server.cors.allow_headers,
            )

        return app
