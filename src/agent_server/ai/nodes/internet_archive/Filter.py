import json
import logging
from typing import Any, List

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableSerializable, RunnableConfig, Runnable
from pydantic import PrivateAttr, BaseModel, Field

from ...prompts.interface import IPromptTemplateFactoryInterface
from ...states.internet_archive import InternetArchiveState

class FilterResultsStructuredOutput(BaseModel):
   filtered_results: List[str] = Field(description="List of item identifiers filtered as relevant")

class FilterNode(Runnable):
    llm: BaseChatModel
    prompt_factory: IPromptTemplateFactoryInterface
    logger: logging.Logger

    def __init__(self, llm, prompt_factory, logger):
        self.logger = logger or logging.getLogger(__name__)
        self.llm = llm
        self.prompt_factory = prompt_factory

    def invoke(self, state: InternetArchiveState, config: Any = None, **kwargs: Any) -> dict:
        results = state.get("results")
        results_len = len(state.get("results", []))
        self.logger.info(f"FilterNode invoked with results len: {results_len}")
        if not results or results_len == 0:
            return {
                **state,
                "filtered_results": [],
                "error": state.get("error") or "No results to filter"
            }

        try:
            # First, try structured output via Pydantic
            try:
                # Second, try structured llm
                llm_structured = self.llm.with_structured_output(FilterResultsStructuredOutput)
                prompt = self.prompt_factory.create(
                    query=state["query"],
                    results=json.dumps(state["results"]),
                )
                response = FilterResultsStructuredOutput(**llm_structured.invoke(prompt))
                filtered_results = getattr(response, "filtered_results", [])

            except Exception as e:
                # Fallback to JsonOutputParser with format instructions
                self.logger.error(f"FilterNode structured output failed: {e}, fallback to JsonOutputParser")
                parser = JsonOutputParser(pydantic_object=FilterResultsStructuredOutput)
                prompt = self.prompt_factory.create(
                    query=state["query"],
                    results=json.dumps(state["results"]),
                    parser=parser,
                )
                llm_response = self.llm.invoke(prompt)
                parsed: dict = parser.parse(llm_response.content)
                filtered_results = parsed.get("filtered_results", [])

            if not isinstance(filtered_results, list):
                filtered_results = []

            return {**state, "filtered_results": filtered_results}
        except Exception as e:
            return {
                **state,
                "filtered_results": state.get("results", []),  # Fall back to unfiltered results
                "error": f"Filter error: {str(e)}"
            }