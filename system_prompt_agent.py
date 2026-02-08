from langchain_groq import ChatGroq
import json as JSON

persona_llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0,
    reasoning_format="parsed"
)

def generate_expert_system_prompt(topic: str) -> str:
    messages = [
        ("system", "You are an expert prompt engineer."),
        ("human", f"""
Create a SYSTEM PROMPT that defines the ideal expert to write a world-class
research study on the topic: "{topic}"

The system prompt must:
- Clearly define expertise, background, and domain authority
- Specify research methodology expectations
- Enforce academic rigor, citations, and structure
- Be concise but powerful

Return ONLY the system prompt as plain text.
""")
    ]

    response = persona_llm.invoke(messages)
    return response.content.strip()

research_llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0,
    reasoning_format="parsed"
)

def generate_research_plan(topic: str, system_prompt: str):
    messages = [
        ("system", system_prompt),
        ("human", f"Generate a detailed research study plan on the topic: {topic}")
    ]

    ai_msg = research_llm.invoke(messages)
    return JSON.loads(ai_msg.content)

input_prompt = input("Give your research topic: ")

# 1. Generate expert persona
system_prompt = generate_expert_system_prompt(input_prompt)
print("\n===== GENERATED SYSTEM PROMPT =====\n")
print(system_prompt)

# 2. Generate research plan
response = generate_research_plan(input_prompt, system_prompt)

print("\n===== RESEARCH PLAN =====\n")
for i in range(1, len(response) + 1):
    print(f"AI {i}:", response[str(i)])
