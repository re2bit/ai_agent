import json
from typing import List, Dict, Any

from fastapi import HTTPException, APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from dependency_injector.wiring import inject, Provide
from langfuse import Langfuse
from ..container.container import container
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
    langfuse_config: dict

    def __call__(self, *args, **kwargs):
        return self.router

    @inject
    def __init__(self, langfuse: dict = Provide[container.langfuse_config]):
        self.langfuse_config = langfuse
        router = APIRouter()
        self.router = router
        self.route.add_api_route("/ask", self.ask, methods=["POST"])
        self.route.add_api_route("/stream", self.stream, methods=["POST"])
        self.router.add_api_route("/test", self.test, methods=["GET"])

    async def test(self):
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

    async def ask(self, query_input: QueryInput):
        """Ask a question to the agent and get the response"""
        try:
            result = ask_agent(query_input.question)
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
                yield f"data: {json.dumps(stream_start_msg)}\n\n"

                # Create the query
                query = {"messages": [HumanMessage(query_input.question)]}

                # Stream the agent's response
                async for event in agent_executor.astream(
                    input=query,
                    config=self.langfuse_config,
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

router = ChatRoutes()()