import logging
import traceback
from typing import Type, Optional, Any

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.language_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.tools import BaseTool
from langchain_community.utilities.sql_database import SQLDatabase
from ..states.internet_archive import InternetArchiveState

class BaseInternetArchiveTool(BaseModel):
    """Base tool for interacting with a SQL database."""

    db: SQLDatabase = Field(exclude=True)
    llm: BaseChatModel = Field(exclude=True)
    graph: CompiledStateGraph = Field(exclude=True)
    logger: logging.Logger|None = Field(exclude=True)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

class _InternetArchiveSearchToolInput(BaseModel):
    tool_input: str = Field("", description="An Search Term for Internet Archive")


class InternetArchiveSearchTool(BaseInternetArchiveTool, BaseTool):  # type: ignore[override, override]
    """Tool for general internet archive search."""

    name: str = "internet_archive_search"
    description: str = "Input is an search term, an json object with results matching the search term, and a json object with filtered results matching the search term."
    args_schema: Type[BaseModel] = _InternetArchiveSearchToolInput

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    def _run(
        self,
        tool_input: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        internet_archive_state = InternetArchiveState(
            query=tool_input,
        )

        ret:Optional[str] = None

        try :
            ret = self.graph.invoke(internet_archive_state)
        except Exception as ex:
            e = traceback.format_exc()
            self.logger.error(f"Error invoking internet archive search tool: {e}")
            return f"{e}"

        return ret