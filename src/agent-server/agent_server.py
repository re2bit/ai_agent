"""
title: Agent API Server
description: FastAPI server for the agent
"""

import os
import json
import requests
import internetarchive
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import (
    BaseModel,
    Field,
    PrivateAttr,
    model_validator,
)
from langchain_core.messages import HumanMessage
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langchain_community.utilities import SQLDatabase
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities.searx_search import SearxSearchWrapper
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent



class InternetArchiveSearchResults(dict):
    def __init__(self, params: dict):
        super().__init__()
        """Take a raw result from Searx and make it into a dict like object."""
        res = dict()
        res['items'] = []
        res['k'] = params["k"]
        res['q'] = params["q"]

        self.__dict__ = res

    def __str__(self) -> str:
        try:
            ret = dict()
            ret['items'] = self.get("items", [])
            if len(ret['items']) == 0:
                ret['error'] = "No good search result found"
            ret['q'] = self.get("q")
            ret['k'] = self.get("k")

            return json.dumps(ret)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    @property
    def items(self) -> Any:
        return self.get("items")

    def add_item(self, item: dict):
        if "items" not in self:
            self["items"] = []
        self["items"].append(item.get("identifier"))


class InternetArchiveSearchWrapper(BaseModel):
    """
    Wrapper Internet Archive search Python Library.
    """

    _result: InternetArchiveSearchResults = PrivateAttr()
    params: dict = Field()
    query_suffix: Optional[str] = ""
    k: int = 100

    @model_validator(mode="before")
    @classmethod
    def validate_params(cls, values: Dict) -> Any:
        """Validate that custom internetarchive search params are merged with default ones."""
        user_params = values.get("params", {})
        default_params = {}
        values["params"] = {**default_params, **user_params}
        return values

    def _internetarchive_query(self, params: dict) -> InternetArchiveSearchResults:
        """Actual request to searx API."""
        res = InternetArchiveSearchResults(params)

        search = internetarchive.search_items(params["q"])
        for item in search:
            res.add_item(item)

        self._result = res
        return res

    def run(
        self,
        query: str,
        **kwargs: Any,
    ) -> str:
        """
        Run a query through Internet Archive API and parse results.
        """
        _params = {
            "q": query,
            "k": self.k,
        }
        params = {**self.params, **_params, **kwargs}

        if self.query_suffix and len(self.query_suffix) > 0:
            params["q"] += " " + self.query_suffix

        res = self._internetarchive_query(params)

        return res

# Load environment variables
load_dotenv('.env')


debug_port = os.getenv("DEBUG")
if debug_port.isnumeric():
    import pydevd_pycharm
    pydevd_pycharm.settrace(
        'host.docker.internal',
        port=int(debug_port),
        stdoutToServer=True,
        stderrToServer=True
    )

# Initialize Langfuse client
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST")
)

langfuse_config = None

try:
    langfuse.auth_check()
    print("Langfuse client is authenticated and ready!")
    langfuse_handler = CallbackHandler()
    langfuse_config = {"callbacks": [langfuse_handler]}
except:
    print("Authentication failed. Please check your credentials and host.")


# Ensure data directory exists
data_dir = os.path.join(os.getcwd(), "data")
os.makedirs(data_dir, exist_ok=True)

# Path to the database file
db_path = os.path.join(data_dir, "Chinook.db")

# Download Chinook database if not exists
if not os.path.isfile(db_path):
    url = os.getenv("CHINOOK_DB_URL")

    response = requests.get(url)

    if response.status_code == 200:
        with open(db_path, "wb") as file:
            file.write(response.content)

        print("File downloaded successfully")

    else:
        print("Failed to download the file")
        print(response.status_code)

# Initialize database and LLM
db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
model = os.getenv("LLM_MODEL")  # Default: qwen2.5, Alternative: llama3.2:3b
llm = ChatOllama(model=model, base_url=os.getenv("OLLAMA_BASE_URL"))


# Get system prompt from hub
#prompt = hub.pull("langchain-ai/sql-agent-system-prompt")
# Local so i dont need an internet connection
prompt = PromptTemplate.from_template("""SYSTEM
You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.
You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for the relevant columns given the question.
You have access to tools for interacting with the database.
Only use the below tools. Only use the information returned by the below tools to construct your final answer.
You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

To start you should ALWAYS look at the tables in the database to see what you can query.
Do NOT skip this step.
Then you should query the schema of the most relevant tables.
""")
system_prompt = prompt.format(dialect=db.dialect, top_k=5)

# Set up SQL toolkit
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
sqlTools = toolkit.get_tools()

# Set up search tools
@tool
def internet_search(query: str):
    """
    Search the web for realtime and latest information.
    for examples, news, stock market, weather updates etc.

    Args:
    query: The search query
    """
    search = SearxSearchWrapper(searx_host=os.getenv("SEARX_HOST"))
    return search.run(query)

@tool
def llm_search(query: str):
    """
    Use the LLM model for general and basic information.
    """
    response = llm.invoke(query)
    return response


@tool
def internetarchive_search(query: str):
    """
    Search the Internet Archive for Historical Documents like old Documentations or Manuals.
    Only return the identifier the Item which most likely contains the information you are looking for.
    Remember that we are looking for historical documents, like Manuals or Documentation not Videos or Games.
    """

    search = InternetArchiveSearchWrapper(k=100)
    result = search.run(query)
    return str(result)

#searchTools = [internet_search, llm_search]
searchTools = [internetarchive_search]

# Create the agent
#agent_executor = create_react_agent(llm, searchTools + sqlTools, state_modifier=system_prompt)
agent_executor = create_react_agent(llm, searchTools, state_modifier=system_prompt)

# Example usage function
def ask_agent(question):
    """
    Ask a question to the agent and get the response

    Args:
        question (str): The question to ask

    Returns:
        The agent's response
    """
    query = {"messages": [HumanMessage(question)]}

    result = agent_executor.invoke(query, config=langfuse_config)
    return result

# Define the FastAPI app
app = FastAPI(
    title="Agent API Server",
    description="FastAPI server for the SQL and search agent",
)

# Define the input model
class QueryInput(BaseModel):
    question: str

# Define the messages model for streaming
class MessagesInput(BaseModel):
    messages: List[Dict[str, Any]]

@app.get("/")
async def root():
    """Root endpoint that returns a welcome message"""
    return {"message": "Welcome to the Agent API Server"}

@app.get("/test")
async def test():
    """Test endpoint that runs the example questions from agent.py"""
    try:

        # Example internet search question
        search_question = "Is there an Manual for \"Super Mario Bros 2\" available ?"
        search_result = ask_agent(search_question)
        search_answer = search_result["messages"][-1].content

        return {
            "search_question": search_question,
            "search_answer": search_answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask(query_input: QueryInput):
    """Ask a question to the agent and get the response"""
    try:
        result = ask_agent(query_input.question)
        return {"answer": result["messages"][-1].content}
    except Exception as e: raise (HTTPException(status_code=500, detail=str(e)))

@app.post("/stream")
async def stream(query_input: QueryInput):
    """Stream the agent's response to a question"""
    async def event_stream():
        try:
            # Stream start message
            stream_start_msg = {
                'choices': [
                    {
                        'delta': {},
                        'finish_reason': None
                    }
                ]
            }
            yield f"data: {json.dumps(stream_start_msg)}\n\n"

            # Create the query
            query = {"messages": [HumanMessage(query_input.question)]}

            # Stream the agent's response
            async for event in agent_executor.astream(
                input=query,
                config=langfuse_config,
                stream_mode="values"
            ):
                if "messages" in event:
                    for message in event["messages"]:
                        if hasattr(message, "content") and message.content:
                            # Create a message with the content
                            content_msg = {
                                'choices': [
                                    {
                                        'delta': {
                                            'content': message.content,
                                        },
                                        'finish_reason': None
                                    }
                                ]
                            }
                            yield f"data: {json.dumps(content_msg)}\n\n"

            # Stream end message
            stream_end_msg = {
                'choices': [
                    {
                        'delta': {},
                        'finish_reason': 'stop'
                    }
                ]
            }
            yield f"data: {json.dumps(stream_end_msg)}\n\n"

        except Exception as e:
            print(f"An error occurred: {e}")
            error_msg = {
                'error': str(e)
            }
            yield f"data: {json.dumps(error_msg)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

if __name__ == "__main__":
    import uvicorn
    # Get host and port from environment variables with defaults
    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port = int(os.getenv("FASTAPI_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)



