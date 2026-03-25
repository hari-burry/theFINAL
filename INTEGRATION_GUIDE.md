# 🔗 REWRITER AGENT - INTEGRATION GUIDE

## Overview

Your existing workflow has been **seamlessly integrated** with the rewriter agent. This guide shows what changed and how to use the new features.

---

## What Was Integrated

### 1. ✅ Planning Agent (Enhanced)

**File:** [planning_agent.py](planning_agent.py)

**What Changed:**

- Added rewriter agent import (optional, with fallback)
- Added new function: `generate_plan_with_rewriter()`

**Before:**

```python
# Old way (still works)
plan = generate_plan("How do neural networks work?")
```

**After:**

```python
# New way with automatic question optimization
result = generate_plan_with_rewriter("How do neural networks work?")
# Returns: {plan, plan_topic, rewrite_info}

# Or still use the old way
plan = generate_plan("Your topic...")  # Still supported
```

**Usage Examples:**

```python
from planning_agent import generate_plan_with_rewriter

# With automatic rewriting (recommended)
result = generate_plan_with_rewriter(
    user_question="How can I learn machine learning?",
    use_rewriter=True  # Auto-optimize
)

print(f"Rewritten topic: {result['plan_topic']}")
print(f"Was optimized: {result['was_rewritten']}")
print(f"Study plan: {result['plan']}")

# Without rewriting (if you just want the old behavior)
result = generate_plan_with_rewriter(
    user_question="Your topic",
    use_rewriter=False
)
```

---

### 2. ✅ Research Chat Agent (Enhanced)

**File:** [streamlit_researchagent.py](streamlit_researchagent.py)

**What Changed:**

- Added rewriter agent import (optional, with fallback)
- Added helper functions:
    - `optimize_search_query()` - Optimizes queries with caching
    - `fetch_best_results()` - Fetches with optimized queries

**New Features:**

- Automatic query optimization before searching
- Caching to avoid redundant API calls
- Better results from news and arXiv searches

**Usage Example:**

```python
import streamlit as st
from streamlit_researchagent import optimize_search_query, fetch_best_results

# Get optimized search queries
user_question = st.text_input("Ask something grounded in news...")

if user_question:
    # Automatically optimized!
    optimized = optimize_search_query(user_question)

    # Fetch with optimized queries
    results = fetch_best_results(user_question)

    # Display news
    for item in results['news_results']:
        st.write(f"**Query:** {item['query']}")
        st.write(item['content'])

    # Display arXiv
    for item in results['arxiv_results']:
        st.write(f"**Query:** {item['query']}")
        st.write(item['content'])
```

---

### 3. ✅ New: Integrated Workflow Module

**File:** [integrated_workflow.py](integrated_workflow.py) ⭐ **NEW FILE**

**Purpose:** Complete research workflows combining your existing modules with the rewriter

**Four Workflow Options:**

#### Workflow 1: Planning-First Research

```python
from integrated_workflow import planning_first_research

result = planning_first_research(
    user_question="What is machine learning?",
    use_rewriter=True
)

# Returns: plan, concepts, search queries
```

**When to use:** For deep conceptual understanding

#### Workflow 2: Search-First Discovery

```python
from integrated_workflow import search_first_discovery

result = search_first_discovery(
    user_question="Tell me about recent AI developments",
    use_rewriter=True,
    news_results=5,
    arxiv_results=5
)

# Returns: news, arxiv papers, suggested plan topic
```

**When to use:** For current information and breaking news

#### Workflow 3: Balanced Research

```python
from integrated_workflow import balanced_research

result = balanced_research(
    user_question="How do transformers work?"
)

# Returns: plan, concepts, news, papers - everything!
```

**When to use:** Comprehensive research combining theory and practice

#### Workflow 4: Quick Research

```python
from integrated_workflow import quick_research

result = quick_research(
    user_question="What's new in quantum computing?"
)

# Returns: quick news + paper results (~30 seconds)
```

**When to use:** Fast lookups and quick answers

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│           YOUR RESEARCH PIPELINE (NOW ENHANCED)         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  planning_agent.py (ENHANCED)                    │  │
│  │  ├─ generate_plan() [original - still works]     │  │
│  │  └─ generate_plan_with_rewriter() [NEW]          │  │
│  └────┬─────────────────────────────────────────────┘  │
│       │                                                 │
│  ┌────▼──────────────────────────────────────────────┐  │
│  │  streamlit_researchagent.py (ENHANCED)           │  │
│  │  ├─ optimize_search_query() [NEW]                │  │
│  │  └─ fetch_best_results() [NEW]                   │  │
│  └────┬─────────────────────────────────────────────┘  │
│       │                                                 │
│  ┌────▼──────────────────────────────────────────────┐  │
│  │  integrated_workflow.py [NEW - RECOMMENDED]      │  │
│  │  ├─ planning_first_research()                    │  │
│  │  ├─ search_first_discovery()                     │  │
│  │  ├─ balanced_research()                          │  │
│  │  └─ quick_research()                             │  │
│  └────┬─────────────────────────────────────────────┘  │
│       │                                                 │
│  ┌────▼──────────────────────────────────────────────┐  │
│  │         REWRITER AGENT                           │  │
│  │  ├─ rewrite_for_planning()                       │  │
│  │  ├─ rewrite_for_search()                         │  │
│  │  └─ rewrite_full_pipeline()                      │  │
│  └────┬─────────────────────────────────────────────┘  │
│       │                                                 │
│  ┌────▼──────────────────────────────────────────────┐  │
│  │         EXISTING MODULES                         │  │
│  │  ├─ concept_engine.py                            │  │
│  │  ├─ mcp_client.py                                │  │
│  │  └─ tool_wrapper.py                              │  │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start - Choose Your Path

### Path 1: Enhance Planning (Easiest)

```python
from planning_agent import generate_plan_with_rewriter

# That's it!
result = generate_plan_with_rewriter("Your question")
```

### Path 2: Use Complete Workflow (Recommended)

```python
from integrated_workflow import balanced_research

# One function does everything
result = balanced_research("Your question")
```

### Path 3: Run Existing Apps (No Changes Needed)

```bash
# Your existing Streamlit apps still work!
streamlit run streamlit_researchagent.py

# Now with rewriter (auto-used if available)
```

---

## Backward Compatibility

✅ **Everything is backward compatible!**

- Old code: `generate_plan(topic)` still works
- Old code: `fetch_news(query)` still works
- Your existing apps: Run without changes
- Rewriter is optional: Falls back gracefully if not available

---

## File Changes Summary

| File                         | Change                                | Impact                |
| ---------------------------- | ------------------------------------- | --------------------- |
| `planning_agent.py`          | Added `generate_plan_with_rewriter()` | Optional enhancement  |
| `streamlit_researchagent.py` | Added helper functions                | Better search results |
| `integrated_workflow.py`     | NEW WORKFLOW MODULE                   | Recommended approach  |
| `prompts.py`                 | Already updated                       | No changes needed     |

---

## Usage Patterns

### Pattern 1: Just Plan Optimization

```python
from planning_agent import generate_plan_with_rewriter

result = generate_plan_with_rewriter("How do LLMs work?")
plan = result['plan']
print(plan)  # Your 5-point study plan!
```

### Pattern 2: Just Search Optimization

```python
from streamlit_researchagent import optimize_search_query, fetch_best_results

question = "Latest developments in AI"
results = fetch_best_results(question)
print(results['news_results'])   # Best news articles
print(results['arxiv_results'])  # Best papers
```

### Pattern 3: Complete Research (RECOMMENDED)

```python
from integrated_workflow import balanced_research

result = balanced_research("Your research topic")
print(result['plan_topic'])        # Optimized topic
print(result['research_plan'])      # 5-point plan
print(result['concepts'])           # Built concepts
print(result['news_results'])       # Latest news
print(result['arxiv_results'])      # Latest papers
```

### Pattern 4: Specific Workflow

```python
from integrated_workflow import planning_first_research, search_first_discovery

# For deep understanding
result = planning_first_research("Your topic")

# For current information
result = search_first_discovery("Your topic")
```

---

## Real-World Examples

### Example 1: Teaching a Concept

```python
from integrated_workflow import planning_first_research

# Focus on building understanding
result = planning_first_research(
    "What is reinforcement learning?",
    use_rewriter=True
)

# Get detailed plan and concepts
study_plan = result['research_plan']
concepts = result['concepts']
```

### Example 2: Researching Current Event

```python
from integrated_workflow import search_first_discovery

# Focus on latest information
result = search_first_discovery(
    "What are the latest breakthroughs in quantum computing?",
    use_rewriter=True
)

# Get news and papers
news = result['news_results']
papers = result['arxiv_results']
```

### Example 3: Comprehensive Research Doc

```python
from integrated_workflow import balanced_research

# Get everything
result = balanced_research("How do neural networks work?")

# Build comprehensive document
topic = result['plan_topic']
plan = result['research_plan']
concepts = result['concepts']
news = result['news_results']
papers = result['arxiv_results']

# Combine into document
```

---

## Testing Your Integration

### Test 1: Planning Rewriter

```bash
python -c "
from planning_agent import generate_plan_with_rewriter
result = generate_plan_with_rewriter('What is AI?')
print('Plan:', result['plan'])
print('Was rewritten:', result['was_rewritten'])
"
```

### Test 2: Search Optimization

```bash
python -c "
from streamlit_researchagent import optimize_search_query
queries = optimize_search_query('Tell me about AI')
print('News queries:', queries['news_queries'])
print('ArXiv queries:', queries['arxiv_queries'])
"
```

### Test 3: Complete Workflow

```bash
python -c "
from integrated_workflow import balanced_research
result = balanced_research('What is machine learning?')
print('Topics found:', len(result['research_plan']))
print('Concepts built:', len(result['concepts']))
"
```

---

## Configuration & Customization

### Disable Rewriter (Fall Back to Original Behavior)

```python
# In planning_agent.py
result = generate_plan_with_rewriter(
    question="Your topic",
    use_rewriter=False  # Disable rewriter
)

# Or just use the original function
result = generate_plan("Your topic")
```

### Customize Search Parameters

```python
from integrated_workflow import search_first_discovery

result = search_first_discovery(
    user_question="Your topic",
    use_rewriter=True,
    news_results=10,      # Get more news
    arxiv_results=10      # Get more papers
)
```

### Customize Workflow Steps

```python
# Extend integrated_workflow.py with your own workflow:

def my_custom_workflow(user_question):
    from rewriter_agent import rewrite_full_pipeline
    from planning_agent import generate_plan
    from mcp_client import fetch_news

    # Step 1: Rewrite
    rewritten = rewrite_full_pipeline(user_question)

    # Step 2: Plan
    plan = generate_plan(rewritten['recommended_plan_topic'])

    # Step 3: Your custom logic
    news = fetch_news(rewritten['recommended_search_queries']['news'][0])

    # Return whatever you need
    return {'plan': plan, 'news': news}
```

---

## Monitoring & Debugging

### Check if Rewriter is Available

```python
from planning_agent import REWRITER_AVAILABLE
print(f"Rewriter available: {REWRITER_AVAILABLE}")

from streamlit_researchagent import REWRITER_AVAILABLE
print(f"In app: {REWRITER_AVAILABLE}")
```

### See What Was Rewritten

```python
result = generate_plan_with_rewriter("Your question")

if result['was_rewritten']:
    print(f"Original: {result['rewrite_info']['original_question']}")
    print(f"Optimized: {result['rewrite_info']['rewritten_question']}")
    print(f"Focus: {result['rewrite_info']['research_focus']}")
```

### Verify Search Query Optimization

```python
from streamlit_researchagent import optimize_search_query

queries = optimize_search_query("Your question")
print(f"Rationale: {queries['search_rationale']}")
for q in queries['news_queries']:
    print(f"  - {q}")
```

---

## Performance Tips

1. **Use Caching** - Search queries are cached automatically
2. **Batch Processing** - Process multiple questions together
3. **Selective Workflows** - Use planning-first OR search-first depending on need
4. **Quick Mode** - Use `quick_research()` for fast answers

---

## Migration Guide

### From Old to New

**Before:**

```python
from planning_agent import generate_plan
plan = generate_plan("Your topic")
```

**After (Recommended):**

```python
from planning_agent import generate_plan_with_rewriter
result = generate_plan_with_rewriter("Your topic")
plan = result['plan']
```

**Still Works (Unchanged):**

```python
from planning_agent import generate_plan
plan = generate_plan("Your optimized topic")
```

---

## Summary

Your system is now **integrated** with the rewriter agent:

✅ **planning_agent.py** - Enhanced with `generate_plan_with_rewriter()`  
✅ **streamlit_researchagent.py** - Enhanced with search optimization  
✅ **integrated_workflow.py** - NEW! Complete workflows  
✅ **Backward compatible** - All old code still works  
✅ **Easy to use** - Choose your workflow and go

---

## Next Steps

1. **Try the new functions:**

    ```bash
    python integrated_workflow.py
    ```

2. **Test in your Streamlit app:**

    ```bash
    streamlit run streamlit_researchagent.py
    ```

3. **Or build your own workflow:**
    ```python
    from integrated_workflow import balanced_research
    result = balanced_research("Your question")
    ```

---

**You're all set! Your rewriter agent is now fully integrated.** 🎉
