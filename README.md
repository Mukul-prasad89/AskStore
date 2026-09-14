# Store Sales GenAI Assistant

A natural-language interface for querying a store's SQLite database using an LLM.

## What it does

A store manager can ask questions about store data (inventory, pricing, sales) in plain English. The app converts the question to SQL using an LLM, executes it against a local SQLite database, and returns a natural-language answer.

## Architecture

```
User Question
      ↓
LangChain SQL Chain
      ↓
OpenRouter LLM
      ↓
SQL Query
      ↓
SQL Validation
      ↓
SQLite Database
      ↓
Query Result
      ↓
LangChain Answer Chain
      ↓
OpenRouter LLM
      ↓
Natural Language Answer
      ↓
Streamlit
```

If SQL execution fails, the app sends the error back to the LLM for one correction attempt.

## Technologies

- **Streamlit** — UI
- **LangChain** — LLM chain orchestration
- **OpenRouter** — LLM provider
- **SQLite** — local database (via Python's built-in `sqlite3`)
- **python-dotenv** — environment configuration

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

Create `.env`:

```
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=openai/gpt-3.5-turbo
```

Run:

```bash
streamlit run app.py
```

## Example Questions

- How many Nike medium T-shirts are available?
- Which brand has the highest stock?
- What is the cheapest T-shirt after discount?
- Which T-shirts have more than 20% discount?
- How many Adidas T-shirts were sold?
- Which brand sold the most T-shirts?
- What is the total stock of XL T-shirts?
- What is the average price of Nike T-shirts?
