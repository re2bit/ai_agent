import logging
from langgraph.graph import StateGraph
from langgraph.types import CachePolicy, RetryPolicy
from langgraph.cache.memory import InMemoryCache

from ..states.internet_archive import InternetArchiveState
from ..nodes.internet_archive.Search import SearchNode
from ..nodes.internet_archive.Finder import FinderNode
from ..nodes.internet_archive.Metadata import MetadataNode
from ..nodes.internet_archive.Filter import FilterNode
from ..nodes.internet_archive.FileFinder import FileFinderNode
from ..nodes.internet_archive.Downloader import DownloaderNode
from ..nodes.internet_archive.Database import DatabaseNode
from ..nodes.cache import CacheFactory


class InternetArchiveGraphBuilder():
    search_node: SearchNode
    filter_node: FilterNode
    metadata_node: MetadataNode
    file_finder_node: FileFinderNode
    finder_node: FinderNode
    downloader_node: DownloaderNode

    logger: logging.Logger | None
    cache_dir: str | None

    def __init__(
            self,
            search_node: SearchNode,
            filter_node: FilterNode,
            metadata_node: MetadataNode,
            finder_node: FinderNode,
            file_finder_node: FileFinderNode,
            downloader_node: DownloaderNode,
            database_node: DatabaseNode,
            logger: logging.Logger | None = None,
            cache_dir: str | None = None,
    ):
        self.database_node = database_node
        self.search_node = search_node
        self.filter_node = filter_node
        self.metadata_node = metadata_node
        self.finder_node = finder_node
        self.file_finder_node = file_finder_node
        self.downloader_node = downloader_node
        self.logger = logger
        self.cache_dir = cache_dir

    def build(self):
        """
            Create a graph for Internet Archive search with search, filter, and metadata nodes.
        Returns:
            A StateGraph for Internet Archive search
        """
        graph = StateGraph(InternetArchiveState)

        cache_reader, cache_writer = CacheFactory.create_nodes(
            _logger=self.logger,
            _directory=self.cache_dir,
            _cache_file_name="query.json",
            _cached_results_key="cached_results",
            _cache_key_getter=lambda s: s.get("cache_key") or s.get("query"),
        )

        graph.add_node("cache", cache_reader, retry_policy=RetryPolicy(max_attempts=1))
        graph.add_node("search", self.search_node, cache_policy=CachePolicy(ttl=120), retry_policy=RetryPolicy(max_attempts=1))
        graph.add_node("state_writer", cache_writer, retry_policy=RetryPolicy(max_attempts=1))
        graph.add_node("filter", self.filter_node, cache_policy=CachePolicy(ttl=120), retry_policy=RetryPolicy(max_attempts=1))
        graph.add_node("metadata", self.metadata_node, retry_policy=RetryPolicy(max_attempts=1))
        graph.add_node("finder", self.finder_node, retry_policy=RetryPolicy(max_attempts=1))
        graph.add_node("file_finder", self.file_finder_node, retry_policy=RetryPolicy(max_attempts=1))
        graph.add_node("downloader", self.downloader_node, retry_policy=RetryPolicy(max_attempts=1))

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
        graph.add_edge("metadata", "finder")
        graph.add_edge("finder", "file_finder")
        graph.add_edge("file_finder", "downloader")
        graph.add_edge("file_finder", "downloader")

        graph.set_entry_point("cache")
        graph.set_finish_point("downloader")

        return graph.compile(cache=InMemoryCache())
