import json
import logging
from typing import Any

from langchain_core.runnables import RunnableSerializable
from pydantic import PrivateAttr

from ...states.internet_archive import InternetArchiveState
from ....adapters.internet_archive import InternetArchiveSearchWrapper


#TODO: this is not a RunnableSerializable, but it's a Runnable' Refactor. This whole RunnerSerializable is problematic
class SearchNode(RunnableSerializable):

    ia: InternetArchiveSearchWrapper
    _logger: logging.Logger = PrivateAttr()

    def __init__(self, **data):
        logger = data.pop("_logger", None)
        super().__init__(**data)
        self._logger = logger or logging.getLogger(__name__)

    def invoke(self, state: InternetArchiveState, config: Any = None, **kwargs) -> dict:
        query = state.get("query")
        self._logger.info(f"SearchNode invoked with state: {query}")
        if not query:
            return {**state, "results": [], "error": state.get("error") or "Missing query"}

        try:
            result = self.ia.search(query)
            result_dict = json.loads(str(result))
            items = result_dict.get("items", [])
            result_len = len(items)
            self._logger.info(f"SearchNode result: {result_len}")

            return {
                **state,
                "results": items,
                "error": result_dict.get("error"),
            }
        except Exception as e:
            return {
                **state,
                "results": [],
                "error": f"Search error: {str(e)}",
            }