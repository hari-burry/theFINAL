import streamlit as st

st.set_page_config(page_title="Knowledge Tree Demo", layout="wide")

# -----------------------
# Mock data (placeholders)
# -----------------------

knowledge_tree = {
    "Virtual Memory": {
        "Address Space Abstraction":
            "Virtual Memory: Address space abstraction explains how programs see a continuous logical memory independent of physical RAM.",
        "Paging": {
            "Page Tables":
                "Virtual Memory: Page tables map virtual pages to physical frames.",
            "Page Faults":
                "Virtual Memory: Page faults occur when a referenced page is not in memory."
        },
        "TLB":
            "Virtual Memory: The TLB caches recent page table entries to speed up translation.",
        "Performance Trade-offs":
            "Virtual Memory: Performance trade-offs involve memory usage, latency, and hardware cost."
    }
}

# -----------------------
# Session state
# -----------------------

if "current_node" not in st.session_state:
    st.session_state.current_node = "Virtual Memory"

# -----------------------
# Sidebar Knowledge Map
# -----------------------

with st.sidebar:
    st.markdown("## 🗺️ Knowledge Map")

    with st.expander("Virtual Memory", expanded=True):

        if st.button("Address Space Abstraction"):
            st.session_state.current_node = "Address Space Abstraction"

        with st.expander("Paging"):
            if st.button("Page Tables"):
                st.session_state.current_node = "Page Tables"

            if st.button("Page Faults"):
                st.session_state.current_node = "Page Faults"

        if st.button("TLB"):
            st.session_state.current_node = "TLB"

        if st.button("Performance Trade-offs"):
            st.session_state.current_node = "Performance Trade-offs"

# -----------------------
# Main Explanation Pane
# -----------------------

st.markdown("## 📘 Explanation")

explanation_map = {
    "Virtual Memory":
        "Virtual Memory is a memory management technique that provides an abstraction of large, continuous memory.",
    "Address Space Abstraction":
        knowledge_tree["Virtual Memory"]["Address Space Abstraction"],
    "Page Tables":
        knowledge_tree["Virtual Memory"]["Paging"]["Page Tables"],
    "Page Faults":
        knowledge_tree["Virtual Memory"]["Paging"]["Page Faults"],
    "TLB":
        knowledge_tree["Virtual Memory"]["TLB"],
    "Performance Trade-offs":
        knowledge_tree["Virtual Memory"]["Performance Trade-offs"],
}

st.write(
    explanation_map.get(
        st.session_state.current_node,
        "Select a concept from the knowledge map."
    )
)

# -----------------------
# Bottom Input Bar
# -----------------------

user_prompt = st.chat_input("Ask or expand a concept...")

if user_prompt:
    st.session_state.current_node = user_prompt
