import json
import duckdb
import streamlit as st
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from dotenv import load_dotenv

load_dotenv()

DB_PATH   = 'data/numero.duckdb'
TABLE     = "films_raw"
DATA_COL  = "data"
DATE_COL  = "week_date"
ROW_LIMIT = 50               # max rows to display
ANSWER_ROWS_LIMIT = 200      # max rows passed into the answer step

@st.cache_resource
def get_conn(path: str):
    return duckdb.connect(path, read_only=True)

conn = get_conn(DB_PATH)

# ==== Model setup ====
MODEL_NAME = "gpt-3.5-turbo"
AGENT_SPEC = f"openai:{MODEL_NAME}"

# ---------- Agent 1: SQL generation ----------
class SQLResult(BaseModel):
    sql_query: str = Field(..., description="A valid DuckDB SELECT query")

@dataclass
class Deps:
    conn: duckdb.DuckDBPyConnection

sql_agent = Agent[Deps, SQLResult](AGENT_SPEC, output_type=SQLResult, deps_type=Deps)

@sql_agent.system_prompt
async def sys_prompt() -> str:
    return f"""
You are a SQL generator for DuckDB.
Data is in table {TABLE}, with JSON column '{DATA_COL}' containing array $.films.
To read films, always explode with:
    FROM {TABLE} fr, json_each(fr.{DATA_COL}, '$.films') f
Then select fields like:
    json_extract_string(f.value,'$.title') AS title,
    CAST(json_extract(f.value,'$.week.gross') AS DOUBLE) AS week_gross,
    CAST(json_extract(f.value,'$.weekend.gross') AS DOUBLE) AS weekend_gross
If asked for only a few rows, add LIMIT.
Only return one SELECT query, no markdown fences.
"""

# ---------- Agent 2: Answer from results ----------
class AnswerOut(BaseModel):
    final_answer: str = Field(..., description="Natural-language answer based strictly on provided rows")

answer_agent = Agent[None, AnswerOut](AGENT_SPEC, output_type=AnswerOut)

@answer_agent.system_prompt
async def answer_sys() -> str:
    return """
You are a careful data analyst.
Given the user's QUESTION and SQL RESULT ROWS (as JSON records), produce a direct, concise answer.
- If the question is in Vietnamese, answer in Vietnamese; otherwise answer in English.
- Cite key numbers with units if present (e.g., $, %, counts, dates).
- If the result set is empty, say there were no matching rows.
- Do NOT invent data beyond the provided rows.
- If asked to list items, produce a short bullet list.
"""

# ==== UI ====
st.set_page_config(page_title="Simple Ask DB", page_icon="🎬")
st.title("Simple ChatBot NL->SQL->Answer")

question = st.text_input("Question:", placeholder="Example: show the first 5 films")
ask = st.button("Ask")

if ask and question.strip():
    with st.spinner("Generating SQL & running..."):
        # Generate SQL
        deps = Deps(conn=conn)
        res = sql_agent.run_sync(question, deps=deps)
        sql = res.output.sql_query.strip().rstrip(";")
        st.subheader("Generated SQL")
        st.code(sql, language="sql")

        # Execute SQL
        try:
            df = conn.execute(sql).fetchdf()
        except Exception as e:
            st.error(f"Query failed: {e}")
            st.stop()

        # Display table & JSON preview
        st.subheader("Result")
        st.dataframe(df.head(ROW_LIMIT), use_container_width=True)

        st.subheader("JSON (preview)")
        preview_records = df.head(min(len(df), ROW_LIMIT)).to_dict(orient="records")
        st.code(json.dumps(preview_records, ensure_ascii=False, indent=2))

        # Generate natural-language answer from result
        with st.spinner("Summarizing answer from SQL result..."):
            # Limit rows for LLM
            rows_for_llm = df.head(min(len(df), ANSWER_ROWS_LIMIT)).to_dict(orient="records")

            prompt = (
                "QUESTION:\n"
                f"{question}\n\n"
                "SQL RESULT ROWS (JSON array of objects):\n"
                f"{json.dumps(rows_for_llm, ensure_ascii=False)}"
            )

            ans = answer_agent.run_sync(prompt)
            final_answer = ans.output.final_answer

        st.subheader("Answer")
        st.markdown(final_answer)

elif ask:
    st.warning("Please enter a question before clicking Ask.")
