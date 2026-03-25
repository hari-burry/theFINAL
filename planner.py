import json
from llm_scheduler import LLMScheduler
from prompts import PLANNER_PROMPT
from concept_engine import build_concept

API_KEYS = [
        "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",
    "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",
    "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"
]
    

scheduler = LLMScheduler(API_KEYS)

topic = input("Enter research topic: ")

# 1️⃣ Generate Plan
messages = [
    ("system", PLANNER_PROMPT),
    ("human", f"Generate plan for topic: {topic}")
]

response = scheduler.invoke(messages)
plan = json.loads(response.content)

print("\n===== STUDY PLAN =====")
for i in range(1, 6):
    print(plan[str(i)])

# 2️⃣ Build Concepts
print("\n===== BUILDING FULL RESEARCH =====")

research_output = []

for i in range(1, 6):
    subtopic = plan[str(i)]
    print(f"\nProcessing: {subtopic}\n")

    result = build_concept(subtopic, scheduler)
    research_output.append(result)

    print("TITLE:", result["title"])
    print(result["content"])

# 3️⃣ Final Usage Report
scheduler.print_usage_report()
