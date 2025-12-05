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
    def create(
            cls,
            results: str,
            query: str,
            parser: Optional[JsonOutputParser] = None
    ) -> str:
        template = _TEMPLATE_FILTER

        params = dict(
            results=results,
            query=query
        )

        if parser is not None:
            template = template + "\n{format_instructions}"
            params["format_instructions"] = parser.get_format_instructions()

        prompt_template = PromptTemplate.from_template(template)

        return prompt_template.format(**params)

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

class FinderPromptFactory(IPromptTemplateFactoryInterface, BaseModel):
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


# New prompt to select relevant PDF files from an item's file list
_TEMPLATE_FILE_FINDER: Final[str] = """
You are a careful assistant that selects the most relevant PDF files for the user's query from a single Internet Archive item.

User query:
{query}

Item identifier/name:
{name}

All available files for this item (JSON array):
{files}

Instructions:
- Return only files that are actual PDFs. Accept typical PDF formats such as "PDF", "Text PDF", "Image Container PDF", "Searchable PDF".
- Prefer high-quality or searchable PDFs if available. If there is both an OCR/searchable PDF and a raw image PDF, include the searchable one first.
- Prefer files with source "original" over "derivative" when both are equivalent.
- Exclude non-PDF files (ePub, DjVu, HTML, JP2, TXT, XML, etc.).
- If multiple PDFs are relevant, you may include more than one, but keep it minimal.
- If none are relevant or no PDFs exist, return an empty list.

Output format:
- Return only JSON with a single field "pdfs_to_download" which is a list of file names (strings).
- Example: {{"pdfs_to_download": ["Example Item.pdf"]}}
"""

class FileFinderPromptFactory(IPromptTemplateFactoryInterface, BaseModel):
    @classmethod
    def create(
        cls,
        query: str,
        name: str,
        files: list[dict],
        parser: Optional[JsonOutputParser] = None,
    ) -> str:
        template: str = _TEMPLATE_FILE_FINDER
        params = dict(
            query=query,
            name=name,
            files=json.dumps(files),
        )
        if parser is not None:
            template = template + "\n{format_instructions}"
            params["format_instructions"] = parser.get_format_instructions()
        prompt_template = PromptTemplate.from_template(template)
        return prompt_template.format(**params)