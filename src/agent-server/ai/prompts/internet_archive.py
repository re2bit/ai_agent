from typing import Final
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

_TEMPLATE_FILTER: Final[str] = """You are a helpful assistant that filters Internet Archive search results.
The user is looking for: {query}

Here are the search results (item identifiers):
{results}

Please filter these results to only include relevant items. But dont be too aggressive.
We will load Metadata later and verify the results.
Return your answer as a JSON list of item identifiers. return only json, no other text.
Example format: ["item1", "item2", "item3"]
"""

_PROMPT_FILTER: Final[PromptTemplate] = PromptTemplate.from_template(_TEMPLATE_FILTER)

class FilterPromptFactory(BaseModel):
    @classmethod
    def create(cls, results: str, query: str) -> str:
        return _PROMPT_FILTER.format(results=results, query=query)


_TEMPLATE_AGENT: Final[str] = """You are a helpful Agent
 """

_PROMPT_AGENT: Final[PromptTemplate] = PromptTemplate.from_template(_TEMPLATE_AGENT)

class AgentPromptFactory(BaseModel):
    @classmethod
    def create(cls) -> str:
        return _PROMPT_AGENT.format()