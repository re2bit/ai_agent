import logging
from typing import Any, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableConfig, Runnable
from langchain_core.runnables.utils import Output
from pydantic import BaseModel, Field

from ...prompts.interface import IPromptTemplateFactoryInterface
from ...states.internet_archive import InternetArchiveState


class FinderNodeStructuredOutput(BaseModel):
   is_this_entry_relevant: bool = Field(description="Whether the entry is relevant to the query")

class FinderNode(Runnable):
    llm: BaseChatModel
    prompt_factory: IPromptTemplateFactoryInterface
    logger: logging.Logger

    def __init__(
            self,
            llm: BaseChatModel,
            prompt_factory: IPromptTemplateFactoryInterface,
            logger: logging.Logger = None
    ):
        self.logger = logger or logging.getLogger(__name__)
        self.llm = llm
        self.prompt_factory = prompt_factory

    def invoke(self, state: InternetArchiveState, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Output:
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
        error = state.get("error") or []

        for name, metadata_info in metadata.items():
            try:
                actual_metadata = metadata_info.get("metadata") or {}

                try:
                    llm = self.llm.with_structured_output(FinderNodeStructuredOutput)

                    prompt = self.prompt_factory.create(
                        query=state["query"],
                        name=name,
                        metadata=actual_metadata,
                    )
                    response: FinderNodeStructuredOutput = FinderNodeStructuredOutput(**llm.invoke(prompt))

                except Exception as e:
                    self.logger.error(f"Error setting structured output: {e}, fallback to Json output parser")

                    parser = JsonOutputParser(pydantic_object=FinderNodeStructuredOutput)

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
                    error.append(str(e))

        result = {
            **state,
            "entries_to_consider":entries_to_consider,
        }

        if error:
            result["error"] = error

        return result