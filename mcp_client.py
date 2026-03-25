"""
mcp_client.py
Synchronous MCP client for the concept-builder-tools server.
Used by app.py to fetch news + arxiv context per subtopic.
"""

import requests

MCP_BASE = "http://localhost:8000"


def _call_tool(tool_name: str, arguments: dict, timeout: int = 30) -> str:
    """
    Call a FastMCP tool via its HTTP endpoint.
    FastMCP (streamable-http) exposes tools at POST /mcp/tools/call
    with body: {"name": "<tool>", "arguments": {...}}
    """
    try:
        r = requests.post(
            f"{MCP_BASE}/mcp/tools/call",
            json={"name": tool_name, "arguments": arguments},
            timeout=timeout,
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()
        data = r.json()

        # FastMCP returns {"content": [{"type": "text", "text": "..."}], ...}
        content = data.get("content", [])
        if content and isinstance(content, list):
            return content[0].get("text", "")
        return str(data)

    except requests.exceptions.ConnectionError:
        return "[MCP server not running — start mcp_server.py]"
    except Exception as e:
        return f"[MCP error: {e}]"


def fetch_news(query: str, max_results: int = 5) -> str:
    """Fetch latest news articles via the MCP news_search tool."""
    return _call_tool("news_search", {"query": query, "max_results": max_results})


def fetch_arxiv(query: str, max_results: int = 5) -> str:
    """Fetch arXiv papers via the MCP arxiv_search tool."""
    return _call_tool("arxiv_search", {"query": query, "max_results": max_results})


def fetch_mcp_context(subtopic: str) -> str:
    """
    Fetch both news and arxiv results for a subtopic and return
    a single merged context string ready to inject into prompts.
    Returns empty string if both fail (server not running).
    """
    news    = fetch_news(subtopic, max_results=4)
    arxiv   = fetch_arxiv(subtopic, max_results=4)

    parts = []
    if news and not news.startswith("[MCP"):
        parts.append(news)
    if arxiv and not arxiv.startswith("[MCP"):
        parts.append(arxiv)

    return "\n\n".join(parts)