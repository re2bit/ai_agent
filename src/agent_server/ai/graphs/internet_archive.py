import logging
from langgraph.graph import StateGraph
from langgraph.types import CachePolicy, RetryPolicy
from langgraph.cache.memory import InMemoryCache

from ..states.internet_archive import InternetArchiveState
from ..nodes.internet_archive import SearchNode, MetadataNode, FilterNode
from ..nodes.cache import CacheFactory


class InternetArchiveGraphBuilder():
    search_node: SearchNode
    filter_node: FilterNode
    metadata_node: MetadataNode
    logger: logging.Logger | None
    data_root: str | None

    def __init__(
            self,
            search_node: SearchNode,
            filter_node: FilterNode,
            metadata_node: MetadataNode,
            logger: logging.Logger | None = None,
            data_root: str | None = None,
    ):
        self.metadata_node = metadata_node
        self.filter_node = filter_node
        self.search_node = search_node
        self.logger = logger
        self.data_root = data_root

    def build(self):
        """
            Create a graph for Internet Archive search with search, filter, and metadata nodes.
        Returns:
            A StateGraph for Internet Archive search
        """
        graph = StateGraph(InternetArchiveState)
        cache_reader, cache_writer = CacheFactory.create_nodes(
            _logger=self.logger,
            _data_root=self.data_root,
            _cache_file_name="query.json",
            _cached_results_key="cached_results",
            _cache_key_getter=lambda s: s.get("cache_key") or s.get("query"),
        )
        graph.add_node("cache", cache_reader, retry_policy=RetryPolicy(max_attempts=1))
        graph.add_node("search", self.search_node, cache_policy=CachePolicy(ttl=120), retry_policy=RetryPolicy(max_attempts=1))
        graph.add_node("state_writer", cache_writer, retry_policy=RetryPolicy(max_attempts=1))
        graph.add_node("filter", self.filter_node, cache_policy=CachePolicy(ttl=120), retry_policy=RetryPolicy(max_attempts=1))
        graph.add_node("metadata", self.metadata_node, retry_policy=RetryPolicy(max_attempts=1))

        graph.set_entry_point("cache")

        def route_next(state: InternetArchiveState):
            return "metadata" if state.get("cached_results") \
                else "search"

        graph.add_conditional_edges(
            "cache",
            route_next,
            {
                "metadata": "metadata",
                "search": "search"
            }
        )

        graph.add_edge("search", "filter")
        graph.add_edge("filter", "state_writer")
        graph.add_edge("state_writer", "metadata")
        graph.set_finish_point("metadata")

        return graph.compile(cache=InMemoryCache())
