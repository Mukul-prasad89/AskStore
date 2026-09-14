from langchain_core.prompts import ChatPromptTemplate

SCHEMA = """\
brands:
- brand_id (INTEGER)
- brand_name (TEXT)

t_shirts:
- tshirt_id (INTEGER)
- brand_id (INTEGER, FK -> brands.brand_id)
- product_name (TEXT)
- size (TEXT: S, M, L, XL, XXL)
- quantity (INTEGER)

pricing:
- pricing_id (INTEGER)
- tshirt_id (INTEGER, FK -> t_shirts.tshirt_id)
- price (REAL)
- discount (REAL, percentage)

sales:
- sale_id (INTEGER)
- tshirt_id (INTEGER, FK -> t_shirts.tshirt_id)
- quantity_sold (INTEGER)
- sale_date (TEXT, YYYY-MM-DD)
"""

SQL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """\
You are a SQL assistant for a clothing store.

Convert the user's question into a valid SQLite SELECT query.

Available tables and columns:

{schema}

Rules:
1. Generate only SELECT queries.
2. Use only the tables and columns provided above.
3. Do not invent data.
4. Use valid SQLite syntax.
5. Return ONLY the SQL query, nothing else.

Example:
User: How many Nike medium T-shirts are available?
SQL: SELECT b.brand_name, t.size, t.quantity FROM t_shirts t JOIN brands b ON t.brand_id = b.brand_id WHERE b.brand_name = 'Nike' AND t.size = 'M';
"""),
    ("human", "{question}"),
])

SQL_CORRECTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """\
You are a SQL correction assistant.

The user asked a question and the generated SQL failed when executed.

Here is the database schema:

{schema}

The original question was:
{question}

The SQL that was generated:
{sql}

The error was:
{error}

Generate a corrected SQLite SELECT query.
Return ONLY the corrected SQL query, nothing else.
"""),
    ("human", "Fix the SQL query."),
])

ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """\
You are a store assistant.

The user asked:
{question}

The SQL query executed was:
{sql}

The database returned:
{result}

Answer the user's question using ONLY the database result.

Do not invent information.
Do not change any numbers.
Do not make assumptions that are not supported by the result.

Give a short, clear answer suitable for a store manager.
"""),
    ("human", "{question}"),
])
