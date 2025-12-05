import logging
import logging
import os
from pathlib import Path
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig, Runnable
from langchain_core.runnables.utils import Output

from ...states.internet_archive import InternetArchiveState
from ....adapters.internet_archive import InternetArchiveSearchWrapper

DATA_ROOT = "/data/ia/data"

class DownloaderNode(Runnable):
    target_dir: Path
    logger: logging.Logger
    ia: InternetArchiveSearchWrapper

    def __init__(
            self,
            ia: InternetArchiveSearchWrapper,
            data_dir: Path|None = None,
            logger: logging.Logger = None
    ):
        data_dir = data_dir if data_dir is Path else Path(DATA_ROOT)
        self.ia = ia
        self.logger = logger or logging.getLogger(__name__)
        if not data_dir.exists():
            raise AttributeError(f"Target directory {data_dir} does not exist")
        if not data_dir.is_dir():
            raise AttributeError(f"Target directory {data_dir} is not a directory")
        if not os.access(data_dir, os.W_OK):
            raise AttributeError(f"Target directory {data_dir} is not writable")
        self.target_dir = data_dir

    def invoke(self, state: InternetArchiveState, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Output:
       pdfs_to_download = state.get("pdfs_to_download") or {}
       error = state.get("error") or []

       for identifier, files in pdfs_to_download.items():
           try:
               self.ia.download(
                   identifier=identifier,
                   files=files,
                   target_dir=self.target_dir,
               )
               self.logger.info(f"Downloading: {files}")
           except Exception as e:
              error.append(str(e))

       result = {
           **state,
       }

       if error:
           result["error"] = error

       return result