import os
import json
from langchain_groq import ChatGroq
import streamlit as st

# =======================
# ENV
# =======================
os.environ["GROQ_API_KEY"] = "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"
if not os.environ.get("GROQ_API_KEY"):
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

BASAL_GENERATOR_PROMPT = """
You are a conceptual explanation agent.

Task:
Give a broad, shallow, end-to-end conceptual overview of the subtopic.
Cover the full breadth, not depth.

Rules:
- High-level theory only
- No deep dives
- No repetition
- No examples, tools, or applications
- Max {word_limit} words

Output (JSON ONLY):
{{
  "new_content": "<text>"
}}
"""

GENERATOR_PROMPT = """
You are a conceptual explanation agent.

Task:
Given the research subtopic, the current explanation, and any unresolved conceptual questions,
add new conceptual content that improves understanding by addressing missing foundations
or clarifying unclear ideas.

Cycle Information: Round {cycle} of 3
Expected Depth: {depth_level}

Guidance:
- If questions are present, focus ONLY on resolving those gaps
- If no questions are present, {depth_instruction}
- Each cycle should explore deeper layers of the topic

Rules:
- Theory only, intuitive and clear
- Do NOT repeat existing content
- Do NOT answer questions verbatim
- No code, tools, applications, or resources
- Avoid equations unless unavoidable
- Max {word_limit} words

Output (JSON ONLY):
{{
  "new_content": "<text>"
}}
"""

SCRUTINIZER_PROMPT = """
You are a strict research scrutinizer.

Task:
Decide whether the current explanation has conceptual gaps that block basic understanding.
If so, ask short, clear, fundamental questions.

Rules:
- Ask at most 3 questions
- Ask none if explanation is sufficient
- Do NOT repeat previously asked questions
- Do NOT suggest fixes

If no questions are needed, return:
{{
  "questions": []
}}

Previously asked questions:
{asked_questions}

Output (JSON ONLY):
{{
  "questions": ["<question>"]
}}
"""



DEEPER_GENERATOR_PROMPT = """
You are a deep conceptual exploration agent.

Task:
Explore the DEEPER THEORETICAL FOUNDATIONS of this topic.
Examine underlying principles, mechanisms, and relationships that weren't covered before.

Cycle Information: Round {cycle} of 3 (DEEPER CYCLE)
Depth Level: Advanced theoretical foundations

Focus Areas for Deepening:
{deeper_focus}

Guidance:
- Investigate WHY things work, not just WHAT they are
- Explore connections to foundational concepts
- Discuss trade-offs and implications
- Each deeper layer should add significant conceptual richness

Rules:
- Theory only, sophisticated and rigorous
- Do NOT repeat existing explanations
- Do NOT provide surface-level summaries
- No code, tools, applications, or resources
- Equations are acceptable when needed
- Max {word_limit} words

Output (JSON ONLY):
{{
  "new_content": "<text>"
}}
"""

DEPTH_VALIDATOR_PROMPT = """
You are a conceptual depth analyzer.

Task:
Analyze both explanations and assess whether the new one represents GENUINE DEEPER understanding.

Rules:
- Check if new content goes BEYOND surface-level extensions
- Verify theoretical depth increased
- Ensure no mere rephrasing occurred
- Rate depth improvement (%, 0=none, 100=deep advancement)

Previous explanation:
{baseline}

New content:
{new_content}

Output (JSON ONLY):
{{
  "depth_improvement_percent": <number 0-100>,
  "is_genuinely_deeper": <true/false>,
  "depth_analysis": "<brief analysis>",
  "recommendation": "<accept/deepen_further>"
}}
"""

REFINER_PROMPT = """
You are a conceptual synthesis agent.

Task:
Merge the previous explanation with the newly generated content into a single,
lucid explanation that progresses from basic ideas to more advanced ones.

Cycle Information: Round {cycle} of 3
Depth Strategy: {depth_strategy}

Rules:
- Preserve all important concepts
- Remove redundancy only
- Maintain logical flow (foundational → intermediate → advanced)
- Ensure depth progression
- No tools or applications
- Max {word_limit} words

Topic:
{topic}

Previous explanation:
{baseline}

New content:
{new_content}

Output (JSON ONLY):
{{
  "refined_explanation": "<text>"
}}
"""

FINAL_REFINER_PROMPT = """
You are a conceptual explanation agent.

Task:
Polish the explanation to be beginner-friendly.
- Keep all concepts
- Order from basic to advanced
- Use short sentences
- Add transitions
- Max {word_limit} words

Topic:
{topic}

Explanation:
{explanation}

Output (JSON ONLY):
{{
  "refined_explanation": "<text>"
}}
"""

# =======================
# FUNCTIONS
# =======================

def generate_basal_explanation(subtopic, word_limit):
    prompt = BASAL_GENERATOR_PROMPT.format(word_limit=word_limit)
    msg = llm.invoke([
        ("system", prompt),
        ("human", f"Subtopic:\n{subtopic}")
    ])
    return json.loads(msg.content)["new_content"]


def generate_new_content(subtopic, baseline, questions, word_limit, cycle=1):
    # Determine depth level and instructions based on cycle
    depth_levels = {
        1: "foundational concepts and basic relationships",
        2: "intermediate mechanisms and deeper relationships",
        3: "advanced theoretical foundations and complex interactions"
    }
    
    depth_instructions = {
        1: "deepen the explanation slightly with foundational concepts",
        2: "deepen significantly - explore mechanisms, relationships, and intermediate theory",
        3: "deepen substantially - investigate fundamental principles and complex interactions"
    }
    
    deeper_focus_areas = {
        1: "- Basic relationships and foundational principles",
        2: "- Mechanisms and intermediate-level relationships\n- How concepts interact\n- Underlying patterns",
        3: "- Fundamental principles driving the concepts\n- Complex relationships and trade-offs\n- Theoretical implications\n- Advanced interconnections"
    }
    
    prompt = GENERATOR_PROMPT.format(
        word_limit=word_limit,
        cycle=cycle,
        depth_level=depth_levels.get(cycle, "advanced"),
        depth_instruction=depth_instructions.get(cycle, "deepen the explanation")
    )
    
    msg = llm.invoke([
        ("system", prompt),
        ("human", f"""
Subtopic:
{subtopic}

Current explanation:
{baseline}

Unresolved questions:
{json.dumps(questions)}
""")
    ])
    return json.loads(msg.content)["new_content"]


def generate_deeper_content(subtopic, baseline, questions, word_limit, cycle=2):
    """Generate content with explicit deeper explanation focus."""
    deeper_focus_areas = {
        2: "- Underlying mechanisms\n- Relationships between concepts\n- Intermediate principles\n- System dynamics",
        3: "- Fundamental theoretical principles\n- Complex interdependencies\n- Trade-offs and constraints\n- Emergent properties\n- Theoretical implications"
    }
    
    prompt = DEEPER_GENERATOR_PROMPT.format(
        word_limit=word_limit,
        cycle=cycle,
        deeper_focus=deeper_focus_areas.get(cycle, "advanced theoretical exploration")
    )
    
    msg = llm.invoke([
        ("system", prompt),
        ("human", f"""
Subtopic:
{subtopic}

Current explanation:
{baseline}

Questions to address:
{json.dumps(questions)}
""")
    ])
    return json.loads(msg.content)["new_content"]


def validate_depth(baseline, new_content, cycle):
    """Validate that new content genuinely deepens understanding."""
    prompt = DEPTH_VALIDATOR_PROMPT.format(
        baseline=baseline,
        new_content=new_content
    )
    
    msg = llm.invoke([
        ("system", prompt),
        ("human", f"Cycle {cycle}: Validate depth improvement")
    ])
    
    return json.loads(msg.content)


def scrutinize(subtopic, explanation, asked_questions):
    prompt = SCRUTINIZER_PROMPT.format(
        asked_questions=json.dumps(list(asked_questions))
    )
    msg = llm.invoke([
        ("system", prompt),
        ("human", f"Explanation:\n{explanation}")
    ])
    questions = json.loads(msg.content)["questions"]
    return [q for q in questions if q not in asked_questions]


def refine(baseline, new_content, word_limit, subtopic, cycle=1):
    depth_strategies = {
        1: "Build foundational understanding first",
        2: "Expand with intermediate complexity",
        3: "Integrate advanced theoretical depth"
    }
    
    prompt = REFINER_PROMPT.format(
        word_limit=word_limit,
        topic=subtopic,
        baseline=baseline,
        new_content=new_content,
        cycle=cycle,
        depth_strategy=depth_strategies.get(cycle, "progressive deepening")
    )
    msg = llm.invoke([("system", prompt)])
    return json.loads(msg.content)["refined_explanation"]


def final_refine(explanation, subtopic, word_limit):
    prompt = FINAL_REFINER_PROMPT.format(
        word_limit=word_limit,
        topic=subtopic,
        explanation=explanation
    )
    msg = llm.invoke([("system", prompt)])
    return json.loads(msg.content)["refined_explanation"]

# =======================
# MAIN PIPELINE
# =======================

if __name__ == "__main__":
    subtopic = input("Enter subtopic: ")

    basal_limit = 150
    gen_limits = {1: 120, 2: 180, 3: 220}
    refine_limits = {1: 150, 2: 275, 3: 400}

    print("\n[INIT] Generating basal explanation...")
    baseline = generate_basal_explanation(subtopic, basal_limit)

    asked_questions = set()
    rounds = []

    for i in range(1, 4):
        print(f"\n=== ROUND {i} - DEPTH CYCLE ===")
        print("[Current Explanation]\n", baseline[:200] + "..." if len(baseline) > 200 else baseline)

        questions = scrutinize(subtopic, baseline, asked_questions)
        asked_questions.update(questions)

        if not questions and i > 1:
            print("[Scrutinizer] No gaps found at this level.")
        
        # Generate new content with cycle-aware depth
        if i == 1:
            new_content = generate_new_content(
                subtopic,
                baseline,
                questions,
                gen_limits[i],
                cycle=i
            )
            print(f"[Generator] Round {i}: Foundational deepening")
        else:
            # Deeper cycles use explicit deeper generation
            new_content = generate_deeper_content(
                subtopic,
                baseline,
                questions,
                gen_limits[i],
                cycle=i
            )
            print(f"[Generator] Round {i}: Advanced theoretical deepening")
        
        # Validate depth improvement
        print("[Validator] Checking depth improvement...")
        depth_check = validate_depth(baseline, new_content, i)
        print(f"  └─ Depth improvement: {depth_check['depth_improvement_percent']}%")
        print(f"  └─ Analysis: {depth_check['depth_analysis']}")
        
        # Ensure genuine depth - regenerate if needed
        if depth_check['depth_improvement_percent'] < 30 and i > 1:
            print(f"  └─ [WARNING] Depth improvement too low, regenerating with stronger focus...")
            new_content = generate_deeper_content(
                subtopic,
                baseline,
                questions,
                gen_limits[i] + 50,  # Allow more words for genuine deepening
                cycle=i
            )
            depth_check = validate_depth(baseline, new_content, i)
            print(f"  └─ Retried depth improvement: {depth_check['depth_improvement_percent']}%")

        print("[Generator] New content added.")

        baseline = refine(
            baseline,
            new_content,
            refine_limits[i],
            subtopic,
            cycle=i
        )

        print(f"[Refiner] Explanation refined - now at depth level {i}/3")

        rounds.append({
            "round": i,
            "questions": questions,
            "explanation": baseline,
            "depth_validation": {
                "improvement_percent": depth_check['depth_improvement_percent'],
                "is_deeper": depth_check['is_genuinely_deeper']
            }
        })


    print("\n" + "="*60)
    print("FINAL OUTPUT - PROGRESSIVE DEPTH EXPLANATION")
    print("="*60)
    
    final_answer = final_refine(baseline, subtopic, word_limit=600)
    
    print(f"\n📚 TOPIC: {subtopic}")
    print(f"✅ DEPTH CYCLES COMPLETED: {len(rounds)}/3")
    print(f"❓ QUESTIONS EXPLORED: {len(asked_questions)}")
    
    print("\n📊 DEPTH PROGRESSION:")
    total_improvement = 0
    for round_data in rounds:
        depth_val = round_data.get('depth_validation', {})
        improvement = depth_val.get('improvement_percent', 0)
        total_improvement += improvement
        print(f"  Round {round_data['round']}: +{improvement}% depth | Questions: {len(round_data['questions'])}")
    
    print(f"\n📈 TOTAL DEPTH IMPROVEMENT: {total_improvement}%")
    print("\n" + "-"*60)
    print("EXPLANATION:\n")
    print(final_answer)
    print("\n" + "="*60)

