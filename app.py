import streamlit as st
import os
from dotenv import load_dotenv

from db import init_db
from chains import run_question

load_dotenv()

# For Streamlit Cloud: read from secrets if .env not present
if not os.getenv("OPENROUTER_API_KEY"):
    try:
        os.environ["OPENROUTER_API_KEY"] = st.secrets["OPENROUTER_API_KEY"]
        os.environ["OPENROUTER_MODEL"] = st.secrets.get("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
    except (KeyError, FileNotFoundError):
        pass

# Initialize database
init_db()

# Page config
st.set_page_config(page_title="Store Sales AI", page_icon="🛍️", layout="centered")

# Title
st.title("🛍️ Store Sales AI")
st.caption("Ask questions about your store using natural language.")

# Session state for history
if "history" not in st.session_state:
    st.session_state.history = []

# Suggested questions
SUGGESTIONS = [
    "How many Nike medium T-shirts are available?",
    "Which brand has the highest stock?",
    "What is the cheapest T-shirt after discount?",
    "Which T-shirts have more than 20% discount?",
    "How many Adidas T-shirts were sold?",
    "Which brand sold the most T-shirts?",
    "What is the total stock of XL T-shirts?",
    "What is the average price of Nike T-shirts?",
]

st.subheader("Ask your store a question:")

# Suggestion chips
cols = st.columns(4)
for i, suggestion in enumerate(SUGGESTIONS):
    col = cols[i % 4]
    with col:
        if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
            st.session_state["question_input"] = suggestion

# Question input
question = st.text_input(
    "Your question",
    value=st.session_state.get("question_input", ""),
    placeholder="e.g. How many Nike M T-shirts do we have?",
    label_visibility="collapsed",
)

# Ask button
if st.button("Ask AI", type="primary", use_container_width=True) and question.strip():
    with st.spinner("Thinking..."):
        result = run_question(question.strip())

    # Store in history
    st.session_state.history.insert(0, {
        "question": question.strip(),
        "answer": result["answer"],
        "sql": result["sql"],
        "result": result["result"],
        "error": result["error"],
    })

# Display results
if st.session_state.history:
    latest = st.session_state.history[0]

    # Answer
    st.subheader("🤖 Answer")
    if latest["error"] and not latest["answer"]:
        st.error(latest["error"])
    else:
        st.success(latest["answer"])

    # Generated SQL
    with st.expander("🔍 Generated SQL"):
        st.code(latest["sql"], language="sql")

    # Database Result
    with st.expander("📊 Database Result"):
        if latest["result"]:
            st.text(latest["result"])
        else:
            st.info("No results returned.")

# Conversation history
if len(st.session_state.history) > 1:
    st.divider()
    st.subheader("📜 Conversation History")
    for i, entry in enumerate(st.session_state.history[1:], 1):
        with st.expander(f"Q{i}: {entry['question']}"):
            st.write(f"**Answer:** {entry['answer']}")
            if entry["sql"]:
                st.code(entry["sql"], language="sql")
