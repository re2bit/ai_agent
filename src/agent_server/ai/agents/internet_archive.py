import logging
from typing import Any

from langchain_community.utilities import SQLDatabase
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage
from langchain_core.messages.base import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt.chat_agent_executor import create_react_agent
from pydantic import BaseModel

from ..graphs.internet_archive import InternetArchiveGraphBuilder
from ..nodes.internet_archive import FilterNode, MetadataNode, SearchNode
from ..prompts.internet_archive import FilterPromptFactory
from ..prompts.internet_archive import AgentPromptFactory
from ..toolkits.internet_archive import InternetArchiveToolkit
from ..tools.internet_archive import InternetArchiveSearchTool
from ...adapters.internet_archive import InternetArchiveSearchWrapper


class InternetArchiveMessage(BaseModel):
    messages: list[BaseMessage]

class AgentFactory:
    llm:BaseLanguageModel
    logger:logging.Logger
    db:SQLDatabase
    langfuse_config:RunnableConfig
    data_root: str | None

    def __init__(
            self,
            llm:BaseLanguageModel,
            logger:logging.Logger,
            db:SQLDatabase,
            langfuse_config:RunnableConfig,
            k:int=40,
            data_root:str=None
    ):
        self.data_root = data_root
        self.llm=llm
        self.logger=logger
        self.db=db
        self.k=k
        self.langfuse_config=langfuse_config

    def create(self):
        agent = create_react_agent(
            self.llm,
            InternetArchiveToolkit(
                tools=[
                    InternetArchiveSearchTool(
                        llm=self.llm,
                        db=self.db,
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
        return InternetArchiveGraphBuilder(
            search_node=SearchNode(
                _logger=self.logger,
                ia=InternetArchiveSearchWrapper(
                    k=self.k,
                    _logger=self.logger
                )
            ),
            filter_node=FilterNode(
                _logger=self.logger,
                llm=self.llm,
                prompt_template=FilterPromptFactory()
            ),
            metadata_node=MetadataNode(
                _logger=self.logger,
                ia=InternetArchiveSearchWrapper(
                    k=self.k,
                    _logger = self.logger
                )
            ),
            logger=self.logger,
            data_root=self.data_root,
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

