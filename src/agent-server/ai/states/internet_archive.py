from typing import TypedDict, List, Dict, Optional, Any

class InternetArchiveState(TypedDict):
    """State for the Internet Archive search graph."""
    query: str
    results: Optional[List[str]]
    filtered_results: Optional[List[str]]
    metadata: Optional[Dict[str, Any]]
    error: Optional[str]