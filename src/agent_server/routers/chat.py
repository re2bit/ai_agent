import json
from typing import List, Dict, Any

from alembic.autogenerate import renderers
from fastapi import HTTPException, APIRouter
from fastapi.responses import StreamingResponse
from dependency_injector.wiring import inject, Provide
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from ..container.container import Container
from ..ai.agents.sql_agent import SQLAgent
from ..renderer.open_webui import OpenWebUiRenderer
from logging import Logger

from pydantic import (
    BaseModel,
)
# Define the input model
class QueryInput(BaseModel):
    question: str

# Define the message model for streaming
class MessagesInput(BaseModel):
    messages: List[Dict[str, Any]]

class Routes:
    router: APIRouter
    agent: SQLAgent
    logger: Logger
    renderer: OpenWebUiRenderer

    def __call__(self, *args, **kwargs):
        return self.router

    @inject
    def __init__(
            self,
            agent: SQLAgent = Provide[Container.sql_agent],
            logging: Logger = Provide[Container.logger],
            renderer: OpenWebUiRenderer = Provide[Container.renderer],
    ):
        self.agent = agent
        self.logger = logging
        self.renderer = renderer
        self.router = APIRouter()
        self.router.add_api_route("/ask", self.ask, methods=["POST"])
        self.router.add_api_route("/stream", self.stream, methods=["POST"])

    async def ask(self, query_input: QueryInput):
        try:
            result = self.agent.ask(query_input.question)
            return {"answer": result["messages"][-1].content}
        except Exception as e: raise (HTTPException(status_code=500, detail=str(e)))

    async def stream(self, query_input: QueryInput):
        return StreamingResponse(
            self.renderer.render(event_stream=self.agent.stream(query_input.question)),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )