import aiohttp
from typing import Optional, Dict, Any
from langchain_emoji.settings.settings import settings
from pydantic import ValidationError
import logging
import asyncio
import streamlit as st
import uuid
import base64
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)


class ApiRequest:
    def __init__(self, loop: asyncio.AbstractEventLoop, base_url: str):
        self.base_url = base_url
        self.loop = loop
        self.timeout = aiohttp.ClientTimeout(total=10 * 60)
        self.session = None

    async def initialize_session(self):
        self.session = aiohttp.ClientSession(loop=self.loop, timeout=self.timeout)

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        if self.session is None:
            await self.initialize_session()
        url = f"{self.base_url}{endpoint}"
        headers = headers or {}
        headers["Content-Type"] = "application/json"
        try:
            async with self.session.request(
                method, url, params=params, json=json, headers=headers
            ) as response:
                return await response.json()
        except aiohttp.ServerTimeoutError as timeout_error:
            logger.warning(
                f"Timeout error in {method} request to {url}: {timeout_error}"
            )
            raise
        except aiohttp.ClientError as e:
            logger.warning(f"Error in {method} request to {url}: {e}")
            raise
        except Exception as e:
            logger.warning(f"Unexpected error in {method} request to {url}: {e}")
            raise

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        return await self._request("GET", endpoint, params=params, headers=headers)

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        return await self._request("POST", endpoint, json=data, headers=headers)

    async def close(self):
        await self.session.close()


class EmojiApiHandler(ApiRequest):
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__(
            loop=loop, base_url="http://127.0.0.1:" + str(settings().server.port)
        )
        self.accesstoken = settings().server.auth.secret

    async def emoji(
        self,
        data: Dict,
        endpoint: str = "/v1/emoji",
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict | None:
        headers = headers or {}
        headers["Authorization"] = f"Basic {self.accesstoken}"
        logger.info(data)
        try:
            resp_dict = await self.post(endpoint=endpoint, data=data, headers=headers)
            # logger.info(resp_dict)
            return resp_dict
        except ValidationError as e:
            logger.warning(f"Unexpected ValidationError error in UserReg request : {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error in UserReg request : {e}")
            return None


async def handler_progress_bar(progress_bar):
    for i in range(8):
        progress_bar.progress(10 * i)
        await asyncio.sleep(0.1)


def decodebase64(context: str):
    img_data = base64.b64decode(context)  # 解码时只要内容部分

    image = Image.open(BytesIO(img_data))
    return image


def fetch_emoji(prompt: str, llm: str, progress_bar):

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    emoji_api = EmojiApiHandler(loop)

    async def emoji_request():
        try:
            response = await emoji_api.emoji(
                data={"prompt": prompt, "req_id": str(uuid.uuid4()), "llm": llm}
            )
            return response.get("data")
        finally:
            await emoji_api.close()

    try:
        emoji_task = loop.create_task(emoji_request())
        progress_task = loop.create_task(handler_progress_bar(progress_bar))
        result = loop.run_until_complete(asyncio.gather(emoji_task, progress_task))
        return result[0]
    finally:
        loop.close()


def area_image(area_placeholder, image, filename):
    col1, col2, col3 = area_placeholder.columns([1, 3, 1])
    with col1:
        st.write(" ")

    with col2:
        st.image(
            image=image,
            caption=filename,
            use_column_width=True,
        )
    with col3:
        st.write(" ")


st.subheader("🥳 LangChain-Emoji")
st.markdown(
    "基于LangChain的开源表情包斗图Agent [Github](https://github.com/ptonlix/LangChain-Emoji) [作者: Baird](https://github.com/ptonlix)"
)

with st.container():
    image_path = "../docs/pic/logo.jpg"

    with st.container():
        image_placeholder = st.empty()
        area_placeholder = st.empty()
        content_placeholder = st.empty()
        area_image(area_placeholder, image_path, "帝阅DeepRead")

    with st.form("emoji_form"):
        st.write("Emoji Input")
        select_llm = st.radio(
            "Please select a LLM",
            ["ChatGPT", "ZhipuAI", "DeepSeek"],
            captions=["OpenAI", "智谱清言", "深度求索"],
        )
        llm_mapping = {
            "ChatGPT": "openai",
            "ZhipuAI": "zhipuai",
            "DeepSeek": "deepseek",
        }
        llm = llm_mapping[select_llm]

        prompt = st.text_input("Enter Emoji Prompt:", value="今天很开心～")

        submitted = st.form_submit_button("Submit", help="点击获取最佳表情包")
        if submitted:
            bar = st.progress(0)
            response = fetch_emoji(prompt, llm, bar)
            bar.progress(100)
            base64_str = response["emojidetail"]["base64"]
            filename = response["emojiinfo"]["filename"]
            content = response["emojiinfo"]["content"]
            area_image(area_placeholder, decodebase64(base64_str), filename)
            content_placeholder.write(content)
