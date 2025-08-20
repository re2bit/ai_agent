from langgraph.constants import END
from langgraph.graph import StateGraph
from ..nodes import internet_archive_filter, internet_archive_search,


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