import os
import json
import streamlit as st
from tool_wrapper import news_tool, arxiv_tool
from mcp_client import fetch_news, fetch_arxiv
from langchain_groq import ChatGroq
from rewriter_agent import rewrite_full_pipeline, rewrite_for_planning, rewrite_for_search
from planning_agent import generate_plan

if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = "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"

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Research Agent with Rewriter",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 Research Agent with Question Rewriter")

st.markdown("""
This agent uses **question rewriting** to:
1. **Optimize questions** for the planning process (clarity, scope, focus)
2. **Generate smart search queries** for news and arXiv (relevant results)
3. **Create research plans** based on rewritten questions
4. **Fetch grounded information** from the best sources
""")

# --- SIDEBAR CONFIG ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    mode = st.radio(
        "Select Mode:",
        ["Full Pipeline", "Search Only", "Planning Only", "Raw Rewriting"],
        help="Choose what you want to optimize"
    )
    
    include_search = st.checkbox("Include Content Fetching", value=True)
    show_details = st.checkbox("Show Detailed Output", value=False)

# --- MAIN INPUT ---
user_question = st.text_area(
    "Enter your research question:",
    placeholder="E.g., How do transformers work? What's new in AI safety? Can you explain quantum computing?",
    height=100
)

if st.button("🚀 Process Question", type="primary", use_container_width=True):
    if not user_question.strip():
        st.error("Please enter a research question")
    else:
        # --- STEP 1: REWRITE ---
        st.header("📝 Step 1: Question Rewriting")
        
        with st.spinner("Rewriting your question..."):
            rewrite_result = rewrite_full_pipeline(user_question)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Original Question")
            st.info(user_question)
        
        with col2:
            st.subheader("Rewritten for Planning")
            st.success(rewrite_result['planning_rewrite'].get('rewritten_question'))
        
        if show_details:
            st.divider()
            st.subheader("Rewriting Details")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Planning Focus:**")
                st.write(rewrite_result['planning_rewrite'].get('research_focus'))
            
            with col2:
                st.write("**Search Rationale:**")
                st.write(rewrite_result['search_rewrite'].get('search_rationale'))
        
        # --- CONDITIONAL EXECUTION ---
        if mode == "Full Pipeline":
            # --- STEP 2: PLANNING ---
            st.header("📋 Step 2: Research Planning")
            
            plan_topic = rewrite_result['recommended_plan_topic']
            
            with st.spinner("Generating research plan..."):
                research_plan = generate_plan(plan_topic)
            
            for key, value in research_plan.items():
                st.write(f"**{key}.** {value}")
            
            # --- STEP 3: SEARCH (if enabled) ---
            if include_search:
                st.header("🔍 Step 3: Fetching Relevant Content")
                
                news_queries = rewrite_result['recommended_search_queries']['news']
                arxiv_queries = rewrite_result['recommended_search_queries']['arxiv']
                
                tab1, tab2 = st.tabs(["📰 News Results", "📚 ArXiv Results"])
                
                with tab1:
                    st.subheader("News Search Queries")
                    for query in news_queries:
                        st.write(f"• {query}")
                    
                    with st.spinner("Fetching news..."):
                        try:
                            news_results = []
                            for query in news_queries[:2]:  # Limit to 2 queries
                                try:
                                    result = fetch_news(query)
                                    if result:
                                        news_results.append({"query": query, "content": result})
                                except Exception as e:
                                    st.warning(f"Could not fetch for '{query}': {str(e)}")
                            
                            if news_results:
                                for item in news_results:
                                    st.write(f"**Query:** {item['query']}")
                                    st.write(item['content'][:500] + "...")
                                    st.divider()
                        except Exception as e:
                            st.error(f"Error fetching news: {e}")
                
                with tab2:
                    st.subheader("ArXiv Search Queries")
                    for query in arxiv_queries:
                        st.write(f"• {query}")
                    
                    with st.spinner("Fetching papers..."):
                        try:
                            arxiv_results = []
                            for query in arxiv_queries[:2]:  # Limit to 2 queries
                                try:
                                    result = fetch_arxiv(query, max_results=3)
                                    if result:
                                        arxiv_results.append({"query": query, "content": result})
                                except Exception as e:
                                    st.warning(f"Could not fetch for '{query}': {str(e)}")
                            
                            if arxiv_results:
                                for item in arxiv_results:
                                    st.write(f"**Query:** {item['query']}")
                                    st.write(item['content'][:500] + "...")
                                    st.divider()
                        except Exception as e:
                            st.error(f"Error fetching arxiv: {e}")
        
        elif mode == "Search Only":
            st.header("🔍 Search Optimization")
            
            news_queries = rewrite_result['recommended_search_queries']['news']
            arxiv_queries = rewrite_result['recommended_search_queries']['arxiv']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📰 Optimized News Queries")
                for i, query in enumerate(news_queries, 1):
                    st.write(f"{i}. {query}")
            
            with col2:
                st.subheader("📚 Optimized ArXiv Queries")
                for i, query in enumerate(arxiv_queries, 1):
                    st.write(f"{i}. {query}")
            
            if include_search:
                st.divider()
                st.header("📊 Search Results")
                
                tab1, tab2 = st.tabs(["📰 News", "📚 ArXiv"])
                
                with tab1:
                    with st.spinner("Fetching news..."):
                        try:
                            for query in news_queries[:1]:
                                result = fetch_news(query)
                                st.write(f"**Query:** {query}")
                                st.write(result[:800] + "...")
                        except Exception as e:
                            st.error(f"Error: {e}")
                
                with tab2:
                    with st.spinner("Fetching papers..."):
                        try:
                            for query in arxiv_queries[:1]:
                                result = fetch_arxiv(query, max_results=3)
                                st.write(f"**Query:** {query}")
                                st.write(result[:800] + "...")
                        except Exception as e:
                            st.error(f"Error: {e}")
        
        elif mode == "Planning Only":
            st.header("📋 Planning Optimization")
            
            plan_topic = rewrite_result['recommended_plan_topic']
            st.info(f"**Plan Topic:** {plan_topic}")
            
            with st.spinner("Generating research plan..."):
                research_plan = generate_plan(plan_topic)
            
            st.subheader("📚 Research Study Plan")
            for key, value in research_plan.items():
                st.write(f"**{key}.** {value}")
        
        elif mode == "Raw Rewriting":
            st.header("🔧 Raw Rewriting Output")
            
            tab1, tab2 = st.tabs(["Planning Rewrite", "Search Rewrite"])
            
            with tab1:
                st.json(rewrite_result['planning_rewrite'])
            
            with tab2:
                st.json(rewrite_result['search_rewrite'])

# --- FOOTER ---
st.divider()
st.markdown("""
### How the Rewriter Agent Works:

1. **Planning Rewriter**: Takes your question and optimizes it for the research planner
   - Clarifies intent and scope
   - Focuses on conceptual understanding
   - Removes implementation details

2. **Search Rewriter**: Generates specialized queries for different sources
   - News queries: Recent developments, current events, applications
   - ArXiv queries: Academic papers, theoretical foundations, methodologies

3. **Integration**: The rewritten outputs feed into the planning and search workflows

### Tips for Best Results:
- Be specific about what you want to understand
- Use both Planning and Search modes for comprehensive research
- Check "Show Detailed Output" to understand the rewriting logic
""")
