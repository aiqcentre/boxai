import json
import re
import duckdb
import streamlit as st
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from dotenv import load_dotenv
import pandas as pd
from prompts import sys_prompt, answer_sys

load_dotenv()
st.set_page_config(page_title="Simple Ask DB", page_icon="🎬", layout="wide")

st.markdown("""
<style>
.block-container { max-width: 1100px; }
.card { border:1px solid #e5e7eb; border-radius:12px; padding:14px 16px; background:#fafafa; }
</style>
""", unsafe_allow_html=True)

DB_PATH   = "data/numero.duckdb"
TABLE     = "films_raw"
DATA_COL  = "data"
DATE_COL  = "week_date"
ROW_LIMIT = 50
ANSWER_ROWS_LIMIT = 200
MODEL_NAME = "gpt-5-mini"
AGENT_SPEC = f"openai:{MODEL_NAME}"
FORBIDDEN_SQL_KEYWORDS = (
    "delete", "update", "insert", "alter", "drop", "truncate", "create",
    "replace", "grant", "revoke", "attach", "detach", "copy", "load",
    "export", "pragma", "call", "vacuum", "set"
)
DESTRUCTIVE_INTENT_WORDS = (
    "delete", "remove", "drop", "truncate", "update", "insert",
    "modify", "change", "alter", "create", "add column", "erase"
)

def _strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql

def is_user_intent_destructive(question: str) -> bool:
    q = question.lower()
    return any(w in q for w in DESTRUCTIVE_INTENT_WORDS)

def is_select_only(sql: str) -> bool:
    s = _strip_sql_comments(sql).strip().lower()
    if ";" in s:
        return False
    starts_ok = s.startswith("select") or s.startswith("with ")
    if not starts_ok:
        return False
    return not any(re.search(rf"\b{kw}\b", s) for kw in FORBIDDEN_SQL_KEYWORDS)

@st.cache_resource
def get_conn(path: str):
    return duckdb.connect(path, read_only=True)

conn = get_conn(DB_PATH)
class SQLResult(BaseModel):
    sql_query: str = Field(..., description="A valid DuckDB SELECT query")

@dataclass
class Deps:
    conn: duckdb.DuckDBPyConnection

sql_agent = Agent[Deps, SQLResult](AGENT_SPEC, output_type=SQLResult, deps_type=Deps)

@sql_agent.system_prompt
async def sql_system_prompt()->str:
    base = sys_prompt(TABLE, DATA_COL, DATE_COL)
    guard = (
        "\n\nCRITICAL RULES:\n"
        "- Only generate a single-statement SELECT (optionally WITH ... SELECT).\n"
        "- Never use DELETE/UPDATE/INSERT/ALTER/DROP/TRUNCATE/CREATE/PRAGMA/etc.\n"
        "- If the user asks to delete/modify/create data, do NOT comply; still output a harmless\n"
        "  SELECT like: SELECT 'refused' AS message WHERE 1=0.\n"
    )
    return base + guard

class AnswerOut(BaseModel):
    final_answer: str = Field(..., description="Natural-language answer based strictly on provided rows")

answer_agent = Agent[None, AnswerOut](AGENT_SPEC, output_type=AnswerOut)

@answer_agent.system_prompt
async def sql_to_nl_prompt()->str:
    return answer_sys()

# ====== UI ======
st.title("🎬 Simple ChatBot NL → SQL → Answer")
st.caption("A simple chatbot that answers questions about a dataset using SQL queries.")

with st.form("ask_form", clear_on_submit=False):
    question = st.text_input(
        "Question",
        placeholder="Example: top 5 films by weekend gross in July 2023",
    )
    ask = st.form_submit_button("Ask", type="primary")

if ask:
    if not question.strip():
        st.warning("Please enter a question before clicking Ask.")
        st.stop()
    if is_user_intent_destructive(question):
        st.error("Sorry, I can’t delete or modify data. This app is read-only.")
        st.stop()

    with st.spinner("Generating SQL & running..."):
        deps = Deps(conn=conn)
        try:
            res = sql_agent.run_sync(question, deps=deps)
            sql = res.output.sql_query.strip().rstrip(";")
        except Exception as e:
            st.error(f"SQL generation failed: {e}")
            st.stop()

        if not is_select_only(sql):
            st.error("Blocked a non-SELECT or potentially destructive SQL. This app is read-only.")
            st.subheader("Generated (blocked) SQL")
            st.code(sql, language="sql")
            st.stop()
        try:
            df: pd.DataFrame = conn.execute(sql).fetchdf()
        except Exception as e:
            st.error(f"Query failed: {e}")
            st.subheader("Generated SQL")
            st.code(sql, language="sql")
            st.stop()
        rows_for_llm = json.loads(
            df.head(ANSWER_ROWS_LIMIT).to_json(orient="records", date_format="iso")
        )
        row_count = len(rows_for_llm)
        columns = list(df.columns)

        prompt = (
            "QUESTION:\n"
            f"{question}\n\n"
            f"ROW_COUNT: {row_count}\n"
            f"COLUMNS: {columns}\n"
            "SQL RESULT ROWS (JSON array of objects):\n"
            f"{json.dumps(rows_for_llm, ensure_ascii=False)}"
        )

        try:
            ans = answer_agent.run_sync(prompt)
            final_answer = ans.output.final_answer
        except Exception as e:
            final_answer = f"Could not summarize from result. Error: {e}"

    # ====== Output ======
    st.markdown(f"#### 🧠 Answer to: *{question}*")
    tab1, tab2, tab3, tab4 = st.tabs(["🧾 Answer", "🧮 SQL", "📊 Table", "🧱 JSON"])

    with tab1:
        st.markdown(
            f"<div class='card' style='color:#9333ea; font-weight:500;'>{final_answer}</div>",
            unsafe_allow_html=True
        )

    with tab2:
        st.code(sql, language="sql")

    with tab3:
        st.caption(f"{len(df)} rows • showing up to {min(len(df), ROW_LIMIT)}")
        st.dataframe(df.head(ROW_LIMIT), use_container_width=True)
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"),
                               file_name="query_result.csv", mime="text/csv", use_container_width=True)
        with c2:
            st.download_button("Download JSON", df.to_json(orient="records", date_format="iso"),
                               file_name="query_result.json", mime="application/json", use_container_width=True)

    with tab4:
        preview_json = df.head(ROW_LIMIT).to_json(orient="records", date_format="iso")
        st.code(preview_json, language="json")


