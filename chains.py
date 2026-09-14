import re
import os

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

from prompts import SQL_PROMPT, SQL_CORRECTION_PROMPT, ANSWER_PROMPT, SCHEMA
from db import execute_sql

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def get_llm():
    return ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo"),
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base=OPENROUTER_BASE_URL,
        temperature=0,
    )


def extract_sql(response: str) -> str:
    """Extract SQL from LLM response, stripping markdown fences if present."""
    text = response.strip()
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # If no fences, try to find a SELECT statement
    match = re.search(r"(SELECT\b.*)", text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


UNSAFE_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
    "TRUNCATE", "REPLACE", "ATTACH", "DETACH", "PRAGMA",
]


def validate_sql(sql: str) -> bool:
    """Check that the SQL is a safe SELECT query."""
    upper = sql.upper().strip()
    if not upper.startswith("SELECT"):
        return False
    for keyword in UNSAFE_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper):
            return False
    return True


def format_result(columns: list[str], rows: list[dict], row_count: int) -> str:
    """Format database result as a readable string for the LLM."""
    if row_count == 0:
        return "No records found."

    header = " | ".join(columns)
    separator = "-" * len(header)
    lines = [header, separator]
    for row in rows:
        line = " | ".join(str(row[col]) for col in columns)
        lines.append(line)
    lines.append(f"\n({row_count} record{'s' if row_count != 1 else ''})")
    return "\n".join(lines)


def run_question(question: str) -> dict:
    """
    Full pipeline: Question -> SQL -> Execute -> Answer.
    Returns dict with keys: sql, result, answer, error.
    """
    llm = get_llm()
    sql_chain = SQL_PROMPT | llm | StrOutputParser()
    answer_chain = ANSWER_PROMPT | llm | StrOutputParser()
    correction_chain = SQL_CORRECTION_PROMPT | llm | StrOutputParser()

    # Step 1: Generate SQL
    try:
        raw_sql = sql_chain.invoke({"question": question, "schema": SCHEMA})
        sql = extract_sql(raw_sql)
    except Exception as e:
        return {"sql": "", "result": "", "answer": "", "error": f"Failed to generate SQL: {e}"}

    # Step 2: Validate SQL
    if not validate_sql(sql):
        return {
            "sql": sql,
            "result": "",
            "answer": "The generated query is not a valid read-only SELECT statement. Please try rephrasing your question.",
            "error": "SQL validation failed",
        }

    # Step 3: Execute SQL
    try:
        columns, rows, row_count = execute_sql(sql)
    except Exception as e:
        # Step 3a: Try correction
        try:
            corrected_raw = correction_chain.invoke({
                "question": question,
                "sql": sql,
                "error": str(e),
                "schema": SCHEMA,
            })
            corrected_sql = extract_sql(corrected_raw)

            if not validate_sql(corrected_sql):
                return {
                    "sql": corrected_sql,
                    "result": "",
                    "answer": "I couldn't process that request. Please try asking the question in another way.",
                    "error": "Corrected SQL also failed validation",
                }

            try:
                columns, rows, row_count = execute_sql(corrected_sql)
                sql = corrected_sql
            except Exception as e2:
                return {
                    "sql": corrected_sql,
                    "result": "",
                    "answer": "I couldn't process that request. Please try asking the question in another way.",
                    "error": f"Corrected SQL also failed: {e2}",
                }
        except Exception:
            return {
                "sql": sql,
                "result": "",
                "answer": "I couldn't process that request. Please try asking the question in another way.",
                "error": str(e),
            }

    # Step 4: Format result
    result_str = format_result(columns, rows, row_count)

    # Step 5: Generate answer
    try:
        answer = answer_chain.invoke({
            "question": question,
            "sql": sql,
            "result": result_str,
        })
    except Exception as e:
        return {
            "sql": sql,
            "result": result_str,
            "answer": f"Database result available, but failed to generate answer: {e}",
            "error": str(e),
        }

    return {"sql": sql, "result": result_str, "answer": answer, "error": ""}
