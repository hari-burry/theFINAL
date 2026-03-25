import os
import requests
import streamlit as st
from tool_wrapper import news_tool, arxiv_tool
from mcp_client import fetch_news, fetch_arxiv
from langchain_groq import ChatGroq
from langchain_core.tools import Tool

# Import rewriter agent for query optimization
try:
    from rewriter_agent import rewrite_for_search
    REWRITER_AVAILABLE = True
except ImportError:
    REWRITER_AVAILABLE = False

if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = "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"

# --- UI ---
st.title("📰 Research Chat Agent (News Grounded)")

# --- API key (safe loading) ---.u
# if not os.getenv("GROQ_API_KEY", "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"):
#     st.warning("Please set GROQ_API_KEY environment variable")

# --- HELPER FUNCTIONS FOR SEARCH OPTIMIZATION ---

@st.cache_data
def optimize_search_query(user_question: str) -> dict:
    """
    Optimize user question to generate better search queries for news and arxiv.
    Results are cached to avoid redundant API calls.
    """
    if not REWRITER_AVAILABLE:
        return {
            'news_queries': [user_question],
            'arxiv_queries': [user_question],
            'search_rationale': 'Using original question (rewriter not available)'
        }
    
    try:
        result = rewrite_for_search(user_question)
        return result
    except Exception as e:
        st.warning(f"Query optimization failed: {e}. Using original question.")
        return {
            'news_queries': [user_question],
            'arxiv_queries': [user_question],
            'search_rationale': f'Fallback mode: {str(e)}'
        }


def fetch_best_results(user_question: str, max_results: int = 3) -> dict:
    """
    Fetch best results from news and arxiv using optimized queries.
    """
    optimized_queries = optimize_search_query(user_question)
    
    # Fetch from news
    news_results = []
    for query in optimized_queries.get('news_queries', [])[:2]:  # Limit to top 2
        try:
            result = fetch_news(query)
            news_results.append({'query': query, 'content': result})
        except Exception as e:
            pass
    
    # Fetch from arxiv
    arxiv_results = []
    for query in optimized_queries.get('arxiv_queries', [])[:2]:  # Limit to top 2
        try:
            result = fetch_arxiv(query, max_results=max_results)
            arxiv_results.append({'query': query, 'content': result})
        except Exception as e:
            pass
    
    return {
        'news_results': news_results,
        'arxiv_results': arxiv_results,
        'optimized_queries': optimized_queries
    }

# --- LLM ---
llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0
)

# --- Agent ---
agent = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0,
    max_tokens=None,
    reasoning_format="parsed",
    timeout=None,
    max_retries=2,
).bind_tools([news_tool, arxiv_tool])

# --- Chat memory ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Show chat ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Input ---
user_input = st.chat_input("Ask something grounded in news...")

if user_input:

    st.session_state.messages.append(
        {"role": "human", "content": user_input}
    )

    with st.chat_message("human"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Fetching grounded info..."):
            message = [
                (
                    "system",
                        '''You are a helpful research assistant that provides information grounded in the latest news. Use the "news_search" and "arxiv_search" tools to fetch relevant news articles and academic papers when needed. Always base your responses on real-world information from news and academic sources, and avoid speculation.''',
                ),
                ("human", user_input),
            ]

            response = agent.invoke(message)

            # print("Agent response:", response)

            # If model wants to call a tool
            if response.tool_calls:

                tool_call = response.tool_calls[0]
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Run the tool manually
                if tool_name == "news_search":
                    tool_result = fetch_news(tool_args["__arg1"])
                elif tool_name == "arxiv_search":
                    tool_result = fetch_arxiv(tool_args["__arg1"], max_results=tool_args.get("max_results", 5))

                # Send result back to model
                final_response = agent.invoke([
                    *message,
                    response,
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result,
                    },
                ])

                output = final_response.content

            else:
                output = response.content

            print("Final output:", output)
            st.markdown(output)

    st.session_state.messages.append(
    {"role": "assistant", "content": output}
    )