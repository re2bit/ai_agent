"""Toolkit for interacting with an Internet Archive."""

from typing import List

from langchain_core.tools import BaseTool
from langchain_core.tools.base import BaseToolkit

class InternetArchiveToolkit(BaseToolkit):
    tools: List[BaseTool]

    def get_tools(self) -> List[BaseTool]:
        return self.tools