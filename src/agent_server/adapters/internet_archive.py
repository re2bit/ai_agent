import json
import logging
from typing import Dict, Optional, Any

import internetarchive
from fastapi import HTTPException
from pydantic import (
    BaseModel,
    Field,
    PrivateAttr,
    model_validator,
)

class InternetArchiveSearchResults(dict):
    def __init__(self, params: dict):
        super().__init__()
        """Take a raw result from Internet Archive and make it into a dict like object."""
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

    def __init__(self, **data):
        logger = data.pop("_logger", None)
        super().__init__(**data)
        self._logger = logger or logging.getLogger(__name__)

    _logger: logging.Logger = PrivateAttr()
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
        """Actual request to IA API."""
        res = InternetArchiveSearchResults(params)

        search = internetarchive.search_items(params["q"])
        self._logger.debug(f"Search results: {search}")
        for item in search:
            res.add_item(item)

        self._result = res
        return res

    @staticmethod
    def _internetarchive_detail_infos(params: dict) -> dict:
        """Actual request to IA API."""
        item = internetarchive.get_item(params["q"])
        files = internetarchive.get_files(params["q"])

        res = dict()
        res['metadata'] = item.metadata
        res['files'] = []
        for file in files:
            res['files'].append(file.metadata)

        return res

    def search(
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

    def item_metadata(
            self,
            query: str,
            **kwargs: Any,
    ) -> dict:
        """
        Run a query through Internet Archive API and parse results.
        """
        _params = {
            "q": query,
        }
        params = {**self.params, **_params, **kwargs}

        if self.query_suffix and len(self.query_suffix) > 0:
            params["q"] += " " + self.query_suffix

        res = self._internetarchive_detail_infos(params)
        self._logger.info(f"Item Metadata Results: {res}")

        return res