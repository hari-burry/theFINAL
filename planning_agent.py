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

# Optional: Import rewriter agent for automatic question optimization
try:
    from rewriter_agent import rewrite_for_planning
    REWRITER_AVAILABLE = True
except ImportError:
    REWRITER_AVAILABLE = False

PLANNER_PROMPT =  '''You are a research planning agent.

Given a research topic, produce a concise, theory-only study plan that progresses
in a strictly logical sequence from fundamentals to advanced concepts.

Guidance:
- Phrase each subtopic so it explicitly references the main topic
  (e.g., "Virtual Memory: address translation" instead of just "Address translation").

Rules:
- Theory and conceptual understanding only
- No code, tools, frameworks, datasets, applications, deployment, or learning resources
- Produce exactly 5 subtopics that together cover both the full breadth and essential depth of the topic
- Avoid equations unless essential
- Total length under 200 words

Output:
- Valid JSON only
- Numeric string keys starting from "1"
- No introductions, conclusions, or extra text'''

def generate_plan(topic: str):
    messages = [
        ("system", PLANNER_PROMPT),
        ("human", "Generate a detailed research study plan on the topic: " + topic),
    ]

    response = scheduler.invoke(messages)
    return json.loads(response.content)


def generate_plan_with_rewriter(user_question: str, use_rewriter: bool = True):
    """
    Generate a research plan from a user question with optional automatic rewriting.
    
    This is the recommended function to use in your workflow. It:
    1. Optionally rewrites the question for clarity and planning focus
    2. Generates a focused 5-point study plan
    
    Args:
        user_question (str): Raw user question
        use_rewriter (bool): If True, optimize question before planning (default: True)
        
    Returns:
        dict: Contains plan and optional rewrite_info
    """
    rewrite_info = None
    topic_for_planning = user_question
    
    # Step 1: Optionally rewrite the question
    if use_rewriter and REWRITER_AVAILABLE:
        try:
            rewrite_result = rewrite_for_planning(user_question)
            topic_for_planning = rewrite_result['rewritten_question']
            rewrite_info = {
                'original_question': user_question,
                'rewritten_question': rewrite_result['rewritten_question'],
                'research_focus': rewrite_result.get('research_focus', '')
            }
        except Exception as e:
            print(f"Warning: Rewriter failed ({e}). Using original question.")
            topic_for_planning = user_question
    
    # Step 2: Generate plan with (possibly) rewritten topic
    plan = generate_plan(topic_for_planning)
    
    # Return both the plan and rewrite info for transparency
    return {
        'plan': plan,
        'plan_topic': topic_for_planning,
        'rewrite_info': rewrite_info,
        'was_rewritten': rewrite_info is not None
    }
