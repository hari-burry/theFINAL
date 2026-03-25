"""
INTEGRATED RESEARCH WORKFLOW WITH REWRITER AGENT
================================================

This module shows the recommended workflow integrating the rewriter agent
into your existing pipeline for optimal results.

Flow:
  User Question
       ↓
  [REWRITER AGENT] ← Optimization step (NEW)
       ├─ Planning Rewrite
       ├─ Search Query Rewrite
       ↓
  Planning Agent (uses rewritten question)
       ↓
  Concept Engine (iterative understanding)
       ↓
  Search Agent (uses optimized search queries)
       ↓
  Final Response
"""

import os
import json
from typing import Dict, List, Optional

# Import your existing modules
from planning_agent import generate_plan_with_rewriter, generate_plan
from concept_engine import build_concept
from llm_scheduler import LLMScheduler
from mcp_client import fetch_news, fetch_arxiv

# Import rewriter functions
from rewriter_agent import rewrite_full_pipeline, rewrite_for_planning, rewrite_for_search

API_KEYS = [
    "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",
    "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",
    "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",
    "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"
]

scheduler = LLMScheduler(API_KEYS)


# ==========================================
# WORKFLOW 1: PLANNING-FIRST RESEARCH
# ==========================================

def planning_first_research(user_question: str, use_rewriter: bool = True) -> Dict:
    """
    Research workflow focused on building deep conceptual understanding.
    
    Flow: Question → [Rewriter] → Plan → Concepts → Search
    
    Best for: R esearch topics requiring deep understanding
    
    Args:
        user_question: The user's research question
        use_rewriter: Whether to optimize the question first
        
    Returns:
        Dictionary with plan, concepts, and recommended searches
    """
    
    print("\n" + "="*70)
    print("PLANNING-FIRST RESEARCH WORKFLOW")
    print("="*70)
    
    # Step 1: Rewrite for planning
    print(f"\n[STEP 1] Analyzing question...")
    if use_rewriter:
        rewrite_result = rewrite_for_planning(user_question)
        plan_topic = rewrite_result['rewritten_question']
        print(f"  Original: {user_question}")
        print(f"  Optimized: {plan_topic}")
        print(f"  Focus: {rewrite_result.get('research_focus', 'N/A')}")
    else:
        plan_topic = user_question
        print(f"  Using original: {user_question}")
    
    # Step 2: Generate focused research plan
    print(f"\n[STEP 2] Creating research plan...")
    plan = generate_plan(plan_topic)
    print(f"  Generated 5-point study plan:")
    for key, value in plan.items():
        print(f"    {key}. {value}")
    
    # Step 3: Build concepts for each subtopic
    print(f"\n[STEP 3] Building understanding...")
    concepts = {}
    for i in range(1, 6):
        key = str(i)
        if key in plan:
            subtopic = plan[key]
            print(f"    Processing: {subtopic}")
            try:
                concept = build_concept(subtopic, scheduler)
                concepts[key] = concept
            except Exception as e:
                print(f"    Error building concept: {e}")
                concepts[key] = None
    
    # Step 4: Generate search queries
    print(f"\n[STEP 4] Optimizing search queries...")
    if use_rewriter:
        search_rewrite = rewrite_for_search(user_question)
        search_queries = search_rewrite
        print(f"  News queries: {len(search_rewrite.get('news_queries', []))} generated")
        print(f"  ArXiv queries: {len(search_rewrite.get('arxiv_queries', []))} generated")
    else:
        search_queries = {
            'news_queries': [user_question],
            'arxiv_queries': [user_question]
        }
        print(f"  Using original question for search")
    
    return {
        'user_question': user_question,
        'plan_topic': plan_topic,
        'research_plan': plan,
        'concepts': concepts,
        'search_queries': search_queries,
        'workflow_type': 'planning-first'
    }


# ==========================================
# WORKFLOW 2: SEARCH-FIRST DISCOVERY
# ==========================================

def search_first_discovery(user_question: str, use_rewriter: bool = True, 
                          news_results: int = 5, arxiv_results: int = 5) -> Dict:
    """
    Research workflow focused on discovering current information first.
    
    Flow: Question → [Rewriter] → Search → Content → Plan
    
    Best for: Current events, recent developments, latest research
    
    Args:
        user_question: The user's research question
        use_rewriter: Whether to optimize the question first
        news_results: Number of news articles to fetch
        arxiv_results: Number of arxiv papers to fetch
        
    Returns:
        Dictionary with search results and recommended plan topic
    """
    
    print("\n" + "="*70)
    print("SEARCH-FIRST DISCOVERY WORKFLOW")
    print("="*70)
    
    # Step 1: Rewrite for search
    print(f"\n[STEP 1] Optimizing search queries...")
    if use_rewriter:
        search_rewrite = rewrite_for_search(user_question)
        news_queries = search_rewrite.get('news_queries', [user_question])
        arxiv_queries = search_rewrite.get('arxiv_queries', [user_question])
        search_rationale = search_rewrite.get('search_rationale', 'Query optimization applied')
        print(f"  Rationale: {search_rationale[:100]}...")
    else:
        news_queries = [user_question]
        arxiv_queries = [user_question]
    
    # Step 2: Fetch news results
    print(f"\n[STEP 2] Fetching latest news...")
    news_content = []
    for query in news_queries[:3]:  # Limit to 3 queries
        try:
            result = fetch_news(query)
            news_content.append({'query': query, 'content': result[:500]})
            print(f"  ✓ Fetched: {query}")
        except Exception as e:
            print(f"  ✗ Error with '{query}': {e}")
    
    # Step 3: Fetch arxiv papers
    print(f"\n[STEP 3] Fetching research papers...")
    arxiv_content = []
    for query in arxiv_queries[:3]:  # Limit to 3 queries
        try:
            result = fetch_arxiv(query, max_results=arxiv_results)
            arxiv_content.append({'query': query, 'content': result[:500]})
            print(f"  ✓ Fetched: {query}")
        except Exception as e:
            print(f"  ✗ Error with '{query}': {e}")
    
    # Step 4: Suggest research plan based on findings
    print(f"\n[STEP 4] Recommending research topic...")
    if use_rewriter:
        plan_rewrite = rewrite_for_planning(user_question)
        suggested_topic = plan_rewrite['rewritten_question']
        print(f"  Suggested: {suggested_topic}")
    else:
        suggested_topic = user_question
    
    return {
        'user_question': user_question,
        'news_results': news_content,
        'arxiv_results': arxiv_content,
        'suggested_plan_topic': suggested_topic,
        'workflow_type': 'search-first',
        'total_results': len(news_content) + len(arxiv_content)
    }


# ==========================================
# WORKFLOW 3: BALANCED RESEARCH
# ==========================================

def balanced_research(user_question: str) -> Dict:
    """
    Balanced research workflow combining both planning and search.
    
    Flow: Question → [Rewriter] → {Plan + Search in parallel} → Concepts
    
    Best for: Comprehensive research combining theory and practice
    
    Args:
        user_question: The user's research question
        
    Returns:
        Dictionary with plan, search results, and concepts
    """
    
    print("\n" + "="*70)
    print("BALANCED RESEARCH WORKFLOW")
    print("="*70)
    
    # Step 1: Full rewriting
    print(f"\n[STEP 1] Analyzing and optimizing question...")
    rewrite_result = rewrite_full_pipeline(user_question)
    plan_topic = rewrite_result['recommended_plan_topic']
    search_queries = rewrite_result['recommended_search_queries']
    
    print(f"  Original: {user_question}")
    print(f"  Plan topic: {plan_topic}")
    print(f"  Search queries: {len(search_queries['news'])} news, {len(search_queries['arxiv'])} arxiv")
    
    # Step 2: Generate plan
    print(f"\n[STEP 2] Creating research plan...")
    plan = generate_plan(plan_topic)
    print(f"  Generated 5-point study plan")
    
    # Step 3: Fetch search results
    print(f"\n[STEP 3] Gathering research content...")
    news_results = []
    arxiv_results = []
    
    for query in search_queries['news'][:2]:
        try:
            result = fetch_news(query)
            news_results.append({'query': query, 'content': result[:300]})
        except:
            pass
    
    for query in search_queries['arxiv'][:2]:
        try:
            result = fetch_arxiv(query, max_results=3)
            arxiv_results.append({'query': query, 'content': result[:300]})
        except:
            pass
    
    print(f"  News articles: {len(news_results)}")
    print(f"  Research papers: {len(arxiv_results)}")
    
    # Step 4: Build concepts
    print(f"\n[STEP 4] Building conceptual understanding...")
    concepts = {}
    for i in range(1, 4):  # Build first 3 concepts to save time
        key = str(i)
        if key in plan:
            try:
                concept = build_concept(plan[key], scheduler)
                concepts[key] = concept
                print(f"  ✓ Built concept for subtopic {i}")
            except:
                pass
    
    return {
        'user_question': user_question,
        'plan_topic': plan_topic,
        'research_plan': plan,
        'concepts': concepts,
        'news_results': news_results,
        'arxiv_results': arxiv_results,
        'workflow_type': 'balanced',
        'search_attempts': len(news_results) + len(arxiv_results)
    }


# ==========================================
# WORKFLOW 4: QUICK TURNAROUND
# ==========================================

def quick_research(user_question: str) -> Dict:
    """
    Fast research workflow for quick answers.
    
    Flow: Question → [Rewriter] → Best search query → Content
    
    Best for: Quick lookups, breaking news, current information
    Time: ~30 seconds
    
    Args:
        user_question: The user's research question
        
    Returns:
        Dictionary with top search result
    """
    
    print(f"\n[QUICK] Researching: {user_question}")
    
    # Optimize search query
    search_rewrite = rewrite_for_search(user_question)
    best_news_query = search_rewrite.get('news_queries', [user_question])[0]
    best_arxiv_query = search_rewrite.get('arxiv_queries', [user_question])[0]
    
    # Fetch best results
    print(f"  Fetching from: {best_news_query}")
    news = fetch_news(best_news_query)
    
    print(f"  Fetching from: {best_arxiv_query}")
    arxiv = fetch_arxiv(best_arxiv_query, max_results=2)
    
    return {
        'user_question': user_question,
        'news_result': news[:500] if news else "No results",
        'arxiv_result': arxiv[:500] if arxiv else "No results",
        'workflow_type': 'quick',
        'queries_used': [best_news_query, best_arxiv_query]
    }


# ==========================================
# MAIN ENTRY POINT
# ==========================================

if __name__ == "__main__":
    # Example questions
    test_questions = [
        "What is machine learning?",
        "Tell me about recent AI developments",
        "How do neural networks learn?",
    ]
    
    # Test different workflows
    question = test_questions[0]
    
    print("\n" + "="*70)
    print("INTEGRATED WORKFLOW EXAMPLES")
    print("="*70)
    
    # Try planning-first workflow
    result1 = planning_first_research(question)
    print("\n✓ Planning-first workflow complete")
    
    # Try search-first workflow
    result2 = search_first_discovery(question)
    print("\n✓ Search-first workflow complete")
    
    # Try balanced workflow
    result3 = balanced_research(question)
    print("\n✓ Balanced workflow complete")
    
    # Try quick workflow
    result4 = quick_research(question)
    print("\n✓ Quick research complete")
