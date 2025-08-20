import json
from typing import Any

from langchain_core.prompts import PromptTemplate
from ..states.internet_archive import InternetArchiveState
from langchain_core.runnables import RunnableSerializable


class InternetArchiveFilterNode(RunnableSerializable):
    """
    Filter node for the Internet Archive search graph.
    Uses the LLM to filter results based on relevance to the query.

    Args:
        state: The current state with search results

    Returns:
        Updated state with filtered results
    """

    @inject
    def __init__(self, llm):
        super().__init__()
        self.llm = llm

    def invoke(self, input: dict, config: Any = None) -> dict:
        state = input
        if not state.get("results") or len(state.get("results", [])) == 0:
            return {
                **state,
                "filtered_results": [],
                "error": state.get("error") or "No results to filter"
            }

        try:
            # Create a prompt for the LLM to filter the results
            filter_prompt = PromptTemplate.from_template(
                """You are a helpful assistant that filters Internet Archive search results.

                The user is looking for: {query}

                Here are the search results (item identifiers):
                {results}

                Please filter these results to only include relevant items. But dont be too aggressive.
                We will load Metadata later and verify the results.
                Return your answer as a JSON list of item identifiers. return only json, no other text.
                Example format: ["item1", "item2", "item3"]
                """
            )

            # Format the prompt with the query and results
            formatted_prompt = filter_prompt.format(
                query=state["query"],
                results=json.dumps(state["results"])
            )

            # Get the filtered results from the LLM
            llm_response = llm.invoke(formatted_prompt)

            # Try to parse the response as JSON
            try:
                filtered_results = json.loads(llm_response.content)
                if not isinstance(filtered_results, list):
                    filtered_results = []

                return {
                    **state,
                    "filtered_results": filtered_results
                }
            except json.JSONDecodeError:
                # If JSON parsing fails, return the original results
                return {
                    **state,
                    "filtered_results": state["results"],
                    "error": "Failed to parse LLM response as JSON"
                }
        except Exception as e:
            return {
                **state,
                "filtered_results": state["results"],  # Fall back to unfiltered results
                "error": f"Filter error: {str(e)}"
            }



        # synchroner Node-Aufruf
        state = input
        results = state.get("results", [])
        if not results:
            return {**state, "filtered_results": [], "error": "No results to filter"}

        # Prompt bauen & LLM aufrufen
        from langchain_core.prompts import PromptTemplate
        import json

        tmpl = PromptTemplate.from_template("Filter for {query}: {results}")
        formatted_prompt = tmpl.format(
            query=state["query"],
            results=json.dumps(results)
        )
        resp = self.llm.invoke(formatted_prompt)

        try:
            filtered = json.loads(resp.content)
        except Exception:
            filtered = results

        return {**state, "filtered_results": filtered}