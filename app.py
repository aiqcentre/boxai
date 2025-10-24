import os
import json
import duckdb
import httpx
import streamlit as st
from dataclasses import dataclass
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from dotenv import load_dotenv
import pandas as pd
from prompts import sys_prompt, answer_sys
from pathlib import Path
import re
import logfire

# ======================= Setup =======================
logfire.configure()
logfire.instrument_pydantic_ai()
load_dotenv()
st.set_page_config(page_title="Simple Ask DB", page_icon="🎬", layout="wide")

def load_css(css_path: str = "style/styles.css"):
    p = Path(css_path)
    if not p.exists():
        st.warning(f"Custom CSS not found at {css_path}. Skipping style injection.")
        return
    st.markdown(f"<style>{p.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

load_css("style/styles.css")

DB_PATH = "data/numero.duckdb"
TABLE = "films_raw"
DATA_COL = "data"
DATE_COL = "week_date"
ROW_LIMIT = 50
ANSWER_ROWS_LIMIT = 200

MODEL_NAME = "gpt-5-mini"
AGENT_SPEC = f"openai:{MODEL_NAME}"

FORBIDDEN_SQL_KEYWORDS = (
    "delete","update","insert","alter","drop","truncate","create","replace","grant","revoke",
    "attach","detach","copy","load","export","pragma","call","vacuum","set",
)
DESTRUCTIVE_INTENT_WORDS = (
    "delete","remove","drop","truncate","update","insert","modify","change","alter","create",
    "add column","erase",
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

# ======================= DB =======================
@st.cache_resource
def get_conn(path: str):
    return duckdb.connect(path, read_only=True)

conn = get_conn(DB_PATH)

# ======================= SQL Agent =======================
class SQLResult(BaseModel):
    sql_query: str = Field(..., description="A valid DuckDB SELECT query")

@dataclass
class Deps:
    conn: duckdb.DuckDBPyConnection

sql_agent = Agent[Deps, SQLResult](AGENT_SPEC, output_type=SQLResult, deps_type=Deps)

@sql_agent.system_prompt
async def sql_system_prompt() -> str:
    base = sys_prompt(TABLE, DATA_COL, DATE_COL)
    guard = (
        "\n\nCRITICAL RULES:\n"
        "- Only generate a single-statement SELECT (optionally WITH ... SELECT).\n"
        "- Never use DELETE/UPDATE/INSERT/ALTER/DROP/TRUNCATE/CREATE/PRAGMA/etc.\n"
        "- If the user asks to delete/modify/create data, do NOT comply; still output a harmless\n"
        "  SELECT like: SELECT 'refused' AS message WHERE 1=0.\n"
    )
    return base + guard

# ======================= NL Answer Agent =======================
class AnswerOut(BaseModel):
    final_answer: str = Field(
        ..., description="Natural-language answer based strictly on provided rows"
    )

answer_agent = Agent[None, AnswerOut](AGENT_SPEC, output_type=AnswerOut)

@answer_agent.system_prompt
async def sql_to_nl_prompt() -> str:
    return answer_sys()

# ======================= README-based Endpoint Loading =======================
README_PATH = os.getenv("README_FILE", "README.md")

def _load_endpoints_from_readme(readme_path: str) -> Dict[str, Dict[str, str]]:
    """
    Read README.md and extract endpoints from marked sections:
        <!-- AU_DATA_START --> ... <!-- AU_DATA_END -->
        <!-- PREDICT_DATA_START --> ... <!-- PREDICT_DATA_END -->
    Returns dict with 'au' and 'predict' keys containing endpoint mappings.
    """
    p = Path(readme_path)
    if not p.exists():
        raise FileNotFoundError(f"README not found at {readme_path}")

    text = p.read_text(encoding="utf-8", errors="ignore")

    # Extract AU endpoints
    au_block = re.search(
        r"<!--\s*AU_DATA_START\s*-->(?P<body>.*)<!--\s*AU_DATA_END\s*-->",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    
    # Extract PREDICT endpoints
    predict_block = re.search(
        r"<!--\s*PREDICT_DATA_START\s*-->(?P<body>.*)<!--\s*PREDICT_DATA_END\s*-->",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    endpoints = {"au": {}, "predict": {}}

    # Parse AU endpoints
    if au_block:
        body = au_block.group("body")
        urls = re.findall(r"https?://[^\s]+/au/[^\s]+", body)
        for u in urls:
            if re.search(r"/au/states(?:\b|/|\?|#)", u):
                endpoints["au"]["states"] = u.split("?")[0]
            elif re.search(r"/au/capital(?:\b|/|\?|#)", u):
                endpoints["au"]["capital"] = u.split("?")[0]
            elif re.search(r"/au/cities(?:\b|/|\?|#)", u):
                endpoints["au"]["cities"] = u.split("?")[0]
            elif re.search(r"/au/state-of-city(?:\b|/|\?|#)", u):
                endpoints["au"]["state_of_city"] = u.split("?")[0]

    # Parse PREDICT endpoints
    if predict_block:
        body = predict_block.group("body")
        urls = re.findall(r"https?://[^\s]+", body)
        for u in urls:
            if re.search(r"/predict1(?:\b|/|\?|#)", u):
                endpoints["predict"]["predict1"] = u.split("?")[0]
            elif re.search(r"/predict2(?:\b|/|\?|#)", u):
                endpoints["predict"]["predict2"] = u.split("?")[0]
            elif re.search(r"/$", u) or re.search(r"films-predict-app", u):
                endpoints["predict"]["base"] = u.rstrip("/")

    return endpoints

try:
    ALL_ENDPOINTS = _load_endpoints_from_readme(README_PATH)
    AU_ENDPOINTS = ALL_ENDPOINTS.get("au", {})
    PREDICT_ENDPOINTS = ALL_ENDPOINTS.get("predict", {})
    ENDPOINTS_ERROR = None
except Exception as e:
    ALL_ENDPOINTS = None
    AU_ENDPOINTS = None
    PREDICT_ENDPOINTS = None
    ENDPOINTS_ERROR = e

# ======================= HTTP Helper =======================
def _get_json(full_url: str, params: Dict[str, Any] | None = None) -> Dict | List:
    """GET request -> JSON"""
    with httpx.Client(timeout=15.0) as client:
        r = client.get(full_url, params=params)
        r.raise_for_status()
        return r.json()

def _post_json(full_url: str, payload: Dict[str, Any]) -> Dict:
    """POST request with JSON payload -> JSON"""
    with httpx.Client(timeout=15.0) as client:
        r = client.post(full_url, json=payload)
        r.raise_for_status()
        return r.json()

# ======================= AU Tools =======================
AU_HINTS: tuple[str, ...] = (
    "australia","australian","state","states","territory","territories","capital","city","cities",
)

def is_au_query(q: str) -> bool:
    ql = q.lower()
    return any(h in ql for h in AU_HINTS)

def _ensure_au_ready():
    if not AU_ENDPOINTS:
        raise RuntimeError(f"AU endpoints not loaded: {ENDPOINTS_ERROR}")

def au_list_states() -> List[str]:
    _ensure_au_ready()
    data = _get_json(AU_ENDPOINTS["states"])
    if isinstance(data, dict) and "states" in data:
        return [str(x) for x in data["states"]]
    if isinstance(data, list):
        return [str(x) for x in data]
    return [str(data)]

def au_capital_of(state: str) -> str:
    _ensure_au_ready()
    data = _get_json(AU_ENDPOINTS["capital"], params={"state": state})
    if isinstance(data, dict):
        if "capital" in data:
            return str(data["capital"])
        if "result" in data:
            return str(data["result"])
    return str(data)

def au_cities_in(state: str) -> List[str]:
    _ensure_au_ready()
    data = _get_json(AU_ENDPOINTS["cities"], params={"state": state})
    if isinstance(data, dict) and "cities" in data:
        return [str(x) for x in data["cities"]]
    if isinstance(data, list):
        return [str(x) for x in data]
    return [str(data)]

def au_state_of_city(city: str) -> str:
    _ensure_au_ready()
    data = _get_json(AU_ENDPOINTS["state_of_city"], params={"city": city})
    if isinstance(data, dict):
        if "state" in data:
            return str(data["state"])
        if "result" in data:
            return str(data["result"])
    return str(data)

au_agent = Agent(
    AGENT_SPEC,
    system_prompt=(
        "You answer Australian city/state questions strictly using tools:\n"
        "- au_list_states\n- au_capital_of\n- au_cities_in\n- au_state_of_city\n\n"
        "Be concise and factual."
    ),
)

@au_agent.tool_plain
def au_list_states_tool():
    """Tool: list all states/territories."""
    return au_list_states()

@au_agent.tool_plain
def au_capital_of_tool(state: str):
    """Tool: capital city of a given state/territory."""
    return au_capital_of(state)

@au_agent.tool_plain
def au_cities_in_tool(state: str):
    """Tool: list cities in a given state/territory."""
    return au_cities_in(state)

@au_agent.tool_plain
def au_state_of_city_tool(city: str):
    """Tool: which state/territory a city belongs to."""
    return au_state_of_city(city)

# ======================= PREDICT Tools =======================
PREDICT_HINTS: tuple[str, ...] = (
    "predict","prediction","forecast","estimate",
    "box office","final total","week 1","wk1",
)

def is_predict_query(q: str) -> bool:
    ql = q.lower()
    return any(h in ql for h in PREDICT_HINTS)

def _ensure_predict_ready():
    if not PREDICT_ENDPOINTS:
        raise RuntimeError(f"PREDICT endpoints not loaded: {ENDPOINTS_ERROR}")

def predict_week1_gross(censor_rating: str, distributor_name: str, week_date: str, concurrent_films: List = None) -> float:
    """Predict week 1 gross using /predict1 endpoint"""
    _ensure_predict_ready()
    payload = {
        "censorRating": censor_rating,  
        "distributorName": distributor_name,  
        "week_date": week_date,
        "concurrent_films": concurrent_films or []
    }
    data = _post_json(PREDICT_ENDPOINTS["predict1"], payload)
    return data.get("predicted_gross", 0.0)

def predict_final_total(wk1_total: float) -> float:
    """Predict final total gross from week 1 gross using /predict2 endpoint"""
    _ensure_predict_ready()
    payload = {"wk1_total": wk1_total}
    data = _post_json(PREDICT_ENDPOINTS["predict2"], payload)
    return data.get("predicted_gross", 0.0)

predict_agent = Agent(
    AGENT_SPEC,
    system_prompt=(
        "You are a box office prediction assistant. Use these tools:\n\n"
        "- predict_week1_gross_tool(censor_rating, distributor_name, week_date, concurrent_films=[]): "
        "Predict first week gross. MUST provide all 4 parameters. concurrent_films defaults to empty list.\n"
        "- predict_final_total_tool(wk1_total): Predict final total from week 1 gross.\n"
        "- execute_sql_query(query_description): Query the database for film information.\n\n"
        "For prediction queries:\n"
        "1. If user asks to predict for a specific film, first query the database to get film details\n"
        "2. Use the retrieved data (censorRating, distributorName, releaseDate) to make predictions\n"
        "3. ALWAYS pass concurrent_films=[] (empty list) when calling predict_week1_gross_tool\n"
        "4. Provide clear, formatted answers with both predicted values and context\n\n"
        "Always explain what you're doing and format numbers as currency when appropriate."
    ),
    deps_type=Deps,
)

@predict_agent.tool_plain
def predict_week1_gross_tool(censorRating: str, distributorName: str, week_date: str, concurrent_films: list = None):
    """Tool: Predict week 1 box office gross for a film.
    
    Args:
        censorRating: Film censor rating (e.g., 'G', 'PG', 'M', 'MA15+', 'R18+')
        distributorName: Name of the distributor (e.g., 'Disney', 'Universal Pictures', 'Warner Bros')
        week_date: Release week date in YYYY-MM-DD format (e.g., '2024-06-15')
        concurrent_films: List of concurrent films with their features (default: empty list [])
    
    Returns:
        str: Formatted prediction result with currency
    """
    if concurrent_films is None:
        concurrent_films = []
    result = predict_week1_gross(censorRating, distributorName, week_date, concurrent_films)
    return f"Predicted Week 1 Gross: ${result:,.2f}"

@predict_agent.tool_plain
def predict_final_total_tool(wk1_total: float):
    """Tool: Predict final total gross from week 1 gross."""
    result = predict_final_total(wk1_total)
    return f"Predicted Final Total: ${result:,.2f}"

@predict_agent.tool
def execute_sql_query(ctx, query_description: str) -> str:
    """Tool: Execute SQL query to get film data from database."""
    try:
        # Generate SQL from description
        sql_res = sql_agent.run_sync(query_description, deps=ctx.deps)
        sql = sql_res.output.sql_query.strip().rstrip(";")
        
        if not is_select_only(sql):
            return "Error: Cannot execute non-SELECT queries"
        
        # Execute query
        df = ctx.deps.conn.execute(sql).fetchdf()
        
        if len(df) == 0:
            return "No data found for the query"
        
        # Return as JSON string
        return df.head(10).to_json(orient="records", date_format="iso")
    except Exception as e:
        return f"Error executing query: {str(e)}"

# ======================= UI =======================
st.title("🎬 Film Analytics & Prediction ChatBot")
st.caption("Ask about films, Australian cities/states, or make box office predictions!")

with st.form("ask_form", clear_on_submit=False):
    question = st.text_input(
        "Question",
        placeholder="Examples: top 5 films by weekend gross · predict gross for Avatar · capital of Queensland",
    )
    ask = st.form_submit_button("Ask", type="primary")

if ask:
    if not question.strip():
        st.warning("Please enter a question before clicking Ask.")
        st.stop()

    sql = "(n/a)"
    df = pd.DataFrame()
    final_answer = ""

    # ---------- PREDICT branch ----------
    if is_predict_query(question):
        with st.spinner("Making prediction..."):
            try:
                deps = Deps(conn=conn)
                predict_res = predict_agent.run_sync(question, deps=deps)
                final_answer = str(predict_res.output if hasattr(predict_res, 'output') else predict_res)
            except Exception as e:
                st.error(f"Prediction failed: {e}")
                st.stop()

    # ---------- AU branch ----------
    elif is_au_query(question):
        with st.spinner("Answering from AU City/State data..."):
            try:
                au_res = au_agent.run_sync(question)
                out = getattr(au_res, "output", au_res)
                if isinstance(out, list):
                    final_answer = ", ".join(map(str, out))
                elif isinstance(out, dict):
                    final_answer = json.dumps(out, ensure_ascii=False)
                else:
                    final_answer = str(out)
            except Exception as e:
                st.error(f"AU query failed: {e}")
                st.stop()

    # ---------- Standard SQL query ----------
    else:
        if is_user_intent_destructive(question):
            st.error("Sorry, I can't delete or modify data. This app is read-only.")
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
                st.error("Blocked a non-SELECT or potentially destructive SQL.")
                st.subheader("Generated (blocked) SQL")
                st.code(sql, language="sql")
                st.stop()

            try:
                df = conn.execute(sql).fetchdf()
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
                f"QUESTION:\n{question}\n\n"
                f"ROW_COUNT: {row_count}\n"
                f"COLUMNS: {columns}\n"
                "SQL RESULT ROWS (JSON array of objects):\n"
                f"{json.dumps(rows_for_llm, ensure_ascii=False)}"
            )
            try:
                ans = answer_agent.run_sync(prompt)
                final_answer = ans.output.final_answer
            except Exception as e:
                final_answer = f"Could not summarize result. Error: {e}"

    # ====== Output ======
    st.markdown(f"#### 🧠 Answer to: *{question}*")
    tab1, tab2, tab3, tab4 = st.tabs(["🧾 Answer", "🧮 SQL", "📊 Table", "🧱 JSON"])

    with tab1:
        st.markdown(
            f"<div class='card' style='color:#9333ea; font-weight:500;'>{final_answer}</div>",
            unsafe_allow_html=True,
        )
    with tab2:
        st.code(sql, language="sql")
    with tab3:
        st.caption(f"{len(df)} rows • showing up to {min(len(df), ROW_LIMIT)}")
        if len(df) > 0:
            st.dataframe(df.head(ROW_LIMIT), use_container_width=True)
            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    "Download CSV",
                    df.to_csv(index=False).encode("utf-8"),
                    file_name="query_result.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with c2:
                st.download_button(
                    "Download JSON",
                    df.to_json(orient="records", date_format="iso"),
                    file_name="query_result.json",
                    mime="application/json",
                    use_container_width=True,
                )
        else:
            st.info("No table data for this query type.")

    with tab4:
        preview_json = df.head(ROW_LIMIT).to_json(orient="records", date_format="iso") if len(df) > 0 else "{}"
        st.code(preview_json, language="json")