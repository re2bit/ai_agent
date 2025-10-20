from typing import TypedDict, List, Dict, Optional, Any

class InternetArchiveState(TypedDict):
    """State for the Internet Archive search graph."""
    query: str
    results: Optional[List[str]]
    cached_results: Optional[bool]
    filtered_results: Optional[List[str]]
    cached_filtered_results: Optional[bool]
    metadata: Optional[Dict[str, Any]]
    cached_metadata: Optional[bool]
    pdfs_to_download: Optional[List[str]]
    error: Optional[str]