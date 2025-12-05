import logging
from typing import Any, List, Optional, Dict

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableConfig, Runnable
from langchain_core.runnables.utils import Output
from pydantic import BaseModel, Field

from ...prompts.interface import IPromptTemplateFactoryInterface
from ...states.internet_archive import InternetArchiveState


class FileFinderNodeStructuredOutput(BaseModel):
   pdfs_to_download: List[str] = Field(description="List of PDF file names to download for this item")

class FileFinderNode(Runnable):
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
        entries_to_consider = state.get("entries_to_consider") or []
        metadata = state.get("metadata") or {}
        entries_to_consider_length = len(entries_to_consider)
        metadata_length = len(metadata)
        self.logger.info(f"File Finder Node invoked with entries len: {entries_to_consider_length} within metadata len: {metadata_length}")
        if not entries_to_consider or entries_to_consider_length == 0:
            return {
                **state,
                "pdfs_to_download": [],
                "error": state.get("error") or "No entries_to_consider information to check"
            }

        #aggregated_pdfs: List[str] = []
        aggregated_pdfs: Dict[str, List[str]] = {}
        error = state.get("error") or []

        for name in entries_to_consider:
            try:
                entry = metadata.get(name) or {}
                files = entry.get("files") or []

                if not files:
                    # No Files present
                    error.append(f"No files present for entry {name}")
                    continue

                try:
                    llm_structured = self.llm.with_structured_output(FileFinderNodeStructuredOutput)

                    prompt = self.prompt_factory.create(
                        query=state["query"],
                        name=name,
                        files=files,
                    )
                    response_obj: FileFinderNodeStructuredOutput = FileFinderNodeStructuredOutput(**llm_structured.invoke(prompt))
                    selected = getattr(response_obj, "pdfs_to_download", [])

                except Exception as e:
                    self.logger.error(f"FileFinderNode structured output failed: {e}, fallback to JsonOutputParser")

                    parser = JsonOutputParser(pydantic_object=FileFinderNodeStructuredOutput)

                    prompt = self.prompt_factory.create(
                        query=state["query"],
                        name=name,
                        files=files,
                        parser=parser
                    )

                    llm_response = self.llm.invoke(prompt)
                    parsed: dict = parser.parse(llm_response.content)
                    selected = parsed.get("pdfs_to_download", [])

                # Sanity check and aggregate
                if isinstance(selected, list):
                    # make sure they are strings
                    selected = [s for s in selected if isinstance(s, str)]
                    if name not in aggregated_pdfs:
                        aggregated_pdfs[name] = []
                    aggregated_pdfs[name].extend(selected)
            except Exception as e:
                error.append(str(e))

        result = {
            **state,
            "pdfs_to_download": aggregated_pdfs,
        }

        if error:
            result["error"] = error

        return result