import os
import json
from langchain_groq import ChatGroq

# =======================
# ENV CHECK
# =======================
os.environ["GROQ_API_KEY"] = "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"
if "GROQ_API_KEY" not in os.environ:
    raise RuntimeError("GROQ_API_KEY not set")

# =======================
# LLM
# =======================

llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0,
    reasoning_format="parsed",
    max_retries=2,
)

# =======================
# PROMPTS
# =======================

GENERATOR_PROMPT = """
You are a conceptual explanation agent.

Task:
- Explain the given research subtopic.
- Theory only, Explain from first principles in a basic and intuitive way.

Constraints:
- Maximum 100 words.
- No code, tools, implementations, applications, or resources.
- No equations unless unavoidable.

Output (JSON ONLY):
{
  "explanation": "<text>"
}
"""

SCRUTINIZER_PROMPT = """
You are a strict research scrutinizer.

Task:
- Ask questions from the text to explain the concepts in a deeper and more basic way
- The intent is not to branch out to new topics, but to explore the given terms in the text in a more basic level to further understanding.

Rules:
- Ask at most 3 questions.
- Ask fewer if explanation is strong.
- Do NOT suggest fixes.

Output (JSON ONLY):
{
  "questions": [
    "<question>"
  ]
}
"""

REFINEMENT_PROMPT_TEMPLATE = """
You are the same explanation agent.

Task:
- You have to combine the previous explanation you gave with the new one to give a better understanding.
- Do not remove any important details from the previous explanation.Only remove redundant info.


Constraints:
- Maximum {word_limit} words.
- No code, tools, implementations, applications, or resources.
- Do NOT explicitly answer questions.

Output (JSON ONLY):
{{
  "refined_explanation": "<text>"
}}
"""


# =======================
# FUNCTIONS
# =======================

def generate_initial(subtopic):
    msg = llm.invoke([
        ("system", GENERATOR_PROMPT),
        ("human", subtopic)
    ])
    return json.loads(msg.content)["explanation"]


def scrutinize(subtopic, explanation):
    msg = llm.invoke([
        ("system", SCRUTINIZER_PROMPT),
        ("human", f"""
Subtopic:
{subtopic}

Explanation:
{explanation}
""")
    ])
    return json.loads(msg.content)["questions"]


def refine(subtopic, prev_explanation, questions, word_limit):
    refinement_prompt = REFINEMENT_PROMPT_TEMPLATE.format(
        word_limit=word_limit
    )

    msg = llm.invoke([
        ("system", refinement_prompt),
        ("human", f"""
Subtopic:
{subtopic}

Previous explanation:
{prev_explanation}

Critical questions:
{json.dumps(questions)}
""")
    ])
    return json.loads(msg.content)["refined_explanation"]

# =======================
# MAIN PIPELINE
# =======================

if __name__ == "__main__":
    subtopic = input("Enter subtopic: ")

    rounds = []

    explanation = generate_initial(subtopic)

    word_limits = {
        1: 100,
        2: 180,
        3: 250
    }

    for i in range(1, 4):
        questions = scrutinize(subtopic, explanation)

        round_data = {
            "round": i,
            "explanation": explanation,
            "questions": questions
        }

        if questions:
            explanation = refine(
                subtopic,
                explanation,
                questions,
                word_limits[i]
            )
            round_data["refined_explanation"] = explanation

        rounds.append(round_data)

    final_output = {
        "subtopic": subtopic,
        "rounds": rounds,
        "final_refined_answer": explanation
    }

    print(json.dumps(final_output, indent=2))

