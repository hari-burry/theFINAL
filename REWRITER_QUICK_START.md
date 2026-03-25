# 🚀 Rewriter Agent - Quick Start Guide

## Installation & Setup

The rewriter agent uses the same dependencies as your existing system (Groq API, LangChain). No additional installation needed!

## 5-Minute Quick Start

### 1. Test the Rewriter Agent Directly

**Python Script:**

```python
from rewriter_agent import rewrite_full_pipeline

# Your question
question = "What is machine learning?"

# Run the rewriter
result = rewrite_full_pipeline(question)

# View the results
print("Original Question:", result['original_question'])
print("\nRewritten for Planning:", result['recommended_plan_topic'])
print("\nNews Search Queries:")
for q in result['recommended_search_queries']['news']:
    print(f"  • {q}")
print("\nArXiv Search Queries:")
for q in result['recommended_search_queries']['arxiv']:
    print(f"  • {q}")
```

**Run it:**

```bash
cd c:\Users\hari\OneDrive\Desktop\trying
python -c "
from rewriter_agent import rewrite_full_pipeline
result = rewrite_full_pipeline('What is reinforcement learning?')
import json
print(json.dumps(result, indent=2))
"
```

---

### 2. Use the Streamlit Demo

**Start the app:**

```bash
cd c:\Users\hari\OneDrive\Desktop\trying
streamlit run streamlit_rewriter_demo.py
```

**Then:**

1. Open browser to `http://localhost:8501`
2. Enter your research question
3. Choose a mode (Full Pipeline, Search Only, Planning Only, Raw Rewriting)
4. Click "Process Question"
5. Watch the rewriting and planning in action!

---

### 3. Test Different Modes

#### Mode 1: Full Pipeline (Complete Research Flow)

```bash
python -c "
from integration_example import research_pipeline_with_rewriter
result = research_pipeline_with_rewriter('Tell me about quantum computing')
"
```

#### Mode 2: Search Only (Just Optimize Search Queries)

```bash
python -c "
from rewriter_agent import rewrite_for_search
import json
result = rewrite_for_search('What are transformers?')
print('News queries:', json.dumps(result['news_queries'], indent=2))
print('ArXiv queries:', json.dumps(result['arxiv_queries'], indent=2))
"
```

#### Mode 3: Planning Only (Just Optimize for Planning)

```bash
python -c "
from rewriter_agent import rewrite_for_planning
from planning_agent import generate_plan
import json

result = rewrite_for_planning('How do neural networks work?')
print('Rewritten:', result['rewritten_question'])

plan = generate_plan(result['rewritten_question'])
print('Plan:', json.dumps(plan, indent=2))
"
```

---

## Key Functions Reference

### `rewrite_for_planning(question: str)`

Optimizes question for the planning process.

```python
from rewriter_agent import rewrite_for_planning

result = rewrite_for_planning("How do I use machine learning?")
# Returns: original_question, rewritten_question, research_focus
```

### `rewrite_for_search(question: str)`

Generates optimized search queries for news and arXiv.

```python
from rewriter_agent import rewrite_for_search

result = rewrite_for_search("Tell me about AI safety")
# Returns: news_queries, arxiv_queries, search_rationale
```

### `rewrite_full_pipeline(question: str)`

Does both at once.

```python
from rewriter_agent import rewrite_full_pipeline

result = rewrite_full_pipeline("What is NLP?")
# Returns: planning_rewrite + search_rewrite + recommendations
```

---

## Test Cases

Try these example questions to see how the rewriter optimizes them:

### Technical Questions

- "What is a neural network?"
- "How do transformers work?"
- "Explain backpropagation"
- "What is the attention mechanism?"

### Practical Questions

- "How do I build a chatbot?"
- "How can I get started with machine learning?"
- "What tools should I use for deep learning?"

### Current Events

- "What's new in AI?"
- "Tell me about recent developments in quantum computing"
- "What's happening with AI safety?"

### Broad Topics

- "What is artificial intelligence?"
- "Tell me about data science"
- "What is computer vision?"

---

## Expected Outputs

### Good Rewrite Example

**Original:** "How do I use machine learning?"

**Rewritten for Planning:** "Fundamental Algorithms and Methodologies in Machine Learning"

**News Queries:**

- "machine learning industry applications 2024"
- "AI breakthroughs and new models"
- "enterprise machine learning deployment trends"

**ArXiv Queries:**

- "machine learning algorithms survey"
- "supervised learning methodologies"
- "neural network optimization techniques"

---

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'rewriter_agent'"

**Solution:** Make sure you're in the correct directory:

```bash
cd c:\Users\hari\OneDrive\Desktop\trying
```

### Issue: "GROQ_API_KEY not set"

**Solution:** The rewriter uses the same API keys as your planning agent. Verify one is set:

```bash
python -c "import os; print('API Key:', os.environ.get('GROQ_API_KEY', 'NOT SET'))"
```

### Issue: "JSON parsing error"

**Solution:** The LLM might be returning malformed JSON. Retry - it usually works on second attempt:

```python
try:
    result = rewrite_for_planning(question)
except:
    result = rewrite_for_planning(question)  # Retry
```

---

## Next Steps

1. **Try the Streamlit demo** for a visual experience
2. **Read REWRITER_AGENT_DOCS.md** for detailed documentation
3. **Check integration_example.py** for code examples
4. **Integrate into your pipeline** using the patterns shown

---

## Integration Into Existing Code

### Option 1: Add to Planning Agent

```python
# In planning_agent.py or your main script
from rewriter_agent import rewrite_for_planning
from planning_agent import generate_plan

def enhanced_planning(user_question: str):
    # Rewrite first
    rewritten = rewrite_for_planning(user_question)

    # Then plan
    plan = generate_plan(rewritten['rewritten_question'])

    return {
        "original": user_question,
        "rewritten": rewritten['rewritten_question'],
        "plan": plan
    }
```

### Option 2: Add to Research Agent

```python
# In streamlit_researchagent.py
from rewriter_agent import rewrite_for_search

# Before fetching, optimize the query
if user_input:
    rewrite_result = rewrite_for_search(user_input)

    # Use optimized queries
    news = fetch_news(rewrite_result['news_queries'][0])
    arxiv = fetch_arxiv(rewrite_result['arxiv_queries'][0])
```

### Option 3: Add to Multi-Agent System

```python
# In multi_agent.py or orchestrator
from rewriter_agent import rewrite_full_pipeline

def orchestrate_research(user_question: str):
    # Step 1: Rewrite
    rewritten = rewrite_full_pipeline(user_question)

    # Step 2: Plan
    plan = generate_plan(rewritten['recommended_plan_topic'])

    # Step 3: Search with optimized queries
    news = fetch_news(rewritten['recommended_search_queries']['news'][0])

    # ... etc
```

---

## Performance Tips

1. **Cache results for repeated questions:**

    ```python
    from functools import lru_cache
    from rewriter_agent import rewrite_for_planning

    @lru_cache(maxsize=100)
    def cached_rewrite(q):
        return rewrite_for_planning(q)
    ```

2. **Batch multiple rewrites:**

    ```python
    questions = ["Q1", "Q2", "Q3"]
    results = [rewrite_for_planning(q) for q in questions]
    ```

3. **Use just planning or just search depending on need:**
    - Don't call `rewrite_full_pipeline` if you only need search optimization
    - Save API calls!

---

## What to Do Next

✅ Run the quick start examples above  
✅ Try the Streamlit demo  
✅ Read the full documentation  
✅ Integrate into your main application  
✅ Customize prompts in `prompts.py` for your domain

---

**Need help?** Check REWRITER_AGENT_DOCS.md for detailed API reference and advanced usage.
