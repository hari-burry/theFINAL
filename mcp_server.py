"""
mcp_server.py
"""

import os
import requests
import feedparser
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
from mcp.server.fastmcp import FastMCP

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

mcp = FastMCP("concept-builder-tools")


# ── Tool 1 ─────────────────────────────
@mcp.tool()
def news_search(query: str, max_results: int = 5) -> str:
    if not NEWS_API_KEY:
        return "NEWS_API_KEY not set."

    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "pageSize": max_results,
                "apiKey": NEWS_API_KEY,
            },
            timeout=10,
        )
        r.raise_for_status()

        articles = r.json().get("articles", [])

        return "\n".join(
            f"- {a['title']} ({a['source']['name']})\n  {a['url']}"
            for a in articles
        ) or "No news found."

    except Exception as e:
        return f"Error: {e}"


# ── Tool 2 ─────────────────────────────
@mcp.tool()
def arxiv_search(query: str, max_results: int = 5) -> str:
    try:
        r = requests.get(
            "http://export.arxiv.org/api/query",
            params={
                "search_query": query,
                "max_results": max_results,
            },
            timeout=10,
        )
        r.raise_for_status()

        feed = feedparser.parse(r.text)

        results = []
        for entry in feed.entries:
            authors_list = []
            for a in entry.authors[:3]:
                if hasattr(a, "name"):
                    authors_list.append(str(a.name))
                elif isinstance(a, dict):
                    authors_list.append(str(a.get("name", "Unknown")))
                else:
                    authors_list.append(str(a))

            authors = ", ".join(authors_list)

            results.append(
                f"- {entry.title}\n  Authors: {authors}\n  {entry.link}"
            )

        return "\n".join(results) or "No papers found."

    except Exception as e:
        return f"Error: {e}"


# ── FASTAPI WRAPPER ─────────────────────
app = FastAPI()

@app.post("/news")
def news_api(data: dict):
    return {"result": news_search(**data)}

@app.post("/arxiv")
def arxiv_api(data: dict):
    return {"result": arxiv_search(**data)}


# ── RUN SERVER ──────────────────────────
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)