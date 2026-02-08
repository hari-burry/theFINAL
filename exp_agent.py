import getpass
import os
from langchain_groq import ChatGroq
import re
import json as JSON

if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = "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"

    
input_prompt=input("give your Research topic: ")

llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0,
    max_tokens=None,
    reasoning_format="parsed",
    timeout=None,
    max_retries=2,
    
    
)

messages = [
    ("system",
        '''
        You are a conceptual explanation agent.

The user will give you:
- A single subtopic from a research study plan.

Your task:
- Explain the subtopic clearly and deeply, starting from first principles.
- Build intuition before introducing nuance.
- Progress from basic understanding to advanced theoretical insights.
- Clarify why the concept exists, what problem it addresses, and how it fits into the larger theory.

Strict rules:
- Focus ONLY on theory and conceptual understanding.
- Do NOT include code, algorithms, frameworks, libraries, tools, or implementation details.
- Do NOT include applications, use-cases, or deployment.
- Do NOT include learning resources, references, or roadmaps.
- Avoid equations unless absolutely unavoidable.
- Use precise, academic language but remain intuitive.
- Keep the explanation under 100 words.

Output only the explanation.
No introductions, no summaries, no meta commentary.
''',
    ),
    ("human", "Explain the following research subtopic in depth: " + input_prompt),
]
ai_msg = llm.invoke(messages)
print("AI:", ai_msg)