import json
import logging
from typing import Any, List, Tuple, Optional, Iterator

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableSerializable, RunnableConfig, Runnable
from langchain_core.runnables.utils import Input, Output
from pydantic import PrivateAttr, BaseModel, Field

from ..prompts.interface import IPromptTemplateFactoryInterface
from ..prompts.internet_archive import FilterPromptFactory
from ..states.internet_archive import InternetArchiveState
from ...adapters.internet_archive import InternetArchiveSearchWrapper


class FilterNode(RunnableSerializable):
    llm: BaseChatModel
    prompt_template: FilterPromptFactory
    _logger: logging.Logger = PrivateAttr()

    def __init__(self, **data):
        logger = data.pop("_logger", None)
        super().__init__(**data)
        self._logger = logger or logging.getLogger(__name__)

    def invoke(self, input: dict, config: Any = None) -> dict:
        state = input
        results = state.get("results")
        results_len = len(state.get("results", []))
        self._logger.info(f"FilterNode invoked with results len: {results_len}")
        if not results or results_len == 0:
            return {
                **state,
                "filtered_results": [],
                "error": state.get("error") or "No results to filter"
            }

        try:
            # Format the prompt with the query and results
            formatted_prompt = self.prompt_template.create(
                query=state["query"],
                results=json.dumps(state["results"])
            )

            # Get the filtered results from the LLM
            llm_response = self.llm.invoke(formatted_prompt)

            # Try to parse the response as JSON
            try:
                filtered_results = json.loads(llm_response.content)
                if not isinstance(filtered_results, list):
                    filtered_results = []

                return {
                    **state,
                    "filtered_results": filtered_results
                }
            except json.JSONDecodeError:
                # If JSON parsing fails, return the original results
                return {
                    **state,
                    "filtered_results": state["results"],
                    "error": "Failed to parse LLM response as JSON"
                }
        except Exception as e:
            return {
                **state,
                "filtered_results": state["results"],  # Fall back to unfiltered results
                "error": f"Filter error: {str(e)}"
            }

class SearchNode(RunnableSerializable):

    ia: InternetArchiveSearchWrapper
    _logger: logging.Logger = PrivateAttr()

    def __init__(self, **data):
        logger = data.pop("_logger", None)
        super().__init__(**data)
        self._logger = logger or logging.getLogger(__name__)

    def invoke(self, state: InternetArchiveState, config: Any = None) -> dict:
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

    def invoke(self, input: dict, config: Any = None) -> dict:
        state: dict = input
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

class FilterNodeStructuredOutput(BaseModel):
   is_this_entry_relevant: bool = Field(description="Whether the entry is relevant to the query")

class FinderNode(Runnable):
    llm: BaseChatModel
    prompt_factory: IPromptTemplateFactoryInterface
    logger: logging.Logger

    def __init__(self, llm, prompt_factory, logger):
        self.logger = logger or logging.getLogger(__name__)
        self.llm = llm
        self.prompt_factory = prompt_factory

    def invoke(self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Output:
        state: dict = input

        metadata = state.get("metadata") or {}
        metadata_length = len(metadata)
        self.logger.info(f"Finder Node invoked with results len: {metadata_length}")
        if not metadata or metadata_length == 0:
            return {
                **state,
                "entries_to_consider": [],
                "error": state.get("error") or "No metadata information to check"
            }

        entries_to_consider = []
        error = state.get("error") or None

        for name, metadata_info in metadata.items():
            try:
                actual_metadata = metadata_info.get("metadata") or {}

                try:
                    llm = self.llm.with_structured_output(FilterNodeStructuredOutput)

                    prompt = self.prompt_factory.create(
                        query=state["query"],
                        name=name,
                        metadata=actual_metadata,
                    )
                    response: FilterNodeStructuredOutput = llm.invoke(prompt)

                except Exception as e:
                    self.logger.error(f"Error setting structured output: {e}, fallback to Json output parser")

                    parser = JsonOutputParser(pydantic_object=FilterNodeStructuredOutput)

                    prompt = self.prompt_factory.create(
                        query=state["query"],
                        name=name,
                        metadata=actual_metadata,
                        parser=parser
                    )

                    llm_response = self.llm.invoke(prompt)

                    response: dict = parser.parse(llm_response.content)

                if response.get("is_this_entry_relevant"):
                   entries_to_consider.append(name)
            except Exception as e:
                if error is None:
                    error = str(e)
                else:
                    error = "\n".join([error, str(e)])

        result = {
            **state,
            "entries_to_consider":entries_to_consider,
        }

        if error:
            result["error"] = error

        return result