# 🎯 Rewriter Agent - Usage Scenarios & Reference Guide

## Quick Decision Tree

```
START: Do you have a user research question?
  │
  ├─ YES, and I want to create a research PLAN
  │  └─ Use: rewrite_for_planning()
  │     Then: generate_plan(rewritten_question)
  │
  ├─ YES, and I want to fetch NEWS & ARXIV content
  │  └─ Use: rewrite_for_search()
  │     Then: fetch_news() + fetch_arxiv() with returned queries
  │
  ├─ YES, and I want EVERYTHING (plan + search)
  │  └─ Use: rewrite_full_pipeline()
  │     Then: use both planning and search results
  │
  └─ NEED STREAMLIT DEMO?
     └─ Run: streamlit run streamlit_rewriter_demo.py
```

---

## Scenario 1: Creating Better Research Plans

**Goal:** Generate a more focused research study plan from a user question

### Code

```python
from rewriter_agent import rewrite_for_planning
from planning_agent import generate_plan

# User's original question
user_question = "How can I learn machine learning?"

# Step 1: Rewrite for planning
rewrite_result = rewrite_for_planning(user_question)
optimized_topic = rewrite_result['rewritten_question']

# Step 2: Generate plan with optimized topic
research_plan = generate_plan(optimized_topic)

# Use the plan
for key, value in research_plan.items():
    print(f"{key}. {value}")
```

### What Happens

```
INPUT:  "How can I learn machine learning?"
         (too vague, too practical)
           ↓
REWRITER: "Fundamental Concepts and Algorithms in Machine Learning"
         (clear, specific, theory-focused)
           ↓
PLANNER:  1. Fundamentals: Supervised vs Unsupervised Learning
          2. Statistical Foundations: Probability and Bayesian Inference
          3. Algorithm Families: Decision Trees, Regression, SVM
          4. Advanced Topics: Ensemble Methods and Regularization
          5. Modern Approaches: Neural Networks and Deep Learning
```

### When to Use

- ✅ Need focused study plans
- ✅ Questions are too vague
- ✅ Want to shift focus from "how to" to "understand"
- ✅ Need multiple subtopics for deep learning

---

## Scenario 2: Optimizing Search Queries

**Goal:** Get better search results from news and academic sources

### Code

```python
from rewriter_agent import rewrite_for_search
from mcp_client import fetch_news, fetch_arxiv

# User's original question
user_question = "Tell me about recent AI developments"

# Step 1: Rewrite for search
rewrite_result = rewrite_for_search(user_question)
news_queries = rewrite_result['news_queries']
arxiv_queries = rewrite_result['arxiv_queries']

# Step 2: Fetch using optimized queries
news_results = []
for query in news_queries:
    result = fetch_news(query)
    news_results.append(result)

arxiv_results = []
for query in arxiv_queries:
    result = fetch_arxiv(query, max_results=5)
    arxiv_results.append(result)
```

### What Happens

```
INPUT:  "Tell me about recent AI developments"
        (generic search term)
          ↓
REWRITER generates:
  News Queries:
    - "AI breakthroughs 2024"
    - "machine learning industry trends"
    - "artificial intelligence applications"

  ArXiv Queries:
    - "large language model architectures"
    - "deep learning methodology"
    - "neural network optimization"
          ↓
SEARCH:  Better results from specific, targeted searches
```

### When to Use

- ✅ Want news-focused current information
- ✅ Want academic paper results
- ✅ Generic search terms return poor results
- ✅ Need BOTH current events and research papers

---

## Scenario 3: Complete Research Pipeline

**Goal:** Full optimization from question to results

### Code

```python
from rewriter_agent import rewrite_full_pipeline
from planning_agent import generate_plan
from mcp_client import fetch_news, fetch_arxiv

# User's original question
user_question = "What are the latest developments in computer vision?"

# Step 1: Full rewriting
result = rewrite_full_pipeline(user_question)

# Step 2: Create research plan
plan_topic = result['recommended_plan_topic']
research_plan = generate_plan(plan_topic)

# Step 3: Fetch content
news_query = result['recommended_search_queries']['news'][0]
arxiv_query = result['recommended_search_queries']['arxiv'][0]

news_content = fetch_news(news_query)
arxiv_content = fetch_arxiv(arxiv_query, max_results=5)

# Step 4: Pass to concept engine or use directly
print(f"Topic: {plan_topic}")
print(f"Plan: {research_plan}")
print(f"News: {news_content[:200]}")
print(f"Papers: {arxiv_content[:200]}")
```

### What Happens

```
INPUT:  "What are the latest developments in computer vision?"
          ↓
REWRITER OPTIMIZES:
  - For Planning: "Computer Vision: Foundational Concepts and Modern Applications"
  - For Search: Multiple specialized news and arxiv queries
          ↓
PLANNER CREATES:
  1. Image Processing Fundamentals
  2. Convolutional Neural Networks
  3. Object Detection and Recognition
  4. Semantic and Instance Segmentation
  5. Modern Vision Architectures
          ↓
SEARCH FETCHES:
  - Latest news about vision applications
  - Recent academic papers on vision methods
          ↓
OUTPUT: Complete research package ✅
```

### When to Use

- ✅ Want comprehensive research coverage
- ✅ Need both theory and current information
- ✅ Creating detailed research documents
- ✅ Following complete pipeline from question → understanding

---

## Scenario 4: Interactive Exploration (Streamlit)

**Goal:** Explore and test incrementally in a UI

### How to Use

```bash
streamlit run streamlit_rewriter_demo.py
```

### Features

- **Full Pipeline Mode:** See everything in action
- **Search Only Mode:** Focus on optimizing search queries
- **Planning Only Mode:** Focus on creating plans
- **Raw Rewriting Mode:** Debug and see exact JSON outputs

### When to Use

- ✅ Learning how the rewriter works
- ✅ Testing different questions
- ✅ Debugging rewriting logic
- ✅ Demonstrating to others
- ✅ Exploring capabilities

---

## Scenario 5: Custom Integration

**Goal:** Add to your existing agent system

### Integration Point A: Before Planning

```python
# BEFORE: planning_agent.py
def generate_plan(topic: str):
    # ... existing code

# AFTER: planning_agent.py
from rewriter_agent import rewrite_for_planning

def generate_plan_with_rewriter(user_question: str):
    # Rewrite first
    rewritten = rewrite_for_planning(user_question)

    # Then plan with rewritten question
    return generate_plan(rewritten['rewritten_question'])
```

### Integration Point B: Before Search

```python
# BEFORE: streamlit_researchagent.py
news = fetch_news(user_input)

# AFTER: streamlit_researchagent.py
from rewriter_agent import rewrite_for_search

rewritten = rewrite_for_search(user_input)
news = fetch_news(rewritten['news_queries'][0])
```

### Integration Point C: At Pipeline Start

```python
# BEFORE: In your main orchestration
def research(user_question):
    plan = generate_plan(user_question)
    return plan

# AFTER: In your main orchestration
from rewriter_agent import rewrite_full_pipeline

def research(user_question):
    rewritten = rewrite_full_pipeline(user_question)
    plan = generate_plan(rewritten['recommended_plan_topic'])
    return plan
```

### When to Use

- ✅ Integrating into existing code
- ✅ Adding to multi-agent systems
- ✅ Customizing workflow
- ✅ Building production systems

---

## Scenario 6: Batch Processing

**Goal:** Process multiple questions at once

### Code

```python
from rewriter_agent import rewrite_full_pipeline
import json

questions = [
    "What is machine learning?",
    "How do neural networks work?",
    "Tell me about RL",
]

results = {}

for q in questions:
    result = rewrite_full_pipeline(q)
    results[q] = {
        'plan_topic': result['recommended_plan_topic'],
        'news_queries': result['recommended_search_queries']['news'],
        'arxiv_queries': result['recommended_search_queries']['arxiv']
    }

# Save results
with open('rewrite_results.json', 'w') as f:
    json.dump(results, f, indent=2)
```

### When to Use

- ✅ Processing multiple research questions
- ✅ Building research batches
- ✅ Comparing different questions
- ✅ Bulk operations

---

## Scenario 7: Domain-Specific Customization

**Goal:** Specialize rewriter for your domain

### Code

```python
# Create a domain-specific wrapper
from rewriter_agent import rewrite_for_planning, rewrite_for_search

def rewrite_for_medical_research(question: str):
    """Rewrite optimized for medical research"""
    # Could add domain rules, post-processing, etc.
    result = rewrite_for_planning(question)

    # Could enhance with medical-specific logic
    result['domain'] = 'medical'

    return result

def rewrite_for_quantum_physics(question: str):
    """Rewrite optimized for quantum physics"""
    result = rewrite_for_planning(question)
    result['domain'] = 'quantum_physics'
    return result
```

### When to Use

- ✅ Specialized domain knowledge
- ✅ Industry-specific research
- ✅ Academic discipline focus
- ✅ Custom prompt tuning

---

## Quick Copy-Paste Templates

### Template 1: Simple Planning

```python
from rewriter_agent import rewrite_for_planning
from planning_agent import generate_plan

q = "YOUR_QUESTION_HERE"
r = rewrite_for_planning(q)
p = generate_plan(r['rewritten_question'])
print(p)
```

### Template 2: Simple Search

```python
from rewriter_agent import rewrite_for_search
from mcp_client import fetch_news, fetch_arxiv

q = "YOUR_QUESTION_HERE"
r = rewrite_for_search(q)
news = fetch_news(r['news_queries'][0])
arxiv = fetch_arxiv(r['arxiv_queries'][0])
print(news, arxiv)
```

### Template 3: Full Pipeline

```python
from rewriter_agent import rewrite_full_pipeline

q = "YOUR_QUESTION_HERE"
r = rewrite_full_pipeline(q)
print("Plan:", r['recommended_plan_topic'])
print("News:", r['recommended_search_queries']['news'])
```

### Template 4: Loop Over Multiple

```python
from rewriter_agent import rewrite_for_planning

questions = ["Q1", "Q2", "Q3"]
for q in questions:
    r = rewrite_for_planning(q)
    print(f"Q: {q} → {r['rewritten_question']}")
```

---

## Performance Considerations

### API Calls Per Function

| Function                  | API Calls   | Approx Time |
| ------------------------- | ----------- | ----------- |
| `rewrite_for_planning()`  | 1 LLM call  | 10-30 sec   |
| `rewrite_for_search()`    | 1 LLM call  | 10-30 sec   |
| `rewrite_full_pipeline()` | 2 LLM calls | 20-60 sec   |

### Optimization Tips

```python
# TIP 1: Cache results for repeated questions
from functools import lru_cache
from rewriter_agent import rewrite_for_planning

@lru_cache(maxsize=100)
def cached_rewrite(q):
    return rewrite_for_planning(q)

# TIP 2: Use only what you need
# If you only need planning, don't call full_pipeline

# TIP 3: Batch similar questions
# Process multiple at once for efficiency
```

---

## Troubleshooting by Scenario

### Scenario: "Questions are still too vague after rewriting"

**Solution:** The rewriter can't fix extremely vague input

```python
# ❌ Too vague
"Tell me about AI"

# ✅ Better
"What are the mathematical foundations of artificial intelligence?"
```

### Scenario: "Search results are still irrelevant"

**Solution:** Check the generated queries first

```python
result = rewrite_for_search(q)
print("Generated queries:")
print(result['news_queries'])
print(result['arxiv_queries'])
print("Rationale:", result['search_rationale'])
```

### Scenario: "API calls failing"

**Solution:** Use the test suite

```bash
python test_rewriter_agent.py
```

### Scenario: "Need different behavior"

**Solution:** Customize the prompts in prompts.py

```python
# In prompts.py
PLANNER_QUESTION_REWRITER_PROMPT = """
Your custom instructions here...
"""
```

---

## Recommended Reading Order

1. 📄 **This file** - Understand different scenarios
2. 🚀 **REWRITER_QUICK_START.md** - Get started quickly
3. 📚 **REWRITER_AGENT_DOCS.md** - Deep technical details
4. 💻 **integration_example.py** - See actual code
5. 🎨 **streamlit_rewriter_demo.py** - Try interactive demo

---

## Summary Table

| Need          | Function                  | Time  | Effort    |
| ------------- | ------------------------- | ----- | --------- |
| Better plans  | `rewrite_for_planning()`  | 15sec | Easy      |
| Better search | `rewrite_for_search()`    | 15sec | Easy      |
| Complete opt. | `rewrite_full_pipeline()` | 30sec | Easy      |
| Interactive   | Streamlit Demo            | 2min  | Very Easy |
| Integration   | integration_example.py    | 5min  | Easy      |
| Customization | Edit prompts.py           | 10min | Medium    |

---

## 🎯 Start Here

1. **Try this NOW:**

    ```python
    from rewriter_agent import rewrite_for_planning
    result = rewrite_for_planning("What is machine learning?")
    print(result['rewritten_question'])
    ```

2. **Or try Streamlit:**

    ```bash
    streamlit run streamlit_rewriter_demo.py
    ```

3. **Then integrate into your code** using one of the patterns above

---

_Choose your scenario above and copy the code to get started immediately!_
