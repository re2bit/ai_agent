import logging
import sys
from pprint import pformat
from typing import Any

class LoggerFactory:
    def __call__(self, level: int = logging.INFO):
        try:
            logger = logging.getLogger(__name__)
            logger.setLevel(level)
            formatter = logging.Formatter(
                "%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%(levelname)s] %(name)s: %(message)s")

            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

            # file_handler = logging.FileHandler("info.log")
            # file_handler.setFormatter(formatter)
            # logger.addHandler(file_handler)

            def _debug_var(obj: Any,
                           name: str = "var",
                           level: int = logging.DEBUG,
                           *,
                           width: int = 100,
                           compact: bool = True,
                           sort_dicts: bool = True,
                           ) -> None:
                if not logger.isEnabledFor(level):
                    return
                logger.log(level, "%s:\n%s", name, pformat(obj, width=width, compact=compact, sort_dicts=sort_dicts))

            logger.debug_var = _debug_var

            return logger
        except Exception:
            return None