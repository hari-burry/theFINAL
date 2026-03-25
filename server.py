from fastapi import FastAPI, HTTPException
import requests
import os
import feedparser
import dotenv

dotenv.load_dotenv()  # Load environment variables from .env file

app = FastAPI()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

@app.post("/mcp/arxiv")
def search_arxiv(data: dict):
    query = data.get("query", "")
    max_results = min(data.get("max_results", 5), 20)

    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    # arXiv API endpoint
    url = "http://export.arxiv.org/api/query"

    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        # Parse Atom XML feed
        feed = feedparser.parse(response.text)

        results = []

        for entry in feed.entries:
            results.append({
                "title": entry.title,
                "authors": [author.name for author in entry.authors],
                "summary": entry.summary,
                "published": entry.published,
                "link": entry.link
            })

        return {"results": results}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/mcp/news")
def get_news(data: dict):
    query = data.get("query", "")

    if not NEWS_API_KEY:
        raise HTTPException(status_code=500, detail="Missing NEWS_API_KEY")

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "relevancy",
        "apiKey": NEWS_API_KEY
    }

    r = requests.get(url, params=params)
    articles = r.json().get("articles", [])[:5]

    results = [
        {
            "title": a["title"],
            "source": a["source"]["name"],
            "url": a["url"]
        }
        for a in articles
    ]

    return {"results": results}


# -------------------------
# Google Custom Search endpoint
# -------------------------
# @app.post("/mcp/search")
# def google_search(data: dict):
#     query = data.get("query", "")
#     num_results = min(data.get("num_results", 5), 10)

#     url = "https://www.googleapis.com/customsearch/v1"

#     params = {
#         "q": query,
#         "key": GOOGLE_API_KEY,
#         "cx": GOOGLE_CX,
#         "num": num_results,
#     }

#     r = requests.get(url, params=params)

#     # 🔥 Debug info
#     print("Status code:", r.status_code)
#     print("Raw response:", r.text)

#     if r.status_code != 200:
#         raise HTTPException(
#             status_code=r.status_code,
#             detail=f"Google API error: {r.text}"
#         )

#     try:
#         data = r.json()
#     except ValueError:
#         raise HTTPException(
#             status_code=500,
#             detail="Google returned invalid JSON response"
#         )

#     results = [
#         {
#             "title": item.get("title"),
#             "link": item.get("link"),
#             "snippet": item.get("snippet"),
#         }
#         for item in data.get("items", [])
#     ]

#     return {"results": results}