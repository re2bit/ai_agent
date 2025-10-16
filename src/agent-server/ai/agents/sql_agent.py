import logging

from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import HumanMessage
from langchain_core.messages.base import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt.chat_agent_executor import create_react_agent
from pydantic import BaseModel


class SqlAgentMessage(BaseModel):
    messages: list[BaseMessage]

class SQLAgent:
    langfuse_config: RunnableConfig
    executor: CompiledStateGraph
    logger: logging.Logger

    def __init__(
            self,
            db : SQLDatabase,
            llm: BaseLanguageModel,
            prompt: str,
            langfuse_config: RunnableConfig,
            logger: logging.Logger
    ):
        self.langfuse_config = langfuse_config
        self.executor = create_react_agent(llm,
            SQLDatabaseToolkit(
                db=db,
                llm=llm
            ).get_tools()
        , prompt=prompt)
        self.logger = logger

    def ask(self, query: str):
        return self.executor.invoke(
            SqlAgentMessage(messages=[HumanMessage(query)]),
            config=self.langfuse_config
        )

    def stream(self, query: str):
        return self.executor.astream(
            SqlAgentMessage(messages=[HumanMessage(query)]),
            config=self.langfuse_config,
            stream_mode = "values"
        )

