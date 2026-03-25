import json
from prompts import (
    BASAL_GENERATOR_PROMPT,
    GENERATOR_PROMPT,
    SCRUTINIZER_PROMPT,
    REFINER_PROMPT,
    FINAL_REFINER_PROMPT,
)


def safe_json_load(content, key):
    try:
        data = json.loads(content)
        return data.get(key, "")
    except:
        return ""


def build_concept(subtopic, scheduler):

    # 1️⃣ Basal
    prompt = BASAL_GENERATOR_PROMPT.format(word_limit=150)
    msg = scheduler.invoke([("system", prompt), ("human", subtopic)])
    baseline = safe_json_load(msg.content, "new_content")

    asked_questions = set()

    # 2️⃣ Iterative refinement
    for i in range(2):

        prompt = SCRUTINIZER_PROMPT.format(
            subtopic=subtopic,
            asked_questions=json.dumps(list(asked_questions)),
        )

        msg = scheduler.invoke([
            ("system", prompt),
            ("human", f"Explanation:\n{baseline}")
        ])

        try:
            questions = json.loads(msg.content)["questions"]
        except:
            questions = []

        questions = [q for q in questions if q not in asked_questions]
        asked_questions.update(questions)

        if not questions:
            break

        # Generate improvement
        prompt = GENERATOR_PROMPT.format(word_limit=200)
        msg = scheduler.invoke([
            ("system", prompt),
            ("human", f"{baseline}\n\nQuestions:\n{questions}")
        ])

        new_content = safe_json_load(msg.content, "new_content")

        # Refine
        prompt = REFINER_PROMPT.format(
            word_limit=300,
            topic=subtopic,
            baseline=baseline,
            new_content=new_content,
        )

        msg = scheduler.invoke([("system", prompt)])
        baseline = safe_json_load(msg.content, "refined_explanation")

    # 3️⃣ Final polish
    prompt = FINAL_REFINER_PROMPT.format(
        word_limit=600,
        topic=subtopic,
        explanation=baseline,
    )

    msg = scheduler.invoke([("system", prompt)])

    try:
        data = json.loads(msg.content)
        return {
            "subtopic": subtopic,
            "title": data.get("title", ""),
            "content": data.get("refined_explanation", ""),
        }
    except:
        return {
            "subtopic": subtopic,
            "title": "",
            "content": baseline,
        }
