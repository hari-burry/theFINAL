import os
import json
from dotenv import load_dotenv
import base64
import streamlit as st
from langchain_groq import ChatGroq
from utils import safe_json_loads, extract_json_value, standardize_llm_output, validate_llm_response, AGENT_SCHEMAS, robust_llm_call


load_dotenv()

if "GROQ_API_KEY" not in os.environ:
   os.environ["GROQ_API_KEY"] = "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"
else:
    os.environ["GROQ_API_KEY"] = "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"
    print("exists")

# =======================
# PAGE CONFIG
# =======================
st.set_page_config(
    page_title="Deep Research Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =======================
# SESSION STATE INIT (must happen before any rendering)
# =======================
for key, default in [
    ("result", None),
    ("rounds_data", []),
    ("asked_questions_list", []),
    ("topic_used", ""),
    ("dark_mode", True),          # ← NEW: theme state
]:
    if key not in st.session_state:
        st.session_state[key] = default

# =======================
# THEME DEFINITIONS
# =======================
DARK_THEME = {
    "bg":               "#020409",
    "bg2":              "rgba(255,255,255,0.02)",
    "bg3":              "rgba(255,255,255,0.03)",
    "bg_final":         "rgba(0,245,196,0.03)",
    "border":           "rgba(0,245,196,0.1)",
    "border_soft":      "rgba(255,255,255,0.06)",
    "border_final":     "rgba(0,245,196,0.15)",
    "text_primary":     "#e2e8f0",
    "text_secondary":   "#94a3b8",
    "text_muted":       "#64748b",
    "text_very_muted":  "#475569",
    "text_final":       "#cbd5e1",
    "accent":           "#00f5c4",
    "accent2":          "#7c3aed",
    "accent2_light":    "#a78bfa",
    "accent_bg":        "rgba(0,245,196,0.08)",
    "accent2_bg":       "rgba(124,58,237,0.08)",
    "accent2_border":   "rgba(124,58,237,0.3)",
    "grid_line":        "rgba(0,245,196,0.03)",
    "scrollbar":        "rgba(0,245,196,0.2)",
    "input_bg":         "rgba(255,255,255,0.03)",
    "input_border":     "rgba(0,245,196,0.2)",
    "input_border_focus":"rgba(0,245,196,0.6)",
    "input_shadow":     "rgba(0,245,196,0.1)",
    "stat_bg":          "rgba(255,255,255,0.03)",
    "stat_border":      "rgba(255,255,255,0.07)",
    "card_idle_border": "rgba(255,255,255,0.06)",
    "card_active_border":"rgba(0,245,196,0.2)",
    "card_done_border": "rgba(124,58,237,0.15)",
    "card_active_shadow":"rgba(0,245,196,0.06)",
    "card_done_shadow":  "rgba(124,58,237,0.05)",
    "depth_bg":         "rgba(255,255,255,0.04)",
    "btn_color":        "#020409",
    "tab_active_bg":    "rgba(0,245,196,0.08)",
    "hero_gradient":    "linear-gradient(135deg, #ffffff 0%, #00f5c4 50%, #7c3aed 100%)",
    "toggle_icon":      "☀️",
    "toggle_label":     "Light Mode",
    "radial_bg":        "radial-gradient(ellipse at top left, rgba(0,245,196,0.04) 0%, transparent 60%)",
}

LIGHT_THEME = {
    "bg":               "#f0f4f8",
    "bg2":              "rgba(0,0,0,0.02)",
    "bg3":              "rgba(0,0,0,0.03)",
    "bg_final":         "rgba(0,180,140,0.04)",
    "border":           "rgba(0,160,120,0.2)",
    "border_soft":      "rgba(0,0,0,0.08)",
    "border_final":     "rgba(0,160,120,0.25)",
    "text_primary":     "#0f172a",
    "text_secondary":   "#334155",
    "text_muted":       "#64748b",
    "text_very_muted":  "#94a3b8",
    "text_final":       "#1e293b",
    "accent":           "#059669",
    "accent2":          "#6d28d9",
    "accent2_light":    "#7c3aed",
    "accent_bg":        "rgba(5,150,105,0.08)",
    "accent2_bg":       "rgba(109,40,217,0.06)",
    "accent2_border":   "rgba(109,40,217,0.25)",
    "grid_line":        "rgba(5,150,105,0.04)",
    "scrollbar":        "rgba(5,150,105,0.3)",
    "input_bg":         "rgba(255,255,255,0.8)",
    "input_border":     "rgba(5,150,105,0.3)",
    "input_border_focus":"rgba(5,150,105,0.7)",
    "input_shadow":     "rgba(5,150,105,0.12)",
    "stat_bg":          "rgba(255,255,255,0.7)",
    "stat_border":      "rgba(0,0,0,0.08)",
    "card_idle_border": "rgba(0,0,0,0.07)",
    "card_active_border":"rgba(5,150,105,0.3)",
    "card_done_border": "rgba(109,40,217,0.2)",
    "card_active_shadow":"rgba(5,150,105,0.08)",
    "card_done_shadow":  "rgba(109,40,217,0.06)",
    "depth_bg":         "rgba(0,0,0,0.06)",
    "btn_color":        "#ffffff",
    "tab_active_bg":    "rgba(5,150,105,0.1)",
    "hero_gradient":    "linear-gradient(135deg, #0f172a 0%, #059669 50%, #6d28d9 100%)",
    "toggle_icon":      "🌙",
    "toggle_label":     "Dark Mode",
    "radial_bg":        "radial-gradient(ellipse at top left, rgba(5,150,105,0.06) 0%, transparent 60%)",
}

def get_theme():
    return DARK_THEME if st.session_state.dark_mode else LIGHT_THEME

# =======================
# CSS GENERATOR (theme-aware)
# =======================
def build_css(t):
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body, .stApp {{
    background: {t['bg']} !important;
    color: {t['text_primary']} !important;
    font-family: 'Syne', sans-serif !important;
    transition: background 0.35s ease, color 0.35s ease;
}}

#MainMenu, footer, header {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}
section[data-testid="stSidebar"] {{ display: none; }}
.block-container {{ padding: 2rem 3rem !important; max-width: 1400px !important; }}

/* ── THEME TOGGLE BUTTON ── */
.theme-toggle-wrap {{
    display: flex; justify-content: flex-end; padding: 0.5rem 0 0;
}}
.theme-toggle-btn {{
    display: inline-flex; align-items: center; gap: 0.5rem;
    background: {t['bg2']}; border: 1px solid {t['border']};
    border-radius: 50px; padding: 0.4rem 1rem; cursor: pointer;
    font-family: 'Space Mono', monospace; font-size: 0.6rem;
    letter-spacing: 0.15em; color: {t['accent']}; text-transform: uppercase;
    transition: all 0.3s ease;
}}
.theme-toggle-btn:hover {{
    background: {t['accent_bg']};
    box-shadow: 0 0 16px {t['input_shadow']};
}}
.theme-toggle-icon {{ font-size: 0.9rem; }}

/* ── HERO ── */
.hero {{ text-align: center; padding: 3rem 0 2rem; position: relative; }}
.hero-eyebrow {{
    font-family: 'Space Mono', monospace; font-size: 0.7rem;
    letter-spacing: 0.3em; color: {t['accent']}; text-transform: uppercase;
    margin-bottom: 1rem; opacity: 0.8;
}}
.hero-title {{
    font-family: 'Syne', sans-serif; font-size: clamp(2.5rem, 6vw, 5rem);
    font-weight: 800; line-height: 1;
    background: {t['hero_gradient']};
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 0.5rem;
    transition: background 0.35s ease;
}}
.hero-sub {{
    font-family: 'Space Mono', monospace; font-size: 0.75rem;
    color: {t['text_muted']}; letter-spacing: 0.1em;
}}

/* ── GRID BACKGROUND ── */
.stApp::before {{
    content: ''; position: fixed; inset: 0;
    background-image:
        linear-gradient({t['grid_line']} 1px, transparent 1px),
        linear-gradient(90deg, {t['grid_line']} 1px, transparent 1px);
    background-size: 60px 60px; pointer-events: none; z-index: 0;
    transition: background-image 0.35s ease;
}}

/* ── PIPELINE ── */
.pipeline-container {{
    background: {t['bg2']};
    border: 1px solid {t['border']};
    border-radius: 16px; padding: 2rem; margin: 2rem 0;
    position: relative; overflow: hidden;
    transition: background 0.35s ease, border-color 0.35s ease;
}}
.pipeline-container::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, {t['accent']}, transparent);
}}
.pipeline-title {{
    font-family: 'Space Mono', monospace; font-size: 0.65rem;
    letter-spacing: 0.25em; color: {t['accent']}; text-transform: uppercase;
    margin-bottom: 1.5rem; opacity: 0.7;
}}
.agents-row {{
    display: flex; align-items: center; justify-content: space-between;
    gap: 0.5rem; flex-wrap: wrap;
}}
.agent-node {{
    display: flex; flex-direction: column; align-items: center;
    gap: 0.5rem; flex: 1; min-width: 100px;
}}
.agent-icon-wrap {{
    width: 60px; height: 60px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem; position: relative; transition: all 0.4s ease;
    border: 2px solid transparent; background: {t['bg3']};
}}
.agent-icon-wrap.idle {{ border-color: {t['text_very_muted']}; box-shadow: none; }}
.agent-icon-wrap.active {{
    border-color: {t['accent']};
    box-shadow: 0 0 20px {t['input_shadow']}, 0 0 40px {t['accent_bg']}, inset 0 0 20px {t['accent_bg']};
    animation: pulse-glow 1.5s ease-in-out infinite;
}}
.agent-icon-wrap.done {{
    border-color: {t['accent2']};
    box-shadow: 0 0 15px {t['accent2_bg']};
    background: {t['accent2_bg']};
}}
@keyframes pulse-glow {{
    0%, 100% {{ box-shadow: 0 0 20px {t['input_shadow']}, 0 0 40px {t['accent_bg']}; }}
    50% {{ box-shadow: 0 0 30px {t['input_shadow']}, 0 0 60px {t['accent_bg']}; }}
}}
.agent-label {{
    font-family: 'Space Mono', monospace; font-size: 0.6rem;
    color: {t['text_muted']}; text-align: center; letter-spacing: 0.05em; text-transform: uppercase;
}}
.agent-label.active {{ color: {t['accent']}; }}
.agent-label.done   {{ color: {t['accent2_light']}; }}

/* ── ARROWS ── */
.arrow-connector {{
    flex: 0 0 auto; display: flex; align-items: center;
    color: {t['text_very_muted']}; font-size: 1.2rem; transition: color 0.4s ease;
}}
.arrow-connector.flow-active {{ color: {t['accent']}; animation: flow 0.8s ease-in-out infinite; }}
.arrow-connector.flow-done   {{ color: {t['accent2']}; }}
@keyframes flow {{
    0%   {{ opacity: 0.3; transform: translateX(-3px); }}
    50%  {{ opacity: 1;   transform: translateX(3px); }}
    100% {{ opacity: 0.3; transform: translateX(-3px); }}
}}

/* ── LOOP BADGE ── */
.loop-badge {{
    background: {t['accent2_bg']}; border: 1px solid {t['accent2_border']};
    border-radius: 20px; padding: 0.2rem 0.7rem;
    font-family: 'Space Mono', monospace; font-size: 0.6rem;
    color: {t['accent2_light']}; letter-spacing: 0.1em; text-align: center; margin-top: 0.5rem;
}}

/* ── ITERATION DOTS ── */
.iter-row {{ display: flex; gap: 0.75rem; margin-top: 1.5rem; justify-content: center; }}
.iter-dot {{
    width: 10px; height: 10px; border-radius: 50%;
    background: {t['bg3']}; border: 1px solid {t['text_very_muted']};
    transition: all 0.4s ease;
}}
.iter-dot.active {{
    background: {t['accent']}; border-color: {t['accent']};
    box-shadow: 0 0 8px {t['input_shadow']}; animation: pulse-glow 1s infinite;
}}
.iter-dot.done {{ background: {t['accent2']}; border-color: {t['accent2_light']}; box-shadow: 0 0 6px {t['accent2_bg']}; }}

/* ── AGENT OUTPUT CARDS ── */
.output-grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem; margin: 1.5rem 0;
}}
.agent-card {{
    background: {t['bg2']}; border: 1px solid {t['card_idle_border']};
    border-radius: 12px; padding: 1.25rem; transition: all 0.4s ease;
    position: relative; overflow: hidden; min-height: 140px;
}}
.agent-card::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: {t['card_idle_border']}; transition: background 0.4s ease;
}}
.agent-card.active::before {{ background: linear-gradient(90deg, transparent, {t['accent']}, transparent); }}
.agent-card.done::before   {{ background: linear-gradient(90deg, transparent, {t['accent2']}, transparent); }}
.agent-card.active {{ border-color: {t['card_active_border']}; box-shadow: 0 4px 30px {t['card_active_shadow']}; }}
.agent-card.done   {{ border-color: {t['card_done_border']}; box-shadow: 0 4px 20px {t['card_done_shadow']}; }}
.card-header {{ display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }}
.card-icon   {{ font-size: 1rem; }}
.card-title  {{
    font-family: 'Space Mono', monospace; font-size: 0.65rem;
    letter-spacing: 0.15em; color: {t['text_muted']}; text-transform: uppercase;
}}
.card-title.active {{ color: {t['accent']}; }}
.card-title.done   {{ color: {t['accent2_light']}; }}
.card-status {{ margin-left: auto; width: 6px; height: 6px; border-radius: 50%; background: {t['text_very_muted']}; }}
.card-status.active {{ background: {t['accent']}; animation: blink 1s infinite; }}
.card-status.done   {{ background: {t['accent2']}; animation: none; }}
@keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.2; }} }}
.card-body {{ font-size: 0.78rem; color: {t['text_secondary']}; line-height: 1.6; font-family: 'Syne', sans-serif; }}
.card-body.active {{ color: {t['text_primary']}; }}
.card-body.done   {{ color: {t['text_primary']}; }}

/* ── DEPTH BARS ── */
.depth-section {{ margin: 1.5rem 0; }}
.depth-label {{
    font-family: 'Space Mono', monospace; font-size: 0.6rem;
    letter-spacing: 0.2em; color: {t['text_muted']}; text-transform: uppercase; margin-bottom: 0.75rem;
}}
.depth-bar-wrap {{
    background: {t['depth_bg']}; border-radius: 4px; height: 6px;
    overflow: hidden; margin-bottom: 0.4rem;
}}
.depth-bar-fill {{
    height: 100%; border-radius: 4px;
    background: linear-gradient(90deg, {t['accent']}, {t['accent2']});
    transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
}}
.depth-bar-label {{
    display: flex; justify-content: space-between;
    font-family: 'Space Mono', monospace; font-size: 0.6rem; color: {t['text_very_muted']};
}}

/* ── FINAL OUTPUT ── */
.final-output-wrap {{
    background: {t['bg_final']}; border: 1px solid {t['border_final']};
    border-radius: 16px; padding: 2rem; margin-top: 2rem;
    position: relative; overflow: hidden;
    transition: background 0.35s ease, border-color 0.35s ease;
}}
.final-output-wrap::before {{
    content: ''; position: absolute; inset: 0;
    background: {t['radial_bg']};
    pointer-events: none;
}}
.final-badge {{
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: {t['accent_bg']}; border: 1px solid {t['border_final']};
    border-radius: 20px; padding: 0.25rem 0.75rem;
    font-family: 'Space Mono', monospace; font-size: 0.6rem;
    color: {t['accent']}; letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 1rem;
}}
.final-topic {{ font-size: 1.4rem; font-weight: 800; color: {t['text_primary']}; margin-bottom: 1rem; line-height: 1.3; }}
.final-text  {{ font-size: 0.9rem; line-height: 1.9; color: {t['text_final']}; font-family: 'Syne', sans-serif; }}

/* ── STATS ── */
.stats-row {{ display: flex; gap: 1rem; margin: 1.5rem 0; flex-wrap: wrap; }}
.stat-chip {{
    background: {t['stat_bg']}; border: 1px solid {t['stat_border']};
    border-radius: 8px; padding: 0.75rem 1rem; flex: 1; min-width: 120px; text-align: center;
    transition: background 0.35s ease;
}}
.stat-value {{
    font-family: 'Space Mono', monospace; font-size: 1.5rem; font-weight: 700;
    background: linear-gradient(135deg, {t['accent']}, {t['accent2']});
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1; margin-bottom: 0.25rem;
}}
.stat-label {{
    font-family: 'Space Mono', monospace; font-size: 0.55rem;
    color: {t['text_very_muted']}; letter-spacing: 0.15em; text-transform: uppercase;
}}

/* ── INPUT AREA ── */
.stTextInput > div > div > input {{
    background: {t['input_bg']} !important;
    border: 1px solid {t['input_border']} !important;
    border-radius: 10px !important; color: {t['text_primary']} !important;
    font-family: 'Syne', sans-serif !important; font-size: 1rem !important;
    padding: 0.75rem 1rem !important;
    transition: background 0.35s ease, border-color 0.35s ease;
}}
.stTextInput > div > div > input:focus {{
    border-color: {t['input_border_focus']} !important;
    box-shadow: 0 0 20px {t['input_shadow']} !important;
}}
.stTextInput label {{
    font-family: 'Space Mono', monospace !important; font-size: 0.65rem !important;
    letter-spacing: 0.2em !important; color: {t['text_muted']} !important; text-transform: uppercase !important;
}}
.stTextArea textarea {{
    background: {t['input_bg']} !important;
    border: 1px solid {t['input_border']} !important;
    border-radius: 10px !important; color: {t['text_primary']} !important;
    font-family: 'Syne', sans-serif !important;
}}
.stButton button {{
    background: linear-gradient(135deg, {t['accent']} 0%, #0891b2 100%) !important;
    border: none !important; border-radius: 10px !important;
    color: {t['btn_color']} !important; font-family: 'Space Mono', monospace !important;
    font-size: 0.75rem !important; font-weight: 700 !important;
    letter-spacing: 0.15em !important; text-transform: uppercase !important;
    padding: 0.75rem 2.5rem !important; transition: all 0.3s ease !important; width: 100% !important;
}}
.stButton button:hover {{ transform: translateY(-2px) !important; box-shadow: 0 8px 30px {t['input_shadow']} !important; }}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{
    background: transparent !important; gap: 0.5rem;
    border-bottom: 1px solid {t['border_soft']} !important;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important; color: {t['text_muted']} !important;
    font-family: 'Space Mono', monospace !important; font-size: 0.65rem !important;
    letter-spacing: 0.15em !important; text-transform: uppercase !important;
    border-radius: 6px 6px 0 0 !important; padding: 0.5rem 1rem !important; border: none !important;
}}
.stTabs [aria-selected="true"] {{
    background: {t['tab_active_bg']} !important; color: {t['accent']} !important;
    border-bottom: 2px solid {t['accent']} !important;
}}

/* ── FILE UPLOADER ── */
.stFileUploader {{
    background: {t['bg2']} !important;
    border: 1px dashed {t['input_border']} !important;
    border-radius: 12px !important; padding: 1rem !important;
}}
.stFileUploader label {{
    font-family: 'Space Mono', monospace !important; font-size: 0.65rem !important;
    color: {t['text_muted']} !important; text-transform: uppercase !important; letter-spacing: 0.15em !important;
}}

/* ── SCROLLBAR ── */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {t['scrollbar']}; border-radius: 2px; }}

/* ── INFO / WARNING ── */
.stAlert {{ background: {t['accent_bg']} !important; border: 1px solid {t['border']} !important; border-radius: 10px !important; }}

/* ── EXPANDER ── */
.streamlit-expanderHeader {{
    background: {t['bg2']} !important;
    color: {t['text_primary']} !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.1em !important;
    border-radius: 8px !important;
}}
</style>
"""

# Inject CSS based on current theme
t = get_theme()
st.markdown(build_css(t), unsafe_allow_html=True)

# =======================
# ENV & LLM
# =======================
@st.cache_resource
def get_llm():
    return ChatGroq(
        model="qwen/qwen3-32b",
        temperature=0,
        reasoning_format="parsed",
        max_retries=2,
    )

llm = get_llm()

# =======================
# PROMPTS
# =======================
BASAL_GENERATOR_PROMPT = """
You are a conceptual explanation agent.
Task: Give a broad, shallow, end-to-end conceptual overview of the subtopic. Cover full breadth, not depth.
Rules: High-level theory only. No deep dives. No repetition. No examples/tools/applications. Max {word_limit} words.
Output (JSON ONLY): {{"new_content": "<text>"}}
"""

GENERATOR_PROMPT = """
You are a conceptual explanation agent.
Task: Given the research subtopic, current explanation, and unresolved conceptual questions,
add new conceptual content addressing missing foundations or clarifying unclear ideas.
Cycle Information: Round {cycle} of 3. Expected Depth: {depth_level}
Guidance:
- If questions are present, focus ONLY on resolving those gaps
- If no questions are present, {depth_instruction}
- Each cycle should explore deeper layers of the topic
Rules: Theory only. Do NOT repeat existing content. No code/tools/applications. Max {word_limit} words.
Output (JSON ONLY): {{"new_content": "<text>"}}
"""

SCRUTINIZER_PROMPT = """
You are a strict research scrutinizer.
Task: Decide whether the current explanation has conceptual gaps that block basic understanding.
If so, ask short, clear, fundamental questions.
Rules: Ask at most 3 questions. Ask none if explanation is sufficient. Do NOT repeat previously asked questions.
Previously asked questions: {asked_questions}
Output (JSON ONLY): {{"questions": ["<question>"]}}
"""

DEEPER_GENERATOR_PROMPT = """
You are a deep conceptual exploration agent.
Task: Explore the DEEPER THEORETICAL FOUNDATIONS of this topic.
Cycle Information: Round {cycle} of 3 (DEEPER CYCLE). Focus Areas: {deeper_focus}
Rules: Theory only. No repetition. No code/tools/applications. Max {word_limit} words.
Output (JSON ONLY): {{"new_content": "<text>"}}
"""

DEPTH_VALIDATOR_PROMPT = """
You are a conceptual depth analyzer.
Task: Analyze both explanations and assess whether the new one represents GENUINE DEEPER understanding.
Previous explanation: {baseline}
New content: {new_content}
Output (JSON ONLY): {{"depth_improvement_percent": <number 0-100>, "is_genuinely_deeper": <true/false>, "depth_analysis": "<brief analysis>", "recommendation": "<accept/deepen_further>"}}
"""

REFINER_PROMPT = """
You are a conceptual synthesis agent.
Task: Merge the previous explanation with the newly generated content into a single, lucid explanation.
Cycle Information: Round {cycle} of 3. Depth Strategy: {depth_strategy}
Rules: Preserve all concepts. Remove redundancy only. Maintain logical flow (foundational → advanced). Max {word_limit} words.
Topic: {topic}
Previous explanation: {baseline}
New content: {new_content}
Output (JSON ONLY): {{"refined_explanation": "<text>"}}
"""

FINAL_REFINER_PROMPT = """
You are a conceptual explanation agent.
Task: Polish the explanation to be beginner-friendly. Keep all concepts. Order basic to advanced. Use short sentences. Add transitions. Max {word_limit} words.
Topic: {topic}
Explanation: {explanation}
Output (JSON ONLY): {{"refined_explanation": "<text>"}}
"""

IMAGE_TOPIC_EXTRACTOR_PROMPT = """
You are a research topic extraction agent.
Task: Given an image (encoded as base64) and an optional hint, identify the primary concept, topic, or subject shown.
Return a clean, concise research topic string — 3 to 10 words — that can be used as input for a deep research pipeline.
Output (JSON ONLY): {{"topic": "<research topic string>"}}
"""

# =======================
# AGENT FUNCTIONS
# =======================
@robust_llm_call
def generate_basal_explanation(subtopic, word_limit):
    prompt = BASAL_GENERATOR_PROMPT.format(word_limit=word_limit)
    msg = llm.invoke([("system", prompt), ("human", f"Subtopic:\n{subtopic}")])
    parsed = safe_json_loads(msg.content, {"new_content": "Error: Could not generate basal explanation"})
    return extract_json_value(parsed, "new_content", "Error: Could not generate basal explanation")

@robust_llm_call
def generate_new_content(subtopic, baseline, questions, word_limit, cycle=1):
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
    prompt = GENERATOR_PROMPT.format(
        word_limit=word_limit, cycle=cycle,
        depth_level=depth_levels.get(cycle, "advanced"),
        depth_instruction=depth_instructions.get(cycle, "deepen the explanation")
    )
    msg = llm.invoke([
        ("system", prompt),
        ("human", f"Subtopic:\n{subtopic}\n\nCurrent explanation:\n{baseline}\n\nUnresolved questions:\n{json.dumps(questions)}")
    ])
    parsed = safe_json_loads(msg.content, {"new_content": "Error: Could not generate new content"})
    return extract_json_value(parsed, "new_content", "Error: Could not generate new content")

@robust_llm_call
def generate_deeper_content(subtopic, baseline, questions, word_limit, cycle=2):
    deeper_focus_areas = {
        2: "- Underlying mechanisms\n- Relationships between concepts\n- Intermediate principles\n- System dynamics",
        3: "- Fundamental theoretical principles\n- Complex interdependencies\n- Trade-offs and constraints\n- Emergent properties\n- Theoretical implications"
    }
    prompt = DEEPER_GENERATOR_PROMPT.format(
        word_limit=word_limit, cycle=cycle,
        deeper_focus=deeper_focus_areas.get(cycle, "advanced theoretical exploration")
    )
    msg = llm.invoke([
        ("system", prompt),
        ("human", f"Subtopic:\n{subtopic}\n\nCurrent explanation:\n{baseline}\n\nQuestions:\n{json.dumps(questions)}")
    ])
    parsed = safe_json_loads(msg.content, {"new_content": "Error: Could not generate deeper content"})
    return extract_json_value(parsed, "new_content", "Error: Could not generate deeper content")

@robust_llm_call
def validate_depth(baseline, new_content):
    prompt = DEPTH_VALIDATOR_PROMPT.format(baseline=baseline, new_content=new_content)
    msg = llm.invoke([("system", prompt), ("human", "Validate depth improvement")])
    parsed = safe_json_loads(msg.content, {
        "depth_improvement_percent": 0,
        "is_genuinely_deeper": False,
        "depth_analysis": "Validation failed",
        "recommendation": "accept"
    })
    return validate_llm_response(parsed, AGENT_SCHEMAS["validator"])

@robust_llm_call
def scrutinize(subtopic, explanation, asked_questions):
    prompt = SCRUTINIZER_PROMPT.format(
        asked_questions=json.dumps(list(asked_questions))
    )
    msg = llm.invoke([
        ("system", prompt),
        ("human", f"Explanation:\n{explanation}")
    ])
    content = msg.content.strip()
    parsed = safe_json_loads(content, {"questions": []})
    questions = extract_json_value(parsed, "questions", [])
    if not isinstance(questions, list):
        questions = [str(questions)] if questions else []
    questions = [q.strip() for q in questions if q and q.strip()]
    return [q for q in questions if q not in asked_questions]

@robust_llm_call
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
    parsed = safe_json_loads(msg.content, {"refined_explanation": f"{baseline}\n\n{new_content}"})
    return extract_json_value(parsed, "refined_explanation", f"{baseline}\n\n{new_content}")

@robust_llm_call
def final_refine(explanation, subtopic, word_limit):
    prompt = FINAL_REFINER_PROMPT.format(word_limit=word_limit, topic=subtopic, explanation=explanation)
    msg = llm.invoke([("system", prompt)])
    parsed = safe_json_loads(msg.content, {"refined_explanation": explanation})
    return extract_json_value(parsed, "refined_explanation", explanation)

def extract_topic_from_image(image_bytes, hint=""):
    if hint:
        return hint
    return "concepts shown in the uploaded image"

# =======================
# UI HELPERS
# =======================
AGENTS = [
    {"id": "planner",     "icon": "🗺️",  "label": "Planner"},
    {"id": "generator",   "icon": "⚡",   "label": "Generator"},
    {"id": "scrutinizer", "icon": "🔬",  "label": "Scrutinizer"},
    {"id": "validator",   "icon": "📊",  "label": "Validator"},
    {"id": "refiner",     "icon": "✨",  "label": "Refiner"},
]

def render_pipeline(active_agent=None, done_agents=None):
    t = get_theme()
    done_agents = done_agents or []
    nodes_html = ""
    for i, agent in enumerate(AGENTS):
        is_active = agent["id"] == active_agent
        is_done   = agent["id"] in done_agents
        state = "active" if is_active else ("done" if is_done else "idle")
        nodes_html += f"""
        <div class="agent-node">
            <div class="agent-icon-wrap {state}">{agent['icon']}</div>
            <div class="agent-label {state}">{agent['label']}</div>
        </div>"""
        if i < len(AGENTS) - 1:
            if is_active:
                arrow_cls = "flow-active"
            elif is_done:
                arrow_cls = "flow-done"
            else:
                arrow_cls = ""
            nodes_html += f'<div class="arrow-connector {arrow_cls}">→</div>'

    return f"""
    <div class="pipeline-container">
        <div class="pipeline-title">▸ Agent Pipeline — Live View</div>
        <div class="agents-row">{nodes_html}</div>
        <div class="loop-badge">⟳ Generator ⇄ Scrutinizer loop × 3 iterations</div>
    </div>"""

def render_iter_dots(current_iter):
    dots = ""
    for i in range(1, 4):
        if i < current_iter:
            dots += '<div class="iter-dot done"></div>'
        elif i == current_iter:
            dots += '<div class="iter-dot active"></div>'
        else:
            dots += '<div class="iter-dot"></div>'
    return f'<div class="iter-row">{dots}</div>'

def render_agent_card(title, icon, content, state="idle"):
    short = (content[:280] + "…") if len(content) > 280 else content
    short = short.replace("<", "&lt;").replace(">", "&gt;")
    return f"""
    <div class="agent-card {state}">
        <div class="card-header">
            <span class="card-icon">{icon}</span>
            <span class="card-title {state}">{title}</span>
            <span class="card-status {state}"></span>
        </div>
        <div class="card-body {state}">{short}</div>
    </div>"""

def render_depth_bar(label, value, round_num):
    clamped = min(max(int(value), 0), 100)
    return f"""
    <div style="margin-bottom:0.75rem;">
        <div class="depth-bar-label">
            <span>Round {round_num} — {label}</span>
            <span>{clamped}%</span>
        </div>
        <div class="depth-bar-wrap">
            <div class="depth-bar-fill" style="width:{clamped}%"></div>
        </div>
    </div>"""

def render_stats(questions_count, rounds_done, total_improvement):
    return f"""
    <div class="stats-row">
        <div class="stat-chip">
            <div class="stat-value">{rounds_done}/3</div>
            <div class="stat-label">Cycles Done</div>
        </div>
        <div class="stat-chip">
            <div class="stat-value">{questions_count}</div>
            <div class="stat-label">Questions</div>
        </div>
        <div class="stat-chip">
            <div class="stat-value">{total_improvement}%</div>
            <div class="stat-label">Depth Gain</div>
        </div>
    </div>"""

def update_cards(cards_ph, card_state):
    html = '<div class="output-grid">'
    for a in AGENTS:
        content, state = card_state[a["id"]]
        html += render_agent_card(a["label"], a["icon"], content or "Waiting…", state)
    html += "</div>"
    cards_ph.markdown(html, unsafe_allow_html=True)

# =======================
# THEME TOGGLE (top-right)
# =======================
t = get_theme()

# Render toggle in a right-aligned column
_toggle_left, _toggle_right = st.columns([5, 1])
with _toggle_right:
    toggle_label = f"{t['toggle_icon']}  {t['toggle_label']}"
    if st.button(toggle_label, key="theme_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

# Refresh theme after potential toggle
t = get_theme()

# =======================
# HEADER
# =======================
st.markdown(f"""
<div class="hero">
    <div class="hero-eyebrow">Multi-Agent Research System</div>
    <div class="hero-title">Deep Research Engine</div>
    <div class="hero-sub">Generator · Scrutinizer · Validator · Refiner · 3× Depth Cycles</div>
</div>
""", unsafe_allow_html=True)

# =======================
# INPUT TABS
# =======================
tab1, tab2, tab3 = st.tabs(["📝  Text", "🖼️  Image", "🎙️  Audio"])

text_input     = ""
img_file       = None
img_topic_hint = ""
audio_file     = None

with tab1:
    text_input = st.text_input(
        "Research Topic",
        placeholder="e.g. Transformer attention mechanisms, Reinforcement learning, Quantum entanglement…"
    )

with tab2:
    img_file = st.file_uploader(
        "Upload an image — describe its research topic below",
        type=["png", "jpg", "jpeg", "webp"]
    )
    img_topic_hint = st.text_input(
        "What concept does this image show?",
        placeholder="e.g. Neural network architecture diagram, DNA replication, Black hole accretion disk…"
    )
    if img_file and not img_topic_hint:
        st.info("💡 Add a topic hint above so the engine knows what to research from your image.")

with tab3:
    audio_file = st.file_uploader(
        "Upload audio — describe its topic below",
        type=["mp3", "wav", "m4a", "ogg"]
    )
    audio_hint = st.text_input(
        "What topic is discussed in the audio?",
        placeholder="e.g. Lecture on photosynthesis, Podcast about blockchain consensus…"
    )
    if audio_file and not audio_hint:
        st.info("💡 Add a topic description above — the engine will research it deeply.")

# =======================
# RESOLVE FINAL TOPIC
# =======================
topic_to_research = ""

if text_input.strip():
    topic_to_research = text_input.strip()
elif img_file and img_topic_hint.strip():
    topic_to_research = img_topic_hint.strip()
elif img_file:
    topic_to_research = "concepts shown in the uploaded image"
elif audio_file and audio_hint.strip():
    topic_to_research = audio_hint.strip()
elif audio_file:
    topic_to_research = "topic discussed in the uploaded audio"

# =======================
# RUN BUTTON
# =======================
col_btn, col_space = st.columns([1, 3])
with col_btn:
    run_clicked = st.button("⚡  Run Research", disabled=not topic_to_research)

# =======================
# LIVE UI PLACEHOLDERS
# =======================
pipeline_ph = st.empty()
iter_ph     = st.empty()
cards_ph    = st.empty()
depth_ph    = st.empty()
stats_ph    = st.empty()

# Show idle pipeline when nothing is running
if not run_clicked and st.session_state.result is None:
    pipeline_ph.markdown(render_pipeline(), unsafe_allow_html=True)

# =======================
# MAIN RESEARCH PIPELINE
# =======================
if run_clicked and topic_to_research:
    st.session_state.result             = None
    st.session_state.rounds_data        = []
    st.session_state.asked_questions_list = []
    st.session_state.topic_used         = topic_to_research

    basal_limit   = 150
    gen_limits    = {1: 120, 2: 180, 3: 220}
    refine_limits = {1: 150, 2: 275, 3: 400}

    done_agents     = []
    depth_history   = []
    asked_questions = set()
    rounds          = []

    card_state = {a["id"]: ("", "idle") for a in AGENTS}

    # ── PHASE 0: Planner ──────────────────────────────────────────────────
    pipeline_ph.markdown(render_pipeline("planner", done_agents), unsafe_allow_html=True)
    iter_ph.markdown(render_iter_dots(1), unsafe_allow_html=True)

    card_state["planner"] = (
        f"Initializing deep research on:\n{topic_to_research}\n\nGenerating basal overview…",
        "active"
    )
    update_cards(cards_ph, card_state)

    baseline = generate_basal_explanation(topic_to_research, basal_limit)

    done_agents.append("planner")
    card_state["planner"] = (baseline, "done")
    update_cards(cards_ph, card_state)

    # ── CYCLES 1-3 ───────────────────────────────────────────────────────
    for i in range(1, 4):
        iter_ph.markdown(render_iter_dots(i), unsafe_allow_html=True)

        # ── Generator ──
        pipeline_ph.markdown(render_pipeline("generator", done_agents), unsafe_allow_html=True)
        round_label = "Foundational deepening" if i == 1 else f"Advanced theoretical deepening (L{i})"
        card_state["generator"] = (f"Round {i}/3 — {round_label}…", "active")
        update_cards(cards_ph, card_state)

        questions = scrutinize(topic_to_research, baseline, asked_questions)
        asked_questions.update(questions)

        if i == 1:
            new_content = generate_new_content(
                topic_to_research, baseline, questions, gen_limits[i], cycle=i
            )
        else:
            new_content = generate_deeper_content(
                topic_to_research, baseline, questions, gen_limits[i], cycle=i
            )

        card_state["generator"] = (new_content, "done")
        update_cards(cards_ph, card_state)

        # ── Scrutinizer ──
        pipeline_ph.markdown(render_pipeline("scrutinizer", done_agents + ["generator"]), unsafe_allow_html=True)
        card_state["scrutinizer"] = (
            f"Scanning for conceptual gaps… Found {len(questions)} question(s).",
            "active"
        )
        update_cards(cards_ph, card_state)

        qs_display = (
            "\n".join([f"• {q}" for q in questions])
            if questions else "✅ No gaps found — explanation is sufficient."
        )
        card_state["scrutinizer"] = (qs_display, "done")
        update_cards(cards_ph, card_state)

        # ── Validator ──
        pipeline_ph.markdown(
            render_pipeline("validator", done_agents + ["generator", "scrutinizer"]),
            unsafe_allow_html=True
        )
        card_state["validator"] = ("Measuring depth improvement…", "active")
        update_cards(cards_ph, card_state)

        depth_check = validate_depth(baseline, new_content)
        imp = depth_check["depth_improvement_percent"]
        depth_history.append((i, imp, depth_check["depth_analysis"]))

        if imp < 30 and i > 1:
            card_state["validator"] = (
                f"⚠️ Only {imp}% depth gain detected. Regenerating with stronger focus…",
                "active"
            )
            update_cards(cards_ph, card_state)

            new_content = generate_deeper_content(
                topic_to_research, baseline, questions, gen_limits[i] + 50, cycle=i
            )
            depth_check = validate_depth(baseline, new_content)
            imp = depth_check["depth_improvement_percent"]
            depth_history[-1] = (i, imp, depth_check["depth_analysis"])

        card_state["validator"] = (
            f"+{imp}% depth improvement\n\n{depth_check['depth_analysis']}",
            "done"
        )
        update_cards(cards_ph, card_state)

        depth_html = '<div class="depth-section"><div class="depth-label">▸ Depth Progression</div>'
        for rd, pct, _ in depth_history:
            depth_html += render_depth_bar("Depth Gain", pct, rd)
        depth_html += "</div>"
        depth_ph.markdown(depth_html, unsafe_allow_html=True)

        # ── Refiner ──
        pipeline_ph.markdown(
            render_pipeline("refiner", done_agents + ["generator", "scrutinizer", "validator"]),
            unsafe_allow_html=True
        )
        card_state["refiner"] = (f"Merging and synthesizing — Round {i}/3…", "active")
        update_cards(cards_ph, card_state)

        baseline = refine(baseline, new_content, refine_limits[i], topic_to_research, cycle=i)

        card_state["refiner"] = (baseline, "done")

        done_agents = ["planner", "generator", "scrutinizer", "validator", "refiner"]
        pipeline_ph.markdown(render_pipeline(None, done_agents), unsafe_allow_html=True)
        update_cards(cards_ph, card_state)

        rounds.append({
            "round": i,
            "questions": list(questions),
            "depth_improvement": imp,
            "depth_analysis": depth_check["depth_analysis"],
        })

    # ── FINAL REFINE ─────────────────────────────────────────────────────
    iter_ph.markdown(render_iter_dots(4), unsafe_allow_html=True)

    pipeline_ph.markdown(render_pipeline("refiner", ["planner", "generator", "scrutinizer", "validator"]), unsafe_allow_html=True)
    card_state["refiner"] = ("Final polish — beginner-friendly synthesis in progress…", "active")
    update_cards(cards_ph, card_state)

    final_answer = final_refine(baseline, topic_to_research, word_limit=600)

    card_state["refiner"] = (final_answer, "done")
    done_agents = ["planner", "generator", "scrutinizer", "validator", "refiner"]
    pipeline_ph.markdown(render_pipeline(None, done_agents), unsafe_allow_html=True)
    update_cards(cards_ph, card_state)

    # ── Stats ────────────────────────────────────────────────────────────
    total_imp = sum(r["depth_improvement"] for r in rounds)
    stats_ph.markdown(
        render_stats(len(asked_questions), 3, total_imp),
        unsafe_allow_html=True
    )

    st.session_state.result               = final_answer
    st.session_state.rounds_data          = rounds
    st.session_state.asked_questions_list = list(asked_questions)


# =======================
# FINAL OUTPUT (persists after run)
# =======================
if st.session_state.result:
    final          = st.session_state.result
    rounds         = st.session_state.rounds_data
    questions_list = st.session_state.asked_questions_list
    topic_used     = st.session_state.get("topic_used", topic_to_research)

    if rounds:
        total_imp = sum(r["depth_improvement"] for r in rounds)
        stats_ph.markdown(
            render_stats(len(questions_list), 3, total_imp),
            unsafe_allow_html=True
        )

    safe_topic = topic_used.replace("<", "&lt;").replace(">", "&gt;")
    safe_final = final.replace("<", "&lt;").replace(">", "&gt;")

    st.markdown(f"""
    <div class="final-output-wrap">
        <div class="final-badge">✦ Research Complete</div>
        <div class="final-topic">{safe_topic}</div>
        <div class="final-text">{safe_final}</div>
    </div>
    """, unsafe_allow_html=True)

    col_copy, col_dl, _ = st.columns([1, 1, 3])
    with col_copy:
        if st.button("📋  Copy Output"):
            st.write("Use Ctrl+A → Ctrl+C on the output above to copy.")
    with col_dl:
        st.download_button(
            label="⬇️  Download .txt",
            data=f"Topic: {topic_used}\n\n{final}",
            file_name=f"research_{topic_used[:30].replace(' ', '_')}.txt",
            mime="text/plain",
        )

    with st.expander("📋  Research Audit Trail — Full Iteration History"):
        for r in rounds:
            depth_bar_val = r["depth_improvement"]
            st.markdown(
                f"**Round {r['round']}** — Depth gain: `+{depth_bar_val}%` — "
                f"*{r.get('depth_analysis', '')}*"
            )
            if r["questions"]:
                for q in r["questions"]:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;🔬 {q}")
            else:
                st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;✅ No conceptual gaps found")
            st.markdown("---")

        st.markdown(f"**All questions explored ({len(questions_list)}):**")
        for q in questions_list:
            st.markdown(f"- {q}")
