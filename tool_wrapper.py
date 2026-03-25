from langchain_core.tools import Tool
from mcp_client import fetch_news, fetch_arxiv

news_tool = Tool(
    name="news_search",
    func=fetch_news,
    description="Fetch latest real-world news related to a topic"
)

arxiv_tool = Tool(
    name="arxiv_search",
    func=fetch_arxiv,
    description="Fetch relevant arXiv papers related to a topic"
)