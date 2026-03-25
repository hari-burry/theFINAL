"""
Test script to validate the Rewriter Agent implementation.
Run with: python test_rewriter_agent.py
"""

import sys
import json

def test_imports():
    """Test that all modules can be imported"""
    print("=" * 70)
    print("TEST 1: Module Imports")
    print("=" * 70)
    
    try:
        from rewriter_agent import rewrite_for_planning, rewrite_for_search, rewrite_full_pipeline
        print("✅ rewriter_agent imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import rewriter_agent: {e}")
        return False
    
    try:
        from planning_agent import generate_plan
        print("✅ planning_agent imported successfully")
    except ImportError as e:
        print(f"⚠️  planning_agent import issue (may be okay): {e}")
    
    try:
        from mcp_client import fetch_news, fetch_arxiv
        print("✅ mcp_client imported successfully")
    except ImportError as e:
        print(f"⚠️  mcp_client import issue (may be okay): {e}")
    
    try:
        from llm_scheduler import LLMScheduler
        print("✅ llm_scheduler imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import llm_scheduler: {e}")
        return False
    
    return True


def test_planning_rewrite():
    """Test planning rewriter function"""
    print("\n" + "=" * 70)
    print("TEST 2: Plan Rewriter Function")
    print("=" * 70)
    
    try:
        from rewriter_agent import rewrite_for_planning
        
        test_question = "How do I get started with machine learning?"
        print(f"\n📝 Input Question: {test_question}")
        
        print("\n🔄 Processing... (this may take 10-30 seconds)")
        result = rewrite_for_planning(test_question)
        
        # Validate output structure
        required_fields = ['original_question', 'rewritten_question', 'research_focus']
        missing_fields = [f for f in required_fields if f not in result]
        
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False
        
        print(f"\n✅ Rewriter executed successfully!")
        print(f"\n📋 Original: {result['original_question']}")
        print(f"🔄 Rewritten: {result['rewritten_question']}")
        print(f"🎯 Focus: {result['research_focus']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in planning rewriter: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_rewrite():
    """Test search query rewriter function"""
    print("\n" + "=" * 70)
    print("TEST 3: Search Query Rewriter Function")
    print("=" * 70)
    
    try:
        from rewriter_agent import rewrite_for_search
        
        test_question = "What is happening with AI safety?"
        print(f"\n📝 Input Question: {test_question}")
        
        print("\n🔄 Processing... (this may take 10-30 seconds)")
        result = rewrite_for_search(test_question)
        
        # Validate output structure
        required_fields = ['original_question', 'news_queries', 'arxiv_queries', 'search_rationale']
        missing_fields = [f for f in required_fields if f not in result]
        
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False
        
        if not isinstance(result['news_queries'], list) or len(result['news_queries']) == 0:
            print("❌ news_queries is not a valid list")
            return False
        
        if not isinstance(result['arxiv_queries'], list) or len(result['arxiv_queries']) == 0:
            print("❌ arxiv_queries is not a valid list")
            return False
        
        print(f"\n✅ Search rewriter executed successfully!")
        print(f"\n📰 News Queries:")
        for i, q in enumerate(result['news_queries'], 1):
            print(f"   {i}. {q}")
        
        print(f"\n📚 ArXiv Queries:")
        for i, q in enumerate(result['arxiv_queries'], 1):
            print(f"   {i}. {q}")
        
        print(f"\n💡 Rationale: {result['search_rationale'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in search rewriter: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_pipeline():
    """Test full rewriting pipeline"""
    print("\n" + "=" * 70)
    print("TEST 4: Full Rewriting Pipeline")
    print("=" * 70)
    
    try:
        from rewriter_agent import rewrite_full_pipeline
        
        test_question = "Tell me about neural networks"
        print(f"\n📝 Input Question: {test_question}")
        
        print("\n🔄 Processing... (this may take 20-60 seconds)")
        result = rewrite_full_pipeline(test_question)
        
        # Validate output structure
        required_fields = ['original_question', 'planning_rewrite', 'search_rewrite', 'recommended_plan_topic']
        missing_fields = [f for f in required_fields if f not in result]
        
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False
        
        print(f"\n✅ Full pipeline executed successfully!")
        print(f"\n📋 Original: {result['original_question']}")
        print(f"🔄 Rewritten for Planning: {result['recommended_plan_topic']}")
        print(f"\n📰 News Queries: {len(result['recommended_search_queries']['news'])} generated")
        print(f"📚 ArXiv Queries: {len(result['recommended_search_queries']['arxiv'])} generated")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in full pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompts_updated():
    """Test that prompts.py has been updated with new prompts"""
    print("\n" + "=" * 70)
    print("TEST 5: Prompts Configuration")
    print("=" * 70)
    
    try:
        from prompts import PLANNER_QUESTION_REWRITER_PROMPT, NEWS_ARXIV_QUERY_REWRITER_PROMPT
        
        print("✅ PLANNER_QUESTION_REWRITER_PROMPT found in prompts.py")
        print("✅ NEWS_ARXIV_QUERY_REWRITER_PROMPT found in prompts.py")
        
        if "rewrite" in PLANNER_QUESTION_REWRITER_PROMPT.lower():
            print("✅ PLANNER_QUESTION_REWRITER_PROMPT has expected content")
        else:
            print("⚠️  PLANNER_QUESTION_REWRITER_PROMPT might not be correct")
        
        if "news" in NEWS_ARXIV_QUERY_REWRITER_PROMPT.lower():
            print("✅ NEWS_ARXIV_QUERY_REWRITER_PROMPT has expected content")
        else:
            print("⚠️  NEWS_ARXIV_QUERY_REWRITER_PROMPT might not be correct")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing prompts: {e}")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "REWRITER AGENT - TEST SUITE" + " " * 27 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = []
    
    # Test 1: Imports
    results.append(("Module Imports", test_imports()))
    
    if not results[0][1]:
        print("\n❌ Import test failed. Cannot continue.")
        return results
    
    # Test 2: Planning Rewriter
    results.append(("Plan Rewriter", test_planning_rewrite()))
    
    # Test 3: Search Rewriter
    results.append(("Search Rewriter", test_search_rewrite()))
    
    # Test 4: Full Pipeline
    results.append(("Full Pipeline", test_full_pipeline()))
    
    # Test 5: Prompts Updated
    results.append(("Prompts Configuration", test_prompts_updated()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Rewriter agent is ready to use.")
        print("\nNext steps:")
        print("  1. Try: streamlit run streamlit_rewriter_demo.py")
        print("  2. Or: python integration_example.py")
        print("  3. Read: REWRITER_QUICK_START.md")
    elif passed >= total - 1:
        print("\n⚠️  Most tests passed. There may be minor issues.")
    else:
        print("\n❌ Multiple test failures. Check the output above.")
    
    return results


if __name__ == "__main__":
    try:
        results = run_all_tests()
        
        # Exit with appropriate code
        passed = sum(1 for _, result in results if result)
        total = len(results)
        sys.exit(0 if passed == total else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
