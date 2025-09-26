import json
from typing import List, Dict, Any

from fastapi import HTTPException, APIRouter
from fastapi.responses import StreamingResponse
from dependency_injector.wiring import inject, Provide
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from ..container.container import Container
from ..ai.agents.sql_agent import SQLAgent
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

    def __call__(self, *args, **kwargs):
        return self.router

    @inject
    def __init__(
            self,
            agent: SQLAgent = Provide[Container.sql_agent],
            logging: Logger = Provide[Container.logger]
    ):
        self.agent = agent
        self.logger = logging
        self.router = APIRouter()
        self.router.add_api_route("/ask", self.ask, methods=["POST"])
        self.router.add_api_route("/stream", self.stream, methods=["POST"])

    async def ask(self, query_input: QueryInput):
        try:
            result = self.agent.ask(query_input.question)
            return {"answer": result["messages"][-1].content}
        except Exception as e: raise (HTTPException(status_code=500, detail=str(e)))

    async def stream(self, query_input: QueryInput):
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
                yield f"data: {json.dumps(stream_start_msg)}\n"

                status_message = {
                    "event": {
                        "type": "status",
                        "data": {
                            "description": "Datenbank Zugriff gestartet",
                            "done": False,
                        },
                    }
                }
                yield f"data: {json.dumps(status_message)}\n"

                async for event in self.agent.stream(query_input.question):
                    self.logger.debug_var(obj=event, name="event")
                    if "messages" in event:
                        message = event["messages"][-1]
                        #for message in event["messages"]:
                        if isinstance(message, HumanMessage):
                            continue
                        if not isinstance(message, AIMessage):
                            continue
                        if hasattr(message, "content") and message.content:
                            if (hasattr(message, "tool_calls") and message.tool_calls) or isinstance(message, ToolMessage):
                               content_msg = {
                                    'choices':
                                        [
                                            {
                                                'delta':
                                                    {
                                                        'reasoning_content': message.content,
                                                    },
                                                'finish_reason': None
                                            }
                                        ]
                                }
                            else:
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
                            yield f"data: {json.dumps(content_msg)}\n"

                status_end_message = {
                    "event": {
                        "type": "status",
                        "data": {
                            "description": "Datenbank Zugriff beendet",
                            "done": True
                        },
                    }
                }
                yield f"data: {json.dumps(status_end_message)}\n"

                stream_end_msg = {
                    'choices': [
                        {
                            'delta': {},
                            'finish_reason': 'stop'
                        }
                    ]
                }
                yield f"data: {json.dumps(stream_end_msg)}\n"

            except Exception as e:
                print(f"An error occurred: {e}")
                error_msg = {
                    'error': str(e)
                }
                yield f"data: {json.dumps(error_msg)}\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )