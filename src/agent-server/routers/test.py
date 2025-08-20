import json
from typing import List, Dict, Any

from fastapi import HTTPException, APIRouter
from dependency_injector.wiring import inject, Provide
from ..container.container import Container
from ..ai.agents.sql_agent import SQLAgent

class Routes:
    router: APIRouter
    agent: SQLAgent
    llm: Any

    def __call__(self, *args, **kwargs):
        return self.router

    @inject
    def __init__(
            self,
            llm : Any = Provide[Container.ollamaLLM],
            agent : SQLAgent = Provide[Container.sql_agent],
    ):
        self.router = APIRouter()
        self.llm = llm
        self.agent = agent
        self.router.add_api_route("/test", self.test, methods=["GET"])

    async def test(self):
        """Test endpoint that runs the example questions from agent.py"""
        # Example internet search question
        search_question = "Is there an Manual for \"Super Mario Bros 2\" available ?"
        search_result = self.agent.ask(search_question)
        #search_answer = search_result["messages"][-1].content
        search_answer = search_result

        return search_answer
        return {
            "search_question": search_question,
            "search_answer": search_answer
        }
