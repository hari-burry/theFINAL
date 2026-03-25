"""
Integration example showing how to use the rewriter agent
in the research pipeline.

Flow:
  User Question
       ↓
  [REWRITER AGENT] ← rewrites for planning & search
       ↓
  Planning Agent (uses rewritten question)
       ↓
  Search Agent (uses optimized search queries)
       ↓
  Concept Engine (builds understanding)
       ↓
  Final Response
"""

import os
import json
from rewriter_agent import rewrite_full_pipeline, rewrite_for_planning, rewrite_for_search
from planning_agent import generate_plan
from mcp_client import fetch_news, fetch_arxiv

# ==========================================
# INTEGRATION EXAMPLES
# ==========================================

def research_pipeline_with_rewriter(user_question: str):
    """
    Complete research pipeline with question rewriting.
    
    Args:
        user_question: The original user question
        
    Returns:
        Dictionary with full pipeline results
    """
    
    print("\n" + "="*70)
    print("RESEARCH PIPELINE WITH REWRITER AGENT")
    print("="*70)
    
    # Step 1: Rewrite for optimization
    print("\n[STEP 1] Rewriting question for planning and search...")
    rewrite_result = rewrite_full_pipeline(user_question)
    
    print(f"\nOriginal Question: {user_question}")
    print(f"\nRewritten for Planning: {rewrite_result['recommended_plan_topic']}")
    print(f"Search Rationale: {rewrite_result['search_rewrite'].get('search_rationale', 'N/A')}")
    
    # Step 2: Generate plan using rewritten question
    print("\n[STEP 2] Generating research plan...")
    plan_topic = rewrite_result['recommended_plan_topic']
    research_plan = generate_plan(plan_topic)
    
    print(f"\nResearch Plan for: {plan_topic}")
    for key, value in research_plan.items():
        print(f"  {key}. {value}")
    
    # Step 3: Fetch relevant content using optimized search queries
    print("\n[STEP 3] Fetching relevant content...")
    news_results = []
    arxiv_results = []
    
    # Use news queries
    print("\nSearching News...")
    for query in rewrite_result['recommended_search_queries']['news'][:2]:
        print(f"  Query: {query}")
        try:
            result = fetch_news(query)
            news_results.append({"query": query, "results": result})
        except Exception as e:
            print(f"  Error: {e}")
    
    # Use arxiv queries
    print("\nSearching ArXiv...")
    for query in rewrite_result['recommended_search_queries']['arxiv'][:2]:
        print(f"  Query: {query}")
        try:
            result = fetch_arxiv(query, max_results=3)
            arxiv_results.append({"query": query, "results": result})
        except Exception as e:
            print(f"  Error: {e}")
    
    # Step 4: Compile results
    pipeline_result = {
        "original_question": user_question,
        "rewriter_output": rewrite_result,
        "research_plan": research_plan,
        "news_results": news_results,
        "arxiv_results": arxiv_results,
        "next_step": "Pass research_plan to concept_engine for iterative deepening"
    }
    
    return pipeline_result


def search_only_with_rewriter(user_question: str):
    """
    If you only want to optimize search queries without full planning.
    Useful for quick research queries.
    
    Args:
        user_question: The original user question
        
    Returns:
        Dictionary with optimized search results
    """
    
    print("\n" + "="*70)
    print("SEARCH OPTIMIZATION WITH REWRITER")
    print("="*70)
    
    # Rewrite for search optimization
    print("\n[STEP 1] Optimizing search queries...")
    search_rewrite = rewrite_for_search(user_question)
    
    print(f"\nOriginal Question: {user_question}")
    print(f"\nOptimized News Queries:")
    for query in search_rewrite.get('news_queries', []):
        print(f"  - {query}")
    
    print(f"\nOptimized ArXiv Queries:")
    for query in search_rewrite.get('arxiv_queries', []):
        print(f"  - {query}")
    
    # Fetch content
    print("\n[STEP 2] Fetching content...")
    results = {
        "original_question": user_question,
        "rewritten_queries": search_rewrite,
        "search_results": []
    }
    
    # Combine news results
    all_news = {}
    for query in search_rewrite.get('news_queries', []):
        try:
            news = fetch_news(query)
            all_news[query] = news
        except Exception as e:
            print(f"Error fetching news for '{query}': {e}")
    
    # Combine arxiv results
    all_arxiv = {}
    for query in search_rewrite.get('arxiv_queries', []):
        try:
            arxiv = fetch_arxiv(query, max_results=5)
            all_arxiv[query] = arxiv
        except Exception as e:
            print(f"Error fetching arxiv for '{query}': {e}")
    
    results["search_results"] = {
        "news_by_query": all_news,
        "arxiv_by_query": all_arxiv
    }
    
    return results


def planning_only_with_rewriter(user_question: str):
    """
    If you only want to optimize the question for planning.
    Useful for deeply understanding a research topic.
    
    Args:
        user_question: The original user question
        
    Returns:
        Dictionary with optimized planning and plan
    """
    
    print("\n" + "="*70)
    print("PLANNING OPTIMIZATION WITH REWRITER")
    print("="*70)
    
    # Rewrite for planning
    print("\n[STEP 1] Optimizing question for planning...")
    planning_rewrite = rewrite_for_planning(user_question)
    
    print(f"\nOriginal Question: {user_question}")
    print(f"Rewritten Question: {planning_rewrite.get('rewritten_question')}")
    print(f"Research Focus: {planning_rewrite.get('research_focus')}")
    
    # Generate plan
    print("\n[STEP 2] Generating research plan...")
    plan_topic = planning_rewrite.get('rewritten_question')
    research_plan = generate_plan(str(plan_topic))
    
    print(f"\nResearch Plan:")
    for key, value in research_plan.items():
        print(f"  {key}. {value}")
    
    return {
        "original_question": user_question,
        "rewriter_output": planning_rewrite,
        "research_plan": research_plan
    }


if __name__ == "__main__":
    # Example questions to test
    test_questions = [
        "How do transformers work?",
        "What is the latest in AI safety?",
        "Can you explain quantum computing basics?",
    ]
    
    # Test the full pipeline with the first question
    if test_questions:
        result = research_pipeline_with_rewriter(test_questions[0])
        print("\n" + "="*70)
        print("FULL PIPELINE COMPLETE")
        print("="*70)
