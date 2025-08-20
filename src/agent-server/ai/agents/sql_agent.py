from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt.chat_agent_executor import create_react_agent
from langchain_core.messages.base import BaseMessage
from pydantic import BaseModel

class SqlAgentMessage(BaseModel):
    messages: list[BaseMessage]

class SQLAgent:
    langfuse_config: RunnableConfig
    executor: CompiledStateGraph

    def __init__(
            self,
            db : SQLDatabase,
            llm: BaseLanguageModel,
            prompt: str,
            langfuse_config: RunnableConfig,
    ):
        self.langfuse_config = langfuse_config
        self.executor = create_react_agent(llm,
            SQLDatabaseToolkit(
                db=db,
                llm=llm
            ).get_tools()
        , prompt=prompt)

    def ask(self, query: str):

        msg = SqlAgentMessage(
            messages=[HumanMessage(query)]
        )
        result = self.executor.invoke(msg, config=self.langfuse_config)

        return result

