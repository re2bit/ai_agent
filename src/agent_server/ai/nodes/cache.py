import hashlib
import json
import logging
import os
from typing import Any, Optional, Callable

from langchain_core.runnables import RunnableSerializable
from pydantic import PrivateAttr

DATA_ROOT = "/data/ia/cache"


def _hash_query(query: str) -> str:
    return hashlib.sha256(query.encode("utf-8")).hexdigest()


class CacheReaderNode(RunnableSerializable):
    """
    Generic entry node that checks for a cached state using a computed cache key.

    - Computes a hash from a cache key derived via `_cache_key_getter` (defaults to state["query"]).
    - Looks for /data/ia/<hash>/<cache_file_name>.
    - If present, loads it, merges into the state, and sets the `_cached_results_key` flag so the graph can route.
      Otherwise, it sets the flag to False and continues.
    """

    _logger: logging.Logger = PrivateAttr()
    _data_root: str = PrivateAttr()
    _cache_file_name: str = PrivateAttr()
    _cached_results_key: str = PrivateAttr()
    _cache_key_getter: Callable[[dict], Optional[str]] = PrivateAttr()

    def __init__(self, **data):
        logger = data.pop("_logger", None)
        data_root = data.pop("_data_root", None)
        cache_file_name = data.pop("_cache_file_name", "query.json")
        cached_results_key = data.pop("_cached_results_key", "cached_results")
        cache_key_getter = data.pop("_cache_key_getter", None)
        super().__init__(**data)
        self._logger = logger or logging.getLogger(__name__)
        self._data_root = data_root or DATA_ROOT
        self._cache_file_name = cache_file_name
        self._cached_results_key = cached_results_key
        # default cache key getter: read from state["query"]
        self._cache_key_getter = cache_key_getter or (lambda s: s.get("query"))

    def invoke(self, state: dict, config: Any = None) -> dict:
        cache_key: Optional[str] = self._cache_key_getter(state)
        if not cache_key:
            return {**state, self._cached_results_key: False}

        key_hash = _hash_query(cache_key)
        cache_dir = os.path.join(self._data_root, key_hash)
        cache_file = os.path.join(cache_dir, self._cache_file_name)
        merged = {**state, "cache_key_hash": key_hash}

        try:
            if os.path.isfile(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_state = json.load(f)
                # Merge cached state; avoid overwriting the original cache key source if present
                merged.update(cached_state)
                merged[self._cached_results_key] = True
                self._logger.info(f"CacheNode: cache hit for hash {key_hash}")
            else:
                os.makedirs(cache_dir, exist_ok=True)
                merged[self._cached_results_key] = False
                self._logger.info(f"CacheNode: cache miss for hash {key_hash}")
        except Exception as e:
            self._logger.error(f"CacheNode error: {e}")
            merged[self._cached_results_key] = False

        return merged


class CacheWriterNode(RunnableSerializable):
    """
    Persists the current state to /data/ia/<hash>/<cache_file_name> using the cache key hash.

    Should run after Search and before Filter so that future runs can skip Search.
    """

    _logger: logging.Logger = PrivateAttr()
    _data_root: str = PrivateAttr()
    _cache_file_name: str = PrivateAttr()
    _cache_key_getter: Callable[[dict], Optional[str]] = PrivateAttr()

    def __init__(self, **data):
        logger = data.pop("_logger", None)
        data_root = data.pop("_data_root", None)
        cache_file_name = data.pop("_cache_file_name", "query.json")
        cache_key_getter = data.pop("_cache_key_getter", None)
        super().__init__(**data)
        self._logger = logger or logging.getLogger(__name__)
        self._data_root = data_root or DATA_ROOT
        self._cache_file_name = cache_file_name
        self._cache_key_getter = cache_key_getter or (lambda s: s.get("query"))

    def invoke(self, state: dict, config: Any = None) -> dict:
        cache_key: Optional[str] = self._cache_key_getter(state)
        if not cache_key:
            return state

        key_hash: str = state.get("cache_key_hash") or _hash_query(cache_key)
        cache_dir = os.path.join(self._data_root, key_hash)
        cache_file = os.path.join(cache_dir, self._cache_file_name)
        try:
            os.makedirs(cache_dir, exist_ok=True)
            # Only persist a subset that is useful. But spec doesn't restrict, so write full state.
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(dict(state), f, ensure_ascii=False, indent=2)
            self._logger.info(f"StateWriterNode: wrote cache to {cache_file}")
        except Exception as e:
            self._logger.error(f"StateWriterNode error writing cache: {e}")
        return state


class CacheFactory:
    """
    Factory to create paired cache nodes (reader and writer) with consistent configuration.

    Defaults:
    - _cache_file_name: "query.json"
    - _cached_results_key: "cached_results"
    - _cache_key_getter: lambda s: s.get("cache_key") or s.get("query")
    - _data_root: DATA_ROOT ("/data/ia") unless overridden
    """

    @staticmethod
    def create_nodes(
        *,
        _logger: logging.Logger | None = None,
        _directory: str | None = None,
        _cache_file_name: str = "query.json",
        _cached_results_key: str = "cached_results",
        _cache_key_getter: Callable[[dict], Optional[str]] = lambda s: s.get("cache_key") or s.get("query"),
    ) -> tuple[CacheReaderNode, CacheWriterNode]:
        reader = CacheReaderNode(
            _logger=_logger,
            _data_root=_directory,
            _cache_file_name=_cache_file_name,
            _cached_results_key=_cached_results_key,
            _cache_key_getter=_cache_key_getter,
        )
        writer = CacheWriterNode(
            _logger=_logger,
            _data_root=_directory,
            _cache_file_name=_cache_file_name,
            _cache_key_getter=_cache_key_getter,
        )
        return reader, writer
