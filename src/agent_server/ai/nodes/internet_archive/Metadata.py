import logging
from typing import Any, List, Tuple, Optional, Iterator

from langchain_core.runnables import RunnableSerializable
from pydantic import PrivateAttr

from ...states.internet_archive import InternetArchiveState
from ....adapters.internet_archive import InternetArchiveSearchWrapper


class MetadataNode(RunnableSerializable):

    ia: InternetArchiveSearchWrapper
    _logger: logging.Logger = PrivateAttr()

    def __init__(self, **data):
        logger = data.pop("_logger", None)
        super().__init__(**data)
        self._logger = logger or logging.getLogger(__name__)

    def receive_metadata(self,filtered:List[str]) -> Iterator[Tuple[Optional[str], Optional[dict], bool]]:
        for item_id in filtered:
            try:
                metadata = self.ia.item_metadata(item_id)
                yield item_id, metadata, True
            except Exception as e:
                error = str(e)
                self._logger.error(f"receive Metadata Error: {error}")
                break

        yield None, None, False

    def invoke(self, state: InternetArchiveState, config: Any = None, **kwargs) -> dict:
        filtered = state.get("filtered_results") or []
        filter_len = len(filtered)
        self._logger.info(f"MetadataNode invoked with state: {filter_len}")

        if len(filtered) == 0:
            return {
                **state,
                "metadata": {},
                "error": state.get("error") or "No filtered results to get metadata for",
            }

        metadata: dict[str, Any] = {}
        try:
            for (item_id, item, success) in self.receive_metadata(filtered):
                if success:
                    metadata[item_id] = item
                else:
                    break

            meta_len = len(metadata)
            self._logger.info(f"MetadataNode result: {meta_len}")
            return {**state, "metadata": metadata}
        except Exception as e:
            error = str(e)
            self._logger.error(f"MetadataNode Error: {error}")
            return {**state, "metadata": {}, "error": f"Metadata error: {error}"}
