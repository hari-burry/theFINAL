import os
import json
import base64
import tempfile
import requests
import streamlit as st
import streamlit.components.v1 as components
from langchain_groq import ChatGroq
from llm_scheduler import LLMScheduler
from planning_agent import generate_plan
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import requests

BASE_URL = "http://127.0.0.1:8000"

def fetch_mcp_context(query: str) -> str:
    try:
        news = requests.post(
            f"{BASE_URL}/news",
            json={"query": query, "max_results": 3},
            timeout=10
        ).json()["result"]

        papers = requests.post(
            f"{BASE_URL}/arxiv",
            json={"query": query, "max_results": 3},
            timeout=10
        ).json()["result"]

        return f"{news}\n\n{papers}"

    except Exception as e:
        return f"MCP fetch error: {e}"

# =======================
# API KEYS & SCHEDULER
# =======================

API_KEYS = [
    "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",
    "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",
    "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",
    "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"
]

GROQ_API_KEY = "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"
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

scheduler = LLMScheduler(API_KEYS)

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

Guidance:
- If questions are present, focus ONLY on resolving those gaps
- If no questions are present, deepen the explanation slightly

Rules:
- Theory only, intuitive and clear
- Do NOT repeat existing content
- Do NOT answer questions verbatim
- No tools, applications, or resources
- No code unless explicitly asked
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
- Ask for code if that particular concept can be better explained with it.

If no questions are needed, return:
{{
  "questions": []
}}

subtopic:
{subtopic}

Previously asked questions:
{asked_questions}

Output (JSON ONLY):
{{
  "questions": ["<question>"]
}}
"""

REFINER_PROMPT = """
You are a conceptual synthesis agent.

Task:
Merge the previous explanation with the newly generated content into a single,
lucid explanation that progresses from basic ideas to more advanced ones.

Rules:
- Preserve all important concepts
- Remove redundancy only
- Maintain logical flow
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
- Make it Pointwise only if possible
- Max {word_limit} words

Additionally:
Generate a short, concise title (3-6 words).
- It must capture the core concept.
- No punctuation.
- No generic words like "Introduction" or "Overview".
- Keep it compact and node-friendly.

Topic:
{topic}

Explanation:
{explanation}

Output (JSON ONLY):
{{
  "title": "<short title>",
  "refined_explanation": "<text>"
}}
"""

IMAGE_EXTRACT_PROMPT = """
You are an expert at reading academic and educational content from images.

Task:
Look at the provided image (which may be a textbook page, diagram, handwritten notes, or slide).
Extract the core research topic or concept being presented.

Return ONLY a clean, concise topic string (max 15 words) that can be used as input
to a concept-building system. Do not explain or elaborate.

Output (JSON ONLY):
{"topic": "<extracted topic>"}
"""

IMAGE_CONTEXT_PROMPT = """
You are an expert at reading academic and educational content from images.

Task:
Look at the provided image (which may be a textbook page, diagram, handwritten notes, or slide).
Extract and describe ALL conceptual content visible in the image.
This will be used as additional context to enrich a research explanation.

Be thorough - capture definitions, relationships, diagrams described, labels, formulas, and key ideas.

Output (JSON ONLY):
{"context": "<extracted content>"}
"""


# =======================
# CORE LLM FUNCTIONS
# =======================

def safe_json_load(content, key):
    try:
        data = json.loads(content)
        return data.get(key, "")
    except Exception:
        return ""

def generate_basal_explanation(subtopic, word_limit, extra_context=""):
    prompt = BASAL_GENERATOR_PROMPT.format(word_limit=word_limit)
    human_msg = subtopic
    if extra_context:
        human_msg += f"\n\nAdditional context from user-provided material:\n{extra_context}"
    msg = scheduler.invoke([("system", prompt), ("human", human_msg)])
    return safe_json_load(msg.content, "new_content")

def generate_new_content(subtopic, baseline, questions, word_limit):
    prompt = GENERATOR_PROMPT.format(word_limit=word_limit)
    msg = scheduler.invoke([
        ("system", prompt),
        ("human", f"Subtopic is: {subtopic}\n\n{baseline}\n\nQuestions:\n{questions}")
    ])
    return safe_json_load(msg.content, "new_content")

def scrutinize(subtopic, explanation, asked_questions):
    prompt = SCRUTINIZER_PROMPT.format(
        subtopic=subtopic,
        asked_questions=json.dumps(list(asked_questions))
    )
    msg = scheduler.invoke([
        ("system", prompt),
        ("human", f"Subtopic is: {subtopic}\n\nExplanation:\n{explanation}")
    ])
    try:
        questions = json.loads(msg.content)["questions"]
    except:
        return []
    return [q for q in questions if q not in asked_questions]

def refine(baseline, new_content, word_limit, subtopic):
    prompt = REFINER_PROMPT.format(
        word_limit=word_limit,
        topic=subtopic,
        baseline=baseline,
        new_content=new_content
    )
    msg = scheduler.invoke([("system", prompt)])
    return safe_json_load(msg.content, "refined_explanation")

def final_refine(explanation, subtopic, word_limit):
    prompt = FINAL_REFINER_PROMPT.format(
        word_limit=word_limit,
        topic=subtopic,
        explanation=explanation
    )
    msg = scheduler.invoke([("system", prompt)])
    try:
        data = json.loads(msg.content)
        return data.get("title", ""), data.get("refined_explanation", "")
    except:
        return "", ""


# =======================
# IMAGE PROCESSING
# =======================

def call_groq_vision(image_bytes, mime_type, prompt_text):
    """Call Groq vision API with llama-4-scout, rotating through all API keys."""
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{b64}"}
                    },
                    {
                        "type": "text",
                        "text": prompt_text
                    }
                ]
            }
        ],
        "max_tokens": 512
    }

    # Try every key in rotation until one works
    all_keys = API_KEYS + [GROQ_API_KEY]
    last_error = None
    for key in all_keys:
        try:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"All API keys failed for vision. Last error: {last_error}")

def extract_topic_from_image(image_bytes, mime_type):
    raw = call_groq_vision(image_bytes, mime_type, IMAGE_EXTRACT_PROMPT)
    try:
        return json.loads(raw).get("topic", "")
    except:
        return raw.strip()

def extract_context_from_image(image_bytes, mime_type):
    raw = call_groq_vision(image_bytes, mime_type, IMAGE_CONTEXT_PROMPT)
    try:
        return json.loads(raw).get("context", "")
    except:
        return raw.strip()


# =======================
# AUDIO PROCESSING
# =======================

def transcribe_audio(audio_bytes, filename, mime_type):
    """Transcribe audio using Groq Whisper large-v3, rotating through all API keys."""
    all_keys = API_KEYS + [GROQ_API_KEY]
    last_error = None
    for key in all_keys:
        try:
            files = {
                "file": (filename, audio_bytes, mime_type),
                "model": (None, "whisper-large-v3"),
                "response_format": (None, "json"),
            }
            response = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {key}"},
                files=files,
                timeout=120
            )
            response.raise_for_status()
            return response.json().get("text", "")
        except Exception as e:
            last_error = e
            continue
    raise RuntimeError(f"All API keys failed for audio. Last error: {last_error}")


# =======================
# VISUAL STATUS DISPLAY
# =======================

def show_processing_visual(phase: str, subtopic: str = "", iteration: int = 0):
    phase_config = {
        "planning": {
            "label": "MAPPING RESEARCH STRUCTURE",
            "sublabel": "Decomposing topic into knowledge nodes",
            "icon": "⬡",
            "color": "#a78bfa",
            "glow": "#7c3aed",
            "steps": ["Parsing topic", "Generating subtopic graph", "Ordering nodes"],
            "active": 0,
        },
        "basal": {
            "label": "SEEDING BASAL LAYER",
            "sublabel": f"Building foundational understanding · {subtopic[:40]}{'...' if len(subtopic) > 40 else ''}",
            "icon": "◈",
            "color": "#38bdf8",
            "glow": "#0284c7",
            "steps": ["Broad sweep", "Anchoring concepts", "Surface coverage"],
            "active": 0,
        },
        "scrutinize": {
            "label": f"SCRUTINIZING · PASS {iteration}",
            "sublabel": "Probing for conceptual blind spots",
            "icon": "◎",
            "color": "#fb923c",
            "glow": "#ea580c",
            "steps": ["Gap detection", "Question generation", "Filtering repeats"],
            "active": 1,
        },
        "generate": {
            "label": f"GENERATING · PASS {iteration}",
            "sublabel": "Synthesizing targeted content for gaps",
            "icon": "◆",
            "color": "#4ade80",
            "glow": "#16a34a",
            "steps": ["Targeting gaps", "Expanding theory", "Injecting depth"],
            "active": 1,
        },
        "refine": {
            "label": f"REFINING · PASS {iteration}",
            "sublabel": "Merging and restructuring knowledge",
            "icon": "◇",
            "color": "#f472b6",
            "glow": "#db2777",
            "steps": ["Merging layers", "Deduplication", "Flow alignment"],
            "active": 2,
        },
        "final": {
            "label": "FINAL POLISH",
            "sublabel": "Beginner-friendly synthesis + title generation",
            "icon": "✦",
            "color": "#fbbf24",
            "glow": "#d97706",
            "steps": ["Ordering concepts", "Simplifying prose", "Generating title"],
            "active": 2,
        },
        "image_analyze": {
            "label": "VISION ANALYSIS",
            "sublabel": "Reading image content via multimodal LLM",
            "icon": "◉",
            "color": "#818cf8",
            "glow": "#4f46e5",
            "steps": ["Encoding image", "Calling vision model", "Extracting concepts"],
            "active": 1,
        },
        "audio_transcribe": {
            "label": "AUDIO TRANSCRIPTION",
            "sublabel": "Running Whisper large-v3 on your recording",
            "icon": "◈",
            "color": "#34d399",
            "glow": "#059669",
            "steps": ["Decoding audio", "Whisper inference", "Parsing transcript"],
            "active": 1,
        },
        "mcp_fetch": {
            "label": "MCP CONTEXT FETCH",
            "sublabel": f"Pulling live news + arXiv papers · {subtopic[:38]}{'...' if len(subtopic) > 38 else ''}",
            "icon": "⬡",
            "color": "#f97316",
            "glow": "#c2410c",
            "steps": ["Querying news_search tool", "Querying arxiv_search tool", "Merging context"],
            "active": 1,
        },
    }

    cfg = phase_config.get(phase, phase_config["basal"])

    steps_html = ""
    for i, step in enumerate(cfg["steps"]):
        if i < cfg["active"]:
            dot_class, bar_width = "done", "100%"
        elif i == cfg["active"]:
            dot_class, bar_width = "active", "60%"
        else:
            dot_class, bar_width = "idle", "0%"

        steps_html += f"""
        <div class="step-row">
          <div class="step-dot {dot_class}"></div>
          <div class="step-info">
            <span class="step-label">{step}</span>
            <div class="step-bar-bg">
              <div class="step-bar" style="width:{bar_width}; background:{cfg['color']};"></div>
            </div>
          </div>
        </div>
        """

    html = f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');
      .proc-card {{
        font-family: 'DM Sans', sans-serif;
        background: #0a0a0a;
        border: 1px solid #1f1f1f;
        border-radius: 12px;
        padding: 22px 26px;
        margin: 8px 0 16px 0;
        position: relative;
        overflow: hidden;
        box-shadow: 0 0 40px {cfg['glow']}22;
      }}
      .proc-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, {cfg['color']}, transparent);
        animation: scanline 2s linear infinite;
      }}
      @keyframes scanline {{
        0% {{ transform: translateX(-100%); }}
        100% {{ transform: translateX(100%); }}
      }}
      .proc-header {{
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 16px;
      }}
      .proc-icon {{
        font-size: 28px;
        color: {cfg['color']};
        animation: pulse-icon 1.4s ease-in-out infinite;
        line-height: 1;
        filter: drop-shadow(0 0 8px {cfg['color']});
      }}
      @keyframes pulse-icon {{
        0%, 100% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.6; transform: scale(0.92); }}
      }}
      .proc-titles {{ flex: 1; }}
      .proc-label {{
        font-family: 'Space Mono', monospace;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.18em;
        color: {cfg['color']};
        margin-bottom: 3px;
        text-transform: uppercase;
      }}
      .proc-sublabel {{
        font-size: 13px;
        color: #6b7280;
        font-weight: 300;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 420px;
      }}
      .proc-badge {{
        font-family: 'Space Mono', monospace;
        font-size: 9px;
        color: {cfg['color']};
        border: 1px solid {cfg['color']}55;
        border-radius: 4px;
        padding: 3px 7px;
        letter-spacing: 0.1em;
        animation: badge-flicker 2.5s ease-in-out infinite;
      }}
      @keyframes badge-flicker {{
        0%, 90%, 100% {{ opacity: 1; }}
        95% {{ opacity: 0.4; }}
      }}
      .steps-container {{ display: flex; flex-direction: column; gap: 9px; }}
      .step-row {{ display: flex; align-items: center; gap: 10px; }}
      .step-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
      .step-dot.done {{ background: {cfg['color']}; box-shadow: 0 0 6px {cfg['color']}; }}
      .step-dot.active {{
        background: {cfg['color']};
        box-shadow: 0 0 10px {cfg['color']};
        animation: dot-pulse 0.8s ease-in-out infinite;
      }}
      .step-dot.idle {{ background: #2a2a2a; border: 1px solid #333; }}
      @keyframes dot-pulse {{
        0%, 100% {{ transform: scale(1); opacity: 1; }}
        50% {{ transform: scale(1.4); opacity: 0.6; }}
      }}
      .step-info {{ flex: 1; display: flex; flex-direction: column; gap: 4px; }}
      .step-label {{
        font-family: 'Space Mono', monospace;
        font-size: 10px;
        color: #9ca3af;
        letter-spacing: 0.06em;
      }}
      .step-bar-bg {{ height: 2px; background: #1f1f1f; border-radius: 2px; overflow: hidden; }}
      .step-bar {{ height: 100%; border-radius: 2px; transition: width 0.6s ease; box-shadow: 0 0 6px {cfg['color']}88; }}
      .proc-footer {{
        margin-top: 14px;
        padding-top: 12px;
        border-top: 1px solid #1a1a1a;
        display: flex;
        align-items: center;
        gap: 8px;
      }}
      .ticker {{
        font-family: 'Space Mono', monospace;
        font-size: 9px;
        color: #374151;
        letter-spacing: 0.08em;
        animation: ticker-scroll 3s linear infinite;
      }}
      @keyframes ticker-scroll {{
        0% {{ opacity: 0.3; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0.3; }}
      }}
      .live-dot {{
        width: 5px; height: 5px; border-radius: 50%;
        background: {cfg['color']};
        animation: dot-pulse 1s ease-in-out infinite;
        flex-shrink: 0;
      }}
    </style>
    <div class="proc-card">
      <div class="proc-header">
        <div class="proc-icon">{cfg['icon']}</div>
        <div class="proc-titles">
          <div class="proc-label">{cfg['label']}</div>
          <div class="proc-sublabel">{cfg['sublabel']}</div>
        </div>
        <div class="proc-badge">LIVE</div>
      </div>
      <div class="steps-container">{steps_html}</div>
      <div class="proc-footer">
        <div class="live-dot"></div>
        <span class="ticker">ITERATIVE CONCEPT BUILDER · PROCESSING · DO NOT INTERRUPT</span>
      </div>
    </div>
    """
    components.html(html, height=210, scrolling=False)


# =======================
# PDF EXPORT
# =======================

def generate_pdf(main_topic, plan, explanations):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(temp_file.name, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph(main_topic, styles["Heading1"]))
    elements.append(Spacer(1, 0.3 * inch))
    for key in sorted(plan.keys(), key=int):
        elements.append(Paragraph(f"{key}. {plan[key]}", styles["Heading2"]))
        elements.append(Spacer(1, 0.15 * inch))
        elements.append(Paragraph(explanations[key], styles["BodyText"]))
        elements.append(Spacer(1, 0.3 * inch))
    doc.build(elements)
    return temp_file.name


# =======================
# STREAMLIT PAGE CONFIG
# =======================

st.set_page_config(page_title="Concept Builder", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500&display=swap');

/* ── BASE APP BACKGROUND ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #0a0a0a !important;
    color: #e5e7eb !important;
}
[data-testid="stHeader"] {
    background-color: #0a0a0a !important;
    border-bottom: 1px solid #1a1a1a;
}
[data-testid="stSidebar"] {
    background-color: #0d0d0d !important;
    border-right: 1px solid #1a1a1a;
}
section.main > div {
    background-color: #0a0a0a !important;
}

/* ── TYPOGRAPHY ── */
h1, h2, h3, h4, h5, h6 {
    color: #f3f4f6 !important;
    font-family: 'Space Mono', monospace !important;
    letter-spacing: -0.01em;
}
h1 { font-size: 1.6rem !important; letter-spacing: 0.05em !important; }
p, li, span, label, div {
    color: #d1d5db;
    font-family: 'DM Sans', sans-serif;
}
.stCaption, [data-testid="stCaptionContainer"] {
    color: #4b5563 !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 11px !important;
}

/* ── TEXT INPUT ── */
input[type="text"], textarea {
    background-color: #111111 !important;
    color: #e5e7eb !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    padding: 0.6em 0.75em !important;
    font-size: 15px !important;
    font-family: 'DM Sans', sans-serif !important;
}
input[type="text"]:focus, textarea:focus {
    border-color: #a78bfa !important;
    box-shadow: 0 0 0 2px rgba(167, 139, 250, 0.15) !important;
    outline: none !important;
}
input::placeholder, textarea::placeholder {
    color: #374151 !important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    background-color: #111111 !important;
    border: 1px dashed #2a2a2a !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #a78bfa !important;
}
[data-testid="stFileUploaderDropzone"] {
    background-color: #111111 !important;
    color: #6b7280 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] * {
    color: #6b7280 !important;
}

/* ── BUTTON ── */
div.stButton > button {
    background-color: #111111 !important;
    color: #e5e7eb !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    padding: 0.6em 1.4em !important;
    font-size: 13px !important;
    font-family: 'Space Mono', monospace !important;
    letter-spacing: 0.08em !important;
    transition: all 0.15s ease !important;
}
div.stButton > button:hover {
    background-color: #a78bfa !important;
    color: #0a0a0a !important;
    border-color: #a78bfa !important;
}
div.stButton > button:active {
    background-color: #7c3aed !important;
    border-color: #7c3aed !important;
}

/* ── DOWNLOAD BUTTON ── */
[data-testid="stDownloadButton"] > button {
    background-color: #111111 !important;
    color: #e5e7eb !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 12px !important;
    letter-spacing: 0.06em !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background-color: #34d399 !important;
    color: #0a0a0a !important;
    border-color: #34d399 !important;
}

/* ── RADIO BUTTONS ── */
[data-testid="stRadio"] label {
    color: #9ca3af !important;
    font-size: 12px !important;
    font-family: 'Space Mono', monospace !important;
}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    font-size: 12px !important;
    color: #9ca3af !important;
}

/* ── SUCCESS / INFO / WARNING ALERTS ── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    border: 1px solid !important;
}
div[data-baseweb="notification"][kind="positive"],
.stSuccess {
    background-color: #052e16 !important;
    border-color: #166534 !important;
    color: #86efac !important;
}
.stInfo {
    background-color: #0c1a2e !important;
    border-color: #1e3a5f !important;
    color: #93c5fd !important;
}
.stWarning {
    background-color: #1c1007 !important;
    border-color: #78350f !important;
    color: #fcd34d !important;
}
.stError {
    background-color: #1c0606 !important;
    border-color: #7f1d1d !important;
    color: #fca5a5 !important;
}

/* ── CODE BLOCK ── */
[data-testid="stCode"], .stCodeBlock {
    background-color: #0d0d0d !important;
    border: 1px solid #1f1f1f !important;
    border-radius: 8px !important;
}
pre, code {
    background-color: #0d0d0d !important;
    color: #a78bfa !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 12px !important;
}

/* ── EXPANDER ── */
[data-testid="stExpander"] {
    background-color: #0f0f0f !important;
    border: 1px solid #1f1f1f !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    color: #9ca3af !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 12px !important;
}

/* ── SPINNER ── */
[data-testid="stSpinner"] {
    color: #a78bfa !important;
}

/* ── DIVIDER ── */
hr {
    border-color: #1f1f1f !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0a0a0a; }
::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #a78bfa; }

/* ── COLUMN LABELS ── */
.col-label {
    font-family: 'Space Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    padding-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.col-label-text  { color: #a78bfa; }
.col-label-image { color: #818cf8; }
.col-label-audio { color: #34d399; }

.badge-opt {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    color: #4b5563;
    border: 1px solid #2a2a2a;
    border-radius: 3px;
    padding: 1px 5px;
    letter-spacing: 0.07em;
}

/* ── COLUMN SEPARATORS ── */
[data-testid="stHorizontalBlock"] > div:not(:last-child) {
    border-right: 1px solid #1a1a1a;
    padding-right: 1.5rem;
}
[data-testid="stHorizontalBlock"] > div:not(:first-child) {
    padding-left: 1.5rem;
}
</style>
""", unsafe_allow_html=True)


# =======================
# HEADER
# =======================

st.title("ITERATIVE CONCEPT BUILDER")
st.caption("Basal understanding → gap detection → targeted refinement")
st.markdown("---")

# =======================
# 3-COLUMN INPUT AREA
# =======================

col_text, col_img, col_audio = st.columns([1.1, 1, 1], gap="medium")

# ── TEXT ─────────────────────────────────
with col_text:
    st.markdown('<div class="col-label col-label-text">⬡ &nbsp;Text Input</div>', unsafe_allow_html=True)
    main_topic = st.text_input(
        label="topic_text",
        label_visibility="collapsed",
        placeholder="e.g. Convolutional Neural Networks",
        key="subtopic_input"
    )
    st.caption("Type your research topic here.")

# ── IMAGE ─────────────────────────────────
with col_img:
    st.markdown('<div class="col-label col-label-image">◉ &nbsp;Image Input &nbsp;<span class="badge-opt">OPTIONAL</span></div>', unsafe_allow_html=True)

    uploaded_image = st.file_uploader(
        label="img",
        label_visibility="collapsed",
        type=["png", "jpg", "jpeg", "webp"],
        key="image_input",
        help="Textbook page, diagram, handwritten notes, slides"
    )
    if uploaded_image:
        st.image(uploaded_image, use_container_width=True)

    image_mode = st.radio(
        "Image use",
        options=["Extract topic from image", "Use as extra context", "Both"],
        index=2,
        key="image_mode",
        label_visibility="visible" if uploaded_image else "collapsed"
    )

# ── AUDIO ─────────────────────────────────
with col_audio:
    st.markdown('<div class="col-label col-label-audio">◈ &nbsp;Audio Input &nbsp;<span class="badge-opt">OPTIONAL</span></div>', unsafe_allow_html=True)

    uploaded_audio = st.file_uploader(
        label="audio",
        label_visibility="collapsed",
        type=["mp3", "wav", "m4a", "ogg", "flac", "webm"],
        key="audio_input",
        help="Voice note or recording describing your topic"
    )
    if uploaded_audio:
        st.audio(uploaded_audio)

    audio_mode = st.radio(
        "Audio use",
        options=["Use as topic (replace text)", "Use as extra context", "Both"],
        index=2,
        key="audio_mode",
        label_visibility="visible" if uploaded_audio else "collapsed"
    )

st.markdown("---")

# =======================
# GENERATE
# =======================

if st.button("Generate Research Tree"):

    final_topic   = main_topic.strip()
    extra_context = ""
    image_topic   = ""
    image_context = ""
    audio_topic   = ""
    audio_context = ""

    # ── Process image ───────────────────────────────
    if uploaded_image:
        uploaded_image.seek(0)
        image_bytes = uploaded_image.read()
        mime_type   = uploaded_image.type

        status_slot = st.empty()
        with status_slot:
            show_processing_visual("image_analyze")

        try:
            if image_mode in ("Extract topic from image", "Both"):
                image_topic = extract_topic_from_image(image_bytes, mime_type)

            if image_mode in ("Use as extra context", "Both"):
                image_context = extract_context_from_image(image_bytes, mime_type)
        except Exception as e:
            st.warning(f"Image processing error: {e}")

        status_slot.empty()

        if image_topic:
            st.info(f"📷 Topic from image: **{image_topic}**")
        if image_context:
            with st.expander("📷 Content extracted from image", expanded=False):
                st.write(image_context)

    # ── Process audio ───────────────────────────────
    if uploaded_audio:
        uploaded_audio.seek(0)
        audio_bytes = uploaded_audio.read()

        status_slot = st.empty()
        with status_slot:
            show_processing_visual("audio_transcribe")

        transcript = ""
        try:
            transcript = transcribe_audio(audio_bytes, uploaded_audio.name, uploaded_audio.type)
        except Exception as e:
            st.warning(f"Audio transcription error: {e}")

        status_slot.empty()

        if transcript:
            with st.expander("🎙 Audio transcript", expanded=False):
                st.write(transcript)

            if audio_mode in ("Use as topic (replace text)", "Both"):
                audio_topic = transcript.split(".")[0].strip()[:120]

            if audio_mode in ("Use as extra context", "Both"):
                audio_context = transcript

    # ── Merge topic sources ─────────────────────────
    # Priority: image topic > audio topic > typed text
    if image_mode in ("Extract topic from image", "Both") and image_topic:
        if audio_mode in ("Use as topic (replace text)", "Both") and audio_topic:
            final_topic = f"{image_topic}. Additional context: {audio_topic}"
        else:
            final_topic = image_topic
    elif audio_mode in ("Use as topic (replace text)", "Both") and audio_topic:
        final_topic = audio_topic

    if not final_topic:
        st.error("Please provide a topic via text, image, or audio input.")
        st.stop()

    # Merge extra context
    context_parts = []
    if image_context:
        context_parts.append(f"[From image]\n{image_context}")
    if audio_context:
        context_parts.append(f"[From audio notes]\n{audio_context}")
    extra_context = "\n\n".join(context_parts)

    st.markdown(f"**🔍 Research topic:** {final_topic}")
    if extra_context:
        st.caption("Extra context from image/audio will enrich the basal explanation.")

    st.markdown("---")

    # ── STEP 1 — Planning ───────────────────────────
    status_slot = st.empty()
    with status_slot:
        show_processing_visual("planning")

    plan = generate_plan(final_topic)
    status_slot.empty()

    st.success("Research plan generated")
    st.markdown("---")
    st.subheader("Research Plan")

    tree_lines = [final_topic]
    keys = sorted(plan.keys(), key=int)
    for i, key in enumerate(keys):
        prefix = "└── " if i == len(keys) - 1 else "├── "
        tree_lines.append(f"{prefix}{plan[key]}")
    st.code("\n".join(tree_lines), language="text")
    st.markdown("---")

    # ── STEP 2 — Subtopic loop ──────────────────────
    explanations = {}

    for key in sorted(plan.keys(), key=int):
        subtopic = plan[key]

        st.markdown("-----")
        st.header(f"{key}. {subtopic}")

        # ── MCP context fetch (news + arxiv) ──────────────
        status_slot = st.empty()
        with status_slot:
            show_processing_visual("mcp_fetch", subtopic=subtopic)
        mcp_context = fetch_mcp_context(subtopic)
        status_slot.empty()

        if mcp_context:
            with st.expander("⬡ Live context fetched (news + arXiv)", expanded=False):
                st.markdown(mcp_context)

        # Merge MCP context with image/audio extra_context
        combined_context = "".join(
            part for part in [extra_context, mcp_context] if part
        )

        # Basal (inject combined context)
        status_slot = st.empty()
        with status_slot:
            show_processing_visual("basal", subtopic=subtopic)
        baseline = generate_basal_explanation(subtopic, 150, extra_context=combined_context)
        status_slot.empty()

        st.subheader("Basal Explanation")
        st.write(baseline)

        asked_questions = set()
        gen_limits    = {1: 120, 2: 180}
        refine_limits = {1: 200, 2: 350}

        for i in range(1, 3):
            status_slot = st.empty()
            with status_slot:
                show_processing_visual("scrutinize", subtopic=subtopic, iteration=i)
            questions = scrutinize(subtopic, baseline, asked_questions)
            status_slot.empty()

            asked_questions.update(questions)
            if not questions:
                break

            status_slot = st.empty()
            with status_slot:
                show_processing_visual("generate", subtopic=subtopic, iteration=i)
            new_content = generate_new_content(subtopic, baseline, questions, gen_limits[i])
            status_slot.empty()

            status_slot = st.empty()
            with status_slot:
                show_processing_visual("refine", subtopic=subtopic, iteration=i)
            baseline = refine(baseline, new_content, refine_limits[i], subtopic)
            status_slot.empty()

        status_slot = st.empty()
        with status_slot:
            show_processing_visual("final", subtopic=subtopic)
        title, final_answer = final_refine(baseline, subtopic, 600)
        status_slot.empty()

        st.subheader(title)
        st.write(final_answer)
        explanations[key] = final_answer

    st.success("Full research tree generated.")

    pdf_path = generate_pdf(final_topic, plan, explanations)
    with open(pdf_path, "rb") as f:
        st.download_button(
            label="Export to PDF",
            data=f,
            file_name=f"{final_topic.replace(' ', '_')[:60]}.pdf",
            mime="application/pdf"
        )