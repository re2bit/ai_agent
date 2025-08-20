import json
from ..states.internet_archive import InternetArchiveState
from ...adapters.internet_archive import InternetArchiveSearchWrapper

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

        result_dict = json.loads(str(result))

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