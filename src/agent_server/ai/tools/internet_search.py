import os

from langchain_community.utilities.searx_search import SearxSearchWrapper
from langchain_core.tools import tool


# Set up search tools
@tool
def internet_search(query: str):
    """
    Search the web for realtime and the latest information.
    for example, news, stock market, weather updates, etc.

    Args:
    query: The search query
    """
    search = SearxSearchWrapper(searx_host=os.getenv("SEARX_HOST"))
    return search.run(query)