import os
import json
from langchain_groq import ChatGroq
from llm_scheduler import LLMScheduler

API_KEYS = [
    "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",
    "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",
    "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",
    "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"
]

scheduler = LLMScheduler(API_KEYS)

# ==========================================
# PROMPT FOR REWRITING QUESTIONS FOR PLANNING
# ==========================================
PLANNER_QUESTION_REWRITER_PROMPT = '''You are a question rewriting specialist for research planning.

Your task is to rewrite user questions to make them MORE SUITABLE for research planning.

Rewriting rules:
- Clarify the core research topic/area
- Make it more specific and bounded
- Emphasize what the user wants to UNDERSTAND (theory, concepts, relationships)
- Avoid implementation details, tooling, applications
- Make it suitable as a research study plan topic

Output format (JSON ONLY):
{
  "original_question": "<original question>",
  "rewritten_question": "<rewritten for planning>",
  "research_focus": "<what will be studied>"
}'''

# ==========================================
# PROMPT FOR OPTIMIZING SEARCH QUERIES
# ==========================================
NEWS_ARXIV_QUERY_REWRITER_PROMPT = '''You are an expert at formulating search queries for news and academic research.

Your task is to take a user question and generate optimized search queries for:
1. News databases (current events, recent developments)
2. ArXiv (academic papers, research)

Optimization rules for news queries:
- Use recent keywords and current terminology
- Focus on practical applications, news angles, industry developments
- Include 3-5 specific search terms
- Emphasize what's happening NOW

Optimization rules for arxiv queries:
- Use formal academic terminology
- Focus on theoretical foundations, methodologies, architectures
- Include specific technical keywords
- Target research papers over tutorials

Output format (JSON ONLY):
{
  "original_question": "<original question>",
  "news_queries": ["<query1>", "<query2>", "<query3>"],
  "arxiv_queries": ["<query1>", "<query2>", "<query3>"],
  "search_rationale": "<why these queries will find relevant content>"
}'''

def rewrite_for_planning(question: str) -> dict:
    """
    Rewrite a user question to be optimized for the planning agent.
    
    Args:
        question: The original user question
        
    Returns:
        Dictionary with original_question, rewritten_question, and research_focus
    """
    messages = [
        ("system", PLANNER_QUESTION_REWRITER_PROMPT),
        ("human", f"Rewrite this question for research planning: {question}"),
    ]
    
    response = scheduler.invoke(messages)
    return json.loads(response.content)


def rewrite_for_search(question: str) -> dict:
    """
    Rewrite a user question to optimize search queries for news and arxiv.
    
    Args:
        question: The original user question
        
    Returns:
        Dictionary with news_queries, arxiv_queries, and search_rationale
    """
    messages = [
        ("system", NEWS_ARXIV_QUERY_REWRITER_PROMPT),
        ("human", f"Generate optimized search queries for: {question}"),
    ]
    
    response = scheduler.invoke(messages)
    return json.loads(response.content)


def rewrite_full_pipeline(question: str) -> dict:
    """
    Complete rewriting pipeline: optimize for both planning and search.
    
    Args:
        question: The original user question
        
    Returns:
        Dictionary with planning_rewrite and search_rewrite
    """
    planning_rewrite = rewrite_for_planning(question)
    search_rewrite = rewrite_for_search(question)
    
    return {
        "original_question": question,
        "planning_rewrite": planning_rewrite,
        "search_rewrite": search_rewrite,
        "recommended_plan_topic": planning_rewrite.get("rewritten_question"),
        "recommended_search_queries": {
            "news": search_rewrite.get("news_queries", []),
            "arxiv": search_rewrite.get("arxiv_queries", [])
        }
    }


if __name__ == "__main__":
    # Example usage
    test_question = "How do I get started with machine learning?"
    
    print("=" * 60)
    print("REWRITER AGENT TEST")
    print("=" * 60)
    print(f"\nOriginal Question: {test_question}\n")
    
    result = rewrite_full_pipeline(test_question)
    print(json.dumps(result, indent=2))
