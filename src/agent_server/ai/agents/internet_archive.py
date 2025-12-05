import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.messages.base import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt.chat_agent_executor import create_react_agent
from pydantic import BaseModel
from sqlalchemy import Engine
from ..graphs.internet_archive import InternetArchiveGraphBuilder
from ..nodes.internet_archive.Search import SearchNode
from ..nodes.internet_archive.Finder import FinderNode
from ..nodes.internet_archive.Metadata import MetadataNode
from ..nodes.internet_archive.Filter import FilterNode
from ..nodes.internet_archive.FileFinder import FileFinderNode
from ..nodes.internet_archive.Downloader import DownloaderNode
from ..nodes.internet_archive.Database import DatabaseNode
from ..prompts.internet_archive import FilterPromptFactory, FileFinderPromptFactory, FinderPromptFactory
from ..prompts.internet_archive import AgentPromptFactory
from ..toolkits.internet_archive import InternetArchiveToolkit
from ..tools.internet_archive import InternetArchiveSearchTool
from ...adapters.internet_archive import InternetArchiveSearchWrapper


class InternetArchiveMessage(BaseModel):
    messages: list[BaseMessage]

class AgentFactory:
    llm:BaseChatModel
    logger:logging.Logger
    langfuse_config:RunnableConfig
    engine:Engine
    cache_dir: str | None
    data_dir: str | None

    def __init__(
            self,
            llm:BaseChatModel,
            logger:logging.Logger,
            engine: Engine,
            langfuse_config:RunnableConfig,
            k:int=40,
            cache_dir:str=None,
            data_dir:str=None
    ):
        self.cache_dir = cache_dir
        self.engine = engine
        self.data_dir = data_dir
        self.llm=llm
        self.logger=logger
        self.k=k
        self.langfuse_config=langfuse_config

    def create(self):
        agent = create_react_agent(
            self.llm,
            InternetArchiveToolkit(
                tools=[
                    InternetArchiveSearchTool(
                        llm=self.llm,
                        logger=self.logger,
                        graph=self.create_graph()
                    )
                ]
            ).get_tools()
            , prompt=AgentPromptFactory().create()
        )

        return InternetArchiveAgent(
            langfuse_config=self.langfuse_config,
            logger=self.logger,
            agent=agent
        )

    def create_graph(self) -> CompiledStateGraph[Any, Any, Any, Any]:
        ia = InternetArchiveSearchWrapper(
                    k=self.k,
                    _logger=self.logger
                )
        return InternetArchiveGraphBuilder(
            search_node=SearchNode(
                _logger=self.logger,
                ia=ia,
            ),
            filter_node=FilterNode(
                logger=self.logger,
                llm=self.llm,
                prompt_factory=FilterPromptFactory()
            ),
            metadata_node=MetadataNode(
                _logger=self.logger,
                ia=ia
            ),
            finder_node=FinderNode(
                llm=self.llm,
                logger=self.logger,
                prompt_factory=FinderPromptFactory(),
            ),
            file_finder_node=FileFinderNode(
                llm=self.llm,
                logger=self.logger,
                prompt_factory=FileFinderPromptFactory()
            ),
            downloader_node=DownloaderNode(
                logger=self.logger,
                ia=ia,
                data_dir=self.data_dir
            ),
            database_node=DatabaseNode(
                engine=self.engine,
                logger=self.logger
            ),
            logger=self.logger,
            cache_dir=self.cache_dir,
        ).build()


class InternetArchiveAgent:
    langfuse_config: RunnableConfig
    agent: CompiledStateGraph
    logger: logging.Logger

    def __init__(
            self,
            langfuse_config: RunnableConfig,
            logger: logging.Logger,
            agent: CompiledStateGraph
    ):
        self.langfuse_config = langfuse_config
        self.agent = agent
        self.logger = logger

    def ask(self, query: str) -> str:
        self.logger.info(f"Agent invoked with: {query}")
        result = self.agent.invoke(
            InternetArchiveMessage(messages=[HumanMessage(query)]),
            config=self.langfuse_config
        )
        self.logger.info(f"Agent Result: {len(result)}")

        return result

    def stream(self, query: str):
        return self.agent.astream(
            InternetArchiveMessage(messages=[HumanMessage(query)]),
            config=self.langfuse_config,
            stream_mode = "values"
        )

