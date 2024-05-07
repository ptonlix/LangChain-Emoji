from pathlib import Path

from langchain_emoji.constants import PROJECT_ROOT_PATH
from langchain_emoji.settings.settings import settings


def _absolute_or_from_project_root(path: str) -> Path:
    if path.startswith("/"):
        return Path(path)
    return PROJECT_ROOT_PATH / path


docs_path: Path = PROJECT_ROOT_PATH / "docs"

local_data_path: Path = _absolute_or_from_project_root(
    settings().data.local_data_folder
)
