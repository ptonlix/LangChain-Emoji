"""FastAPI app creation, logger configuration and main API routes."""

from langchain_emoji.di import global_injector
from langchain_emoji.launcher import create_app

app = create_app(global_injector)
