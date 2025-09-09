import json
import duckdb
import streamlit as st
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from dotenv import load_dotenv
import pandas as pd
from prompts import sys_prompt, answer_sys
load_dotenv()
st.set_page_config(page_title="Simple Ask DB", page_icon="🎬")
DB_PATH   = "data/numero.duckdb"
TABLE     = "films_raw"
DATA_COL  = "data"      
DATE_COL  = "week_date"
ROW_LIMIT = 50            
ANSWER_ROWS_LIMIT = 200   

@st.cache_resource
def get_conn(path: str):
    return duckdb.connect(path, read_only=True)
conn = get_conn(DB_PATH)
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
async def sql_system_prompt()->str:
    return sys_prompt(TABLE, DATA_COL, DATE_COL)

# ---------- Agent 2: Answer from results ----------
class AnswerOut(BaseModel):
    final_answer: str = Field(..., description="Natural-language answer based strictly on provided rows")

answer_agent = Agent[None, AnswerOut](AGENT_SPEC, output_type=AnswerOut)

@answer_agent.system_prompt
async def sql_to_nl_prompt()->str:
    return answer_sys()


# ==== UI ====
st.title("Simple ChatBot NL->SQL->Answer")

question = st.text_input("Question:", placeholder="Example: top 5 films by weekend gross in July 2023")
ask = st.button("Ask")

if ask and question.strip():
    with st.spinner("Generating SQL & running..."):
        deps = Deps(conn=conn)
        res = sql_agent.run_sync(question, deps=deps)
        sql = res.output.sql_query.strip().rstrip(";")
        st.subheader("Generated SQL")
        st.code(sql, language="sql")
        try:
            df: pd.DataFrame = conn.execute(sql).fetchdf()
        except Exception as e:
            st.error(f"Query failed: {e}")
            st.stop()

        # Display table
        st.subheader("Result")
        st.dataframe(df.head(ROW_LIMIT), use_container_width=True)
        st.subheader("JSON (preview)")
        preview_json = df.head(ROW_LIMIT).to_json(orient="records", date_format="iso")
        st.code(preview_json)

        # Generate NL answer from result
        with st.spinner("Summarizing answer from SQL result..."):
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

            ans = answer_agent.run_sync(prompt)
            final_answer = ans.output.final_answer


        st.subheader("Answer")
        st.markdown(final_answer)

elif ask:
    st.warning("Please enter a question before clicking Ask.")
