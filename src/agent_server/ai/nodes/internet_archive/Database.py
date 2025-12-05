import logging
from typing import Any

from langchain_core.runnables import Runnable
from pydantic import PrivateAttr

from agent_server.models.manual import IASearch
from ...states.internet_archive import InternetArchiveState
from sqlalchemy import Engine
from sqlmodel import select, Session


class DatabaseNode(Runnable):

    engine: Engine = PrivateAttr()
    _logger: logging.Logger = PrivateAttr()

    def __init__(self, logger:logging.Logger, engine: Engine):
        self._logger = logger or logging.getLogger(__name__)
        self.engine = engine

    def invoke(self, state: InternetArchiveState, config: Any = None, **kwargs) -> InternetArchiveState:
        with Session(self.engine) as session:
            statement = select(IASearch).where(IASearch.query == state.get("query"))
            ia_search = session.exec(statement).first()

            if ia_search is None:
                ia_search = IASearch(query=state.get("query"))




            return None
