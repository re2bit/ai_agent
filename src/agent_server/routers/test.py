import json
from typing import Any

from fastapi import  APIRouter
from dependency_injector.wiring import inject, Provide
from langgraph.graph.state import CompiledStateGraph

from ..container.container import Container
from ..ai.agents.internet_archive import InternetArchiveAgent
from ..ai.states.internet_archive import InternetArchiveState

class Routes:
    router: APIRouter
    agent: InternetArchiveAgent
    llm: Any

    def __call__(self, *args, **kwargs):
        return self.router

    @inject
    def __init__(
            self,
            llm : Any = Provide[Container.ollamaLLM],
            agent : InternetArchiveAgent = Provide[Container.internet_archive_agent],
            graph : CompiledStateGraph = Provide[Container.internet_archive_graph]
    ):
        self.router = APIRouter()
        self.llm = llm
        self.agent = agent
        self.graph = graph
        self.router.add_api_route("/test", self.test, methods=["GET"])

    async def test(self):
        """Test endpoint that runs the example questions from agent.py"""
        # Example internet search question
        #search_question = "Is there an Manual for \"Super Mario Bros 2\" available ?"
        search_question = "Super Mario Bros 2 Manual"
        #search_result = self.agent.ask(search_question)
        #search_answer = search_result["messages"][-1].content

        internet_archive_state = InternetArchiveState(
            query=search_question,
        )

        search_result = self.graph.invoke(internet_archive_state)
        search_answer = search_result

        return search_answer
        return {
            "search_question": search_question,
            "search_answer": search_answer
        }
