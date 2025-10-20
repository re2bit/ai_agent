import json
from typing import Final, Optional

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

from agent_server.ai.prompts.interface import IPromptTemplateFactoryInterface

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

class FilterPromptFactory(BaseModel, IPromptTemplateFactoryInterface):
    @classmethod
    def create(cls, results: str, query: str) -> str:
        return _PROMPT_FILTER.format(results=results, query=query)

_TEMPLATE_FINDER: Final[str] = """
You are a precise assistant that evaluates Internet Archive entries for relevance.

Task:
- Determine whether the following entry matches the user's query.

User query:
{query}

Entry to evaluate (Identifier/Name):
{name}

Entry metadata (JSON):
{metadata}

Criteria (examples, not exhaustive):
- Title/identifier contains search terms or clear synonyms.
- Language and description are appropriate.
- Media type/format is plausible for the query (e.g., manual/instruction).
- Year/time context appears relevant.
- Relevant keywords/topics align.

Important notes:
- Focus on semantic similarity, not just substring matches.
- If uncertain, it is not relevant.

"""

class FinderPromptFactory(BaseModel, IPromptTemplateFactoryInterface):
    @classmethod
    def create(
            cls,
            query: str,
            name: str,
            metadata:dict,
            parser:Optional[JsonOutputParser],
    ) -> str:
        template: str = _TEMPLATE_FINDER

        params=dict(
            query=query,
            name=name,
            metadata=json.dumps(metadata),
        )

        if parser is not None:
            template = template + "\n{format_instructions}"
            params["format_instructions"] = parser.get_format_instructions()

        prompt_template = PromptTemplate.from_template(template)

        return prompt_template.format(**params)


_TEMPLATE_AGENT: Final[str] = """You are a helpful Agent
 """

_PROMPT_AGENT: Final[PromptTemplate] = PromptTemplate.from_template(_TEMPLATE_AGENT)

class AgentPromptFactory(BaseModel, IPromptTemplateFactoryInterface):
    @classmethod
    def create(cls) -> str:
        return _PROMPT_AGENT.format()