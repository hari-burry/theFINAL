# 🔬 Rewriter Agent Documentation

## Overview

The **Rewriter Agent** is a specialized component that optimizes user questions before they enter the research pipeline. It serves two critical functions:

1. **Planning Rewriter**: Optimizes questions for the planning process (conceptual clarity, bounded scope, research focus)
2. **Search Rewriter**: Generates specialized, high-quality search queries for news and arXiv

## Architecture

```
User Question
    ↓
[REWRITER AGENT]
    ├─→ Planning Rewriter (rewrite_for_planning)
    │   └─→ Output: Rewritten question, research focus
    │
    └─→ Search Rewriter (rewrite_for_search)
        └─→ Output: News queries, ArXiv queries, search rationale
    ↓
Planning Agent (uses rewritten question for plan generation)
    ↓
Search Agents (uses optimized queries for content fetching)
    ↓
Concept Engine (iterative explanation building)
    ↓
Final Response
```

## Module: `rewriter_agent.py`

### Functions

#### `rewrite_for_planning(question: str) -> dict`

Rewrites a user question to be optimal for the research planning process.

**Input:**

- `question` (str): Original user question

**Output:**

```json
{
	"original_question": "How do I get started with machine learning?",
	"rewritten_question": "Fundamental Concepts and Theoretical Foundations of Machine Learning",
	"research_focus": "Core mathematical and conceptual foundations of machine learning"
}
```

**What it does:**

- Clarifies the research topic
- Removes implementation details and tooling references
- Makes it suitable for generating a structured study plan
- Emphasizes conceptual understanding over practical steps

**Example:**

```python
from rewriter_agent import rewrite_for_planning

result = rewrite_for_planning("How does GPT work?")
print(result['rewritten_question'])
# Output: "Transformer Architecture and Attention Mechanisms in Large Language Models"
```

---

#### `rewrite_for_search(question: str) -> dict`

Generates optimized search queries specific to news and academic research sources.

**Input:**

- `question` (str): Original user question

**Output:**

```json
{
	"original_question": "What's happening with AI safety?",
	"news_queries": [
		"AI safety concerns 2024",
		"machine learning alignment research",
		"artificial intelligence ethics regulations"
	],
	"arxiv_queries": [
		"AI alignment methodology",
		"large language model safety evaluation",
		"adversarial robustness neural networks"
	],
	"search_rationale": "News queries focus on recent developments and policy..."
}
```

**What it does:**

- Generates 3 news queries focused on:
    - Recent developments and current events
    - Practical applications and industry news
    - Recent keywords and current terminology
- Generates 3 arXiv queries focused on:
    - Theoretical foundations and methodologies
    - Formal academic terminology
    - Research frameworks and analyses

**Example:**

```python
from rewriter_agent import rewrite_for_search

result = rewrite_for_search("Tell me about quantum computing")
for query in result['news_queries']:
    print(f"News: {query}")
for query in result['arxiv_queries']:
    print(f"ArXiv: {query}")
```

---

#### `rewrite_full_pipeline(question: str) -> dict`

Complete pipeline that performs both planning and search rewrites simultaneously.

**Input:**

- `question` (str): Original user question

**Output:**

```json
{
  "original_question": "How do neural networks learn?",
  "planning_rewrite": {...},
  "search_rewrite": {...},
  "recommended_plan_topic": "Neural Network Learning: Backpropagation and Optimization",
  "recommended_search_queries": {
    "news": ["neural network breakthroughs 2024", ...],
    "arxiv": ["gradient descent optimization", ...]
  }
}
```

**Example:**

```python
from rewriter_agent import rewrite_full_pipeline

result = rewrite_full_pipeline("What is reinforcement learning?")
print("Plan topic:", result['recommended_plan_topic'])
print("News queries:", result['recommended_search_queries']['news'])
```

---

## Integration Points

### 1. Direct Integration with Planning Agent

**Before (without rewriter):**

```python
from planning_agent import generate_plan

plan = generate_plan("How do I use machine learning?")
```

**After (with rewriter):**

```python
from rewriter_agent import rewrite_for_planning
from planning_agent import generate_plan

rewritten = rewrite_for_planning("How do I use machine learning?")
plan = generate_plan(rewritten['rewritten_question'])
```

### 2. Direct Integration with Search

**Before (without rewriter):**

```python
from mcp_client import fetch_news, fetch_arxiv

news = fetch_news("machine learning")
arxiv = fetch_arxiv("machine learning", max_results=5)
```

**After (with rewriter):**

```python
from rewriter_agent import rewrite_for_search
from mcp_client import fetch_news, fetch_arxiv

rewritten = rewrite_for_search("machine learning")
news = fetch_news(rewritten['news_queries'][0])
arxiv = fetch_arxiv(rewritten['arxiv_queries'][0], max_results=5)
```

### 3. Full Pipeline Integration

See `integration_example.py` for complete examples:

```python
from integration_example import research_pipeline_with_rewriter

result = research_pipeline_with_rewriter("Your research question here")
```

### 4. Streamlit Integration

```bash
streamlit run streamlit_rewriter_demo.py
```

Features:

- **Full Pipeline Mode**: Question → Rewrite → Plan → Search → Results
- **Search Only Mode**: Question → Optimize Queries → Fetch Results
- **Planning Only Mode**: Question → Rewrite → Generate Plan
- **Raw Rewriting Mode**: See the exact rewriting outputs in JSON format

---

## Usage Examples

### Example 1: Simple Planning Rewrite

```python
from rewriter_agent import rewrite_for_planning

question = "How can I build a chatbot?"

result = rewrite_for_planning(question)

print("Original:", result['original_question'])
print("Rewritten:", result['rewritten_question'])
print("Focus:", result['research_focus'])

# Output:
# Original: How can I build a chatbot?
# Rewritten: Natural Language Processing and Conversational AI Architectures
# Focus: Core concepts of NLP and conversational systems design
```

---

### Example 2: Optimized Search Queries

```python
from rewriter_agent import rewrite_for_search
from mcp_client import fetch_news, fetch_arxiv

question = "What's new in computer vision?"

result = rewrite_for_search(question)

print("News queries:")
for query in result['news_queries']:
    print(f"  - {query}")

print("\nArXiv queries:")
for query in result['arxiv_queries']:
    print(f"  - {query}")

# Fetch using optimized queries
news = fetch_news(result['news_queries'][0])
arxiv = fetch_arxiv(result['arxiv_queries'][0], max_results=5)
```

---

### Example 3: Full Research Pipeline

```python
from integration_example import research_pipeline_with_rewriter

question = "What is the relationship between physics and machine learning?"

result = research_pipeline_with_rewriter(question)

print("\n=== PIPELINE RESULT ===")
print("\nRecommended Plan Topic:")
print(result['recommended_plan_topic'])

print("\nResearch Plan:")
for key, value in result['research_plan'].items():
    print(f"  {key}. {value}")

print("\nSearch Queries Generated:")
print("News:", result['recommended_search_queries']['news'])
print("ArXiv:", result['recommended_search_queries']['arxiv'])
```

---

## Prompt Templates

The rewriter uses two main prompts defined in `prompts.py`:

### 1. PLANNER_QUESTION_REWRITER_PROMPT

Specializes in converting vague or practical questions into research-focused topics.

**Rules:**

- Clarifies core research topic
- Makes scope specific and bounded
- Emphasizes understanding (theory, concepts)
- Removes implementation details
- Suitable for study plan generation

### 2. NEWS_ARXIV_QUERY_REWRITER_PROMPT

Generates source-specific search queries.

**For News:**

- Uses recent keywords
- Focuses on practical applications
- Current events emphasis
- Multi-word queries

**For ArXiv:**

- Uses formal academic terminology
- Focuses on methodology and theory
- Technical keywords
- Research/survey terms

---

## Best Practices

### 1. Question Formulation for Better Rewrites

❌ **Vague:**

```
"Tell me about AI"
```

✅ **Better:**

```
"What are the fundamental concepts underlying neural networks?"
```

### 2. Using Mode Selection

- **Full Pipeline**: When you need comprehensive understanding (plans + sources)
- **Search Only**: Quick research to find recent developments
- **Planning Only**: Deep conceptual learning without news bias
- **Raw Rewriting**: Debug and understand the rewriting logic

### 3. Iterative Refinement

```python
from rewriter_agent import rewrite_for_planning
from planning_agent import generate_plan

question = "How do neural networks learn?"

# First iteration
rewrite1 = rewrite_for_planning(question)
plan1 = generate_plan(rewrite1['rewritten_question'])

# If plan is too broad, rewrite the rewritten question
rewrite2 = rewrite_for_planning(rewrite1['rewritten_question'])
plan2 = generate_plan(rewrite2['rewritten_question'])
```

### 4. Combining with Concept Engine

```python
from rewriter_agent import rewrite_for_planning
from planning_agent import generate_plan
# from concept_engine import build_understanding

question = "What is attention in transformers?"

rewritten = rewrite_for_planning(question)
plan = generate_plan(rewritten['rewritten_question'])

# Then feed to concept engine for iterative deepening
# understanding = build_understanding(plan)
```

---

## Performance Considerations

### API Calls

- `rewrite_for_planning()`: 1 LLM call
- `rewrite_for_search()`: 1 LLM call
- `rewrite_full_pipeline()`: 2 LLM calls (parallel)

### Token Usage

- Average per rewrite: ~300-500 tokens
- Prompts are optimized for efficiency

### Caching Strategy (Optional)

```python
from functools import lru_cache
from rewriter_agent import rewrite_for_planning

@lru_cache(maxsize=128)
def cached_plan_rewrite(question: str):
    return rewrite_for_planning(question)

# Subsequent calls with same question are instant
result1 = cached_plan_rewrite("What is NLP?")
result2 = cached_plan_rewrite("What is NLP?")  # Cached!
```

---

## Troubleshooting

### Issue: Rewritten question is still too vague

**Solution:** The original question might lack specificity. Try:

```python
# Instead of
rewrite_for_planning("Tell me about AI")

# Use
rewrite_for_planning("What are the mathematical foundations of deep learning?")
```

### Issue: Search queries return irrelevant results

**Solution:** Validate the search queries first:

```python
result = rewrite_for_search(question)
print("Queries:", result['news_queries'])
print("Rationale:", result['search_rationale'])

# Adjust if needed and retry
```

### Issue: LLM API errors

**Solution:** The rewriter uses `LLMScheduler` for load balancing. Check:

```python
# Verify API keys are set
import os
print(os.environ.get("GROQ_API_KEY"))
```

---

## Extension Ideas

1. **Multi-language Support**: Extend rewriter for multilingual questions
2. **Domain-Specific Rewriting**: Add specialized rewriters for specific domains
3. **Feedback Loop**: Learn from user feedback to improve rewrites
4. **Query Ranking**: Rank generated queries by predicted effectiveness
5. **Hybrid Rewriting**: Combine rule-based and LLM-based rewriting

---

## Summary

The Rewriter Agent is the strategic front-end of your research pipeline. By optimizing questions upfront, it ensures:

✅ Better research plans (more focused, bounded, conceptual)  
✅ More relevant search results (targeted queries, source-specific optimization)  
✅ Improved overall research quality (signals flow better through the pipeline)  
✅ Reduced wasted API calls (smarter queries from the start)

Use it as the **first step** in any research inquiry for maximum effectiveness.
