"""
Wolf CLI Web Search Provider

Integrates DuckDuckGo search via duckduckgo-search library.
"""

import logging
from typing import Dict, Any, List

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

logger = logging.getLogger(__name__)


def search_web(query: str, max_results: int = 10) -> Dict[str, Any]:
    """
    Search the web using DuckDuckGo.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 10, max: 50)
        
    Returns:
        Dictionary with keys:
            - ok: bool - Success status
            - query: str - The query that was searched
            - results: list - List of result dicts with title, url, snippet
            - count: int - Number of results returned
            - error: str (optional) - Error message if ok=False
    """
    
    # Validate inputs
    if not query or not isinstance(query, str):
        return {
            "ok": False,
            "query": query if isinstance(query, str) else "",
            "results": [],
            "count": 0,
            "error": "Query must be a non-empty string"
        }
    
    query = query.strip()
    if not query:
        return {
            "ok": False,
            "query": "",
            "results": [],
            "count": 0,
            "error": "Query cannot be empty"
        }
    
    # Validate and clamp max_results
    try:
        max_results = int(max_results)
    except (ValueError, TypeError):
        max_results = 10
    
    max_results = max(1, min(max_results, 50))  # Clamp to [1, 50]
    
    # Check if DDGS is available
    if DDGS is None:
        return {
            "ok": False,
            "query": query,
            "results": [],
            "count": 0,
            "error": "duckduckgo-search library not installed"
        }
    
    try:
        results = []
        
        # Perform search with timeout
        with DDGS(timeout=15) as ddgs:
            for result in ddgs.text(
                query,
                max_results=max_results,
                safesearch="moderate",
                region="wt-wt"
            ):
                # Normalize result fields
                normalized = {
                    "title": result.get("title", ""),
                    "url": result.get("href") or result.get("url", ""),
                    "snippet": result.get("body") or result.get("snippet", "")
                }
                results.append(normalized)
        
        logger.debug(f"Search for '{query}' returned {len(results)} results")
        
        return {
            "ok": True,
            "query": query,
            "results": results,
            "count": len(results)
        }
    
    except Exception as e:
        logger.debug(f"Web search error for query '{query}': {str(e)}", exc_info=True)
        return {
            "ok": False,
            "query": query,
            "results": [],
            "count": 0,
            "error": f"Search failed: {str(e)}"
        }
