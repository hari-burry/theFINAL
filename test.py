import getpass
import os
from langchain_groq import ChatGroq
import re
import json as JSON

if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = getpass.getpass("Enter your Groq API key: ")

    
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
    (
        "system",
        '''You are a research planning agent.

The user will give a topic.
Your task is to produce a concise research study plan from fundamentals to advanced concepts.

Strict rules:
- Focus ONLY on conceptual understanding and theory.
- Do NOT include code, frameworks, libraries, tools, datasets, or implementation steps.
- Do NOT include applications or deployment.
- Do NOT include learning resources or roadmaps.
- Avoid equations unless absolutely necessary.
- Keep the total response under 200 words.

Output only the plan. No introductions, no conclusions, no extra commentary.Give them in a json with each plan indexed by numbers as keys starting from 1.
''',
    ),
    ("human", "Generate a detailes research study plan on the topic: " + input_prompt),
]
ai_msg = llm.invoke(messages)
resonse = JSON.loads(ai_msg.content)

for i in range (1, len(resonse)+1): 
    print("AI:", resonse[str(i)])

print(type(resonse))
print("usage:", ai_msg.usage_metadata)