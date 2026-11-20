import streamlit as st
import os
from dotenv import load_dotenv

from db import init_db, execute_sql
from chains import run_question, get_model

load_dotenv()

# For Streamlit Cloud: read from secrets if .env not present
if not os.getenv("OPENROUTER_API_KEY"):
    try:
        os.environ["OPENROUTER_API_KEY"] = st.secrets["OPENROUTER_API_KEY"]
        os.environ["OPENROUTER_MODEL"] = st.secrets.get("OPENROUTER_MODEL", "openrouter/auto")
    except (KeyError, FileNotFoundError):
        pass

# Initialize database
init_db()

# Page config
st.set_page_config(page_title="Store Sales AI", page_icon="🛍️", layout="centered")

# Title
st.title("🛍️ Store Sales AI")
st.caption(f"Ask questions about your store using natural language • Router: `{get_model()}`")

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

    # Capture rows for buy flow
    rows = []
    if result.get("sql"):
        try:
            _, rows, _ = execute_sql(result["sql"])
        except Exception:
            rows = []

    # Store in history
    st.session_state.history.insert(0, {
        "question": question.strip(),
        "answer": result["answer"],
        "sql": result["sql"],
        "result": result["result"],
        "error": result["error"],
        "rows": rows,
    })

    st.session_state["last_sql"] = result["sql"]
    st.session_state["last_rows"] = rows
    st.session_state["show_buy"] = False

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

    # Buy flow
    last_rows = st.session_state.get("last_rows", latest.get("rows", []))
    last_sql = st.session_state.get("last_sql", latest.get("sql", ""))
    if last_rows:
        if st.button("Buy", key="buy_btn", type="primary"):
            st.session_state["show_buy"] = True

        if st.session_state.get("show_buy"):
            if len(last_rows) > 1:
                idx = st.selectbox(
                    "Select product",
                    range(len(last_rows)),
                    format_func=lambda i: ", ".join(f"{k}={v}" for k, v in last_rows[i].items()),
                    key="buy_select",
                )
            else:
                idx = 0

            qty = st.number_input("Number of items", min_value=1, value=1, key="buy_qty")

            if st.button("Pay", key="pay_btn", type="primary"):
                # Final check against database
                try:
                    _, fresh_rows, _ = execute_sql(last_sql)
                except Exception as e:
                    st.error(f"Payment failed: could not verify stock ({e})")
                    fresh_rows = []

                def _stock(row):
                    for k, v in row.items():
                        kl = k.lower()
                        if any(w in kl for w in ("quant", "stock", "avail")):
                            try:
                                return int(v)
                            except (TypeError, ValueError):
                                try:
                                    return float(v)
                                except (TypeError, ValueError):
                                    pass
                    for v in row.values():
                        if isinstance(v, (int, float)) and not isinstance(v, bool):
                            return v
                    return None

                if idx < len(fresh_rows):
                    stock = _stock(fresh_rows[idx])
                    if stock is not None and stock >= qty:
                        st.success("Payment successful! Your order has been confirmed.")
                        st.session_state["show_buy"] = False
                    else:
                        st.error("Payment failed: product not available in the requested quantity.")
                else:
                    st.error("Payment failed: product not found.")

# Conversation history
if len(st.session_state.history) > 1:
    st.divider()
    st.subheader("📜 Conversation History")
    for i, entry in enumerate(st.session_state.history[1:], 1):
        with st.expander(f"Q{i}: {entry['question']}"):
            st.write(f"**Answer:** {entry['answer']}")
            if entry["sql"]:
                st.code(entry["sql"], language="sql")
