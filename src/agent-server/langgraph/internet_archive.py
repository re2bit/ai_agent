import json
from typing import TypedDict, List, Dict, Optional, Any
from langchain_core.prompts import PromptTemplate
from langgraph.constants import END
from langgraph.graph import StateGraph

from ..adapters.internet_archive import InternetArchiveSearchWrapper


class InternetArchiveState(TypedDict):
    """State for the Internet Archive search graph."""
    query: str
    results: Optional[List[str]]
    filtered_results: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]
    error: Optional[str]

def search_node(state: InternetArchiveState) -> InternetArchiveState:
    """
    Search node for the Internet Archive search graph.
    Uses the InternetArchiveSearchWrapper to search for items.

    Args:
        state: The current state with the query

    Returns:
        Updated state with search results
    """
    try:
        search = InternetArchiveSearchWrapper(k=100, params={})
        result = search.search(state["query"])

        # Parse the JSON string result
        result_dict = json.loads(str(result))

        # Update the state
        return {
            **state,
            "results": result_dict.get("items", []),
            "error": result_dict.get("error")
        }

    except Exception as e:
        return {
            **state,
            "error": f"Search error: {str(e)}"
        }


def filter_node(state: InternetArchiveState) -> InternetArchiveState:
    """
    Filter node for the Internet Archive search graph.
    Uses the LLM to filter results based on relevance to the query.

    Args:
        state: The current state with search results

    Returns:
        Updated state with filtered results
    """
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


def metadata_node(state: InternetArchiveState) -> InternetArchiveState:
    """
    Metadata node for the Internet Archive search graph.
    Retrieves detailed metadata for filtered results.

    Args:
        state: The current state with filtered results

    Returns:
        Updated state with metadata for filtered results
    """
    if not state.get("filtered_results") or len(state.get("filtered_results", [])) == 0:
        return {
            **state,
            "metadata": {},
            "error": state.get("error") or "No filtered results to get metadata for"
        }

    try:
        # Initialize the search wrapper
        search = InternetArchiveSearchWrapper(k=100, params={})

        # Get metadata for each filtered result
        metadata = {}
        for item_id in state["filtered_results"]:
            try:
                item_metadata = search.item_metadata(item_id)
                metadata[item_id] = item_metadata
            except Exception as e:
                # If metadata retrieval fails for an item, add error message
                metadata[item_id] = {"error": f"Failed to get metadata: {str(e)}"}

        # Update the state with metadata
        return {
            **state,
            "metadata": metadata
        }
    except Exception as e:
        return {
            **state,
            "metadata": {},
            "error": f"Metadata error: {str(e)}"
        }

def create_internetarchive_graph():
    """
    Create a graph for Internet Archive search with search, filter, and metadata nodes.

    Returns:
        A StateGraph for Internet Archive search
    """
    # Create the graph
    graph = StateGraph(InternetArchiveState)

    # Add nodes
    graph.add_node("search", search_node)
    graph.add_node("filter", filter_node)
    graph.add_node("metadata", metadata_node)

    # Set the entry point
    graph.set_entry_point("search")

    # Add edges
    graph.add_edge("search", "filter")
    graph.add_edge("filter", "metadata")
    graph.add_edge("metadata", END)

    # Compile the graph
    return graph.compile()