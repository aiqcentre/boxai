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
import httpx
import logfire
from pathlib import Path
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

# sau set_page_config(...)
st.set_page_config(page_title="Simple Ask DB", page_icon="🎬", layout="wide")
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

# ======================= AU Tooling (API-backed, NO DEFAULTS) =======================
# App only reads endpoints from README.md via regex markers. No hardcoded defaults.

AU_HINTS: tuple[str, ...] = (
    "australia","australian","state","states","territory","territories","capital","city","cities",
)
def is_au_query(q: str) -> bool:
    ql = q.lower()
    return any(h in ql for h in AU_HINTS)
README_PATH = os.getenv("AU_README_FILE", "README.md")

def _load_au_endpoints_from_readme(readme_path: str) -> Dict[str, str]:
    """
    Read README.md and extract all AU endpoints between the markers:
        <!-- AU_DATA_START --> ... <!-- AU_DATA_END -->
    Returns a dict with keys: states, capital, cities, state_of_city.
    Raises ValueError if markers or required endpoints are missing.
    """
    p = Path(readme_path)
    if not p.exists():
        raise FileNotFoundError(
            f"README not found at {readme_path}. Set AU_README_FILE env or place README.md in project root."
        )

    text = p.read_text(encoding="utf-8", errors="ignore")

    block = re.search(
        r"<!--\s*AU_DATA_START\s*-->(?P<body>.*)<!--\s*AU_DATA_END\s*-->",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not block:
        raise ValueError(
            "AU endpoints block not found. Please add markers:\n"
            "<!-- AU_DATA_START --> ... <!-- AU_DATA_END --> in README.md"
        )

    body = block.group("body")
    urls = re.findall(r"https?://[^\s]+/au/[^\s]+", body)

    endpoints: Dict[str, str] = {}
    for u in urls:
        if re.search(r"/au/states(?:\b|/|\?|#)", u):
            endpoints["states"] = u.split("?")[0]
        elif re.search(r"/au/capital(?:\b|/|\?|#)", u):
            endpoints["capital"] = u.split("?")[0]
        elif re.search(r"/au/cities(?:\b|/|\?|#)", u):
            endpoints["cities"] = u.split("?")[0]
        elif re.search(r"/au/state-of-city(?:\b|/|\?|#)", u):
            endpoints["state_of_city"] = u.split("?")[0]

    missing = [k for k in ("states","capital","cities","state_of_city") if k not in endpoints]
    if missing:
        raise ValueError(
            "README is missing required AU endpoints: " + ", ".join(missing) +
            "\nMake sure the block includes these 4 URLs (any order) between the markers."
        )

    return endpoints

try:
    AU_ENDPOINTS = _load_au_endpoints_from_readme(README_PATH)
except Exception as e:
    AU_ENDPOINTS = None
    AU_ENDPOINTS_ERROR = e
else:
    AU_ENDPOINTS_ERROR = None
def _get_json_full_url(full_url: str, params: Dict[str, Any] | None = None) -> Dict | List:
    """GET full URL -> JSON; raise on HTTP errors."""
    with httpx.Client(timeout=10.0) as client:
        r = client.get(full_url, params=params)
        r.raise_for_status()
        return r.json()

# ---------- Plain funcs (tools will call) ----------
def _ensure_endpoints_ready():
    if AU_ENDPOINTS is None:
        raise RuntimeError(
            f"AU endpoints are not loaded: {AU_ENDPOINTS_ERROR}. "
            "Please fix README.md markers/URLs and restart the app."
        )

def au_list_states() -> List[str]:
    _ensure_endpoints_ready()
    data = _get_json_full_url(AU_ENDPOINTS["states"])
    if isinstance(data, dict) and "states" in data:
        return [str(x) for x in data["states"]]
    if isinstance(data, list):
        return [str(x) for x in data]
    return [str(data)]

def au_capital_of(state: str) -> str:
    _ensure_endpoints_ready()
    data = _get_json_full_url(AU_ENDPOINTS["capital"], params={"state": state})
    if isinstance(data, dict):
        if "capital" in data:
            return str(data["capital"])
        if "result" in data:
            return str(data["result"])
    return str(data)

def au_cities_in(state: str) -> List[str]:
    _ensure_endpoints_ready()
    data = _get_json_full_url(AU_ENDPOINTS["cities"], params={"state": state})
    if isinstance(data, dict) and "cities" in data:
        return [str(x) for x in data["cities"]]
    if isinstance(data, list):
        return [str(x) for x in data]
    return [str(data)]

def au_state_of_city(city: str) -> str:
    _ensure_endpoints_ready()
    data = _get_json_full_url(AU_ENDPOINTS["state_of_city"], params={"city": city})
    if isinstance(data, dict):
        if "state" in data:
            return str(data["state"])
        if "result" in data:
            return str(data["result"])
    return str(data)

# ---------- AU agent + tools ----------
au_agent = Agent(
    AGENT_SPEC,
    system_prompt=(
        "You answer Australian city/state questions strictly using tools:\n"
        "- au_list_states\n- au_capital_of\n- au_cities_in\n- au_state_of_city\n\n"
        "Be concise and factual. If a state/territory/city is not found, say so plainly."
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

# ---------- AU agent + tools ----------
au_agent = Agent(
    AGENT_SPEC,
    system_prompt=(
        "You answer Australian city/state questions strictly using tools:\n"
        "- au_list_states\n- au_capital_of\n- au_cities_in\n- au_state_of_city\n\n"
        "Be concise and factual. If a state/territory/city is not found, say so plainly."
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


# ======================= UI =======================
st.title("🎬 Simple ChatBot NL → SQL → Answer")
st.caption("Ask dataset questions (SQL), or ask Australian city/state questions (tool-powered).")

with st.form("ask_form", clear_on_submit=False):
    question = st.text_input(
        "Question",
        placeholder="Examples: top 5 films by weekend gross in July 2023 · Capital of Queensland",
    )
    ask = st.form_submit_button("Ask", type="primary")

if ask:
    if not question.strip():
        st.warning("Please enter a question before clicking Ask.")
        st.stop()

    # ---------- AU tool branch ----------
    if is_au_query(question):
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
                sql = "(n/a for AU tool)"
                df = pd.DataFrame()
            except Exception as e:
                st.error(f"AU tool failed: {e}")
                st.stop()

    # ---------- NL → SQL pipeline ----------
    else:
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
            st.info("No table to display for AU tool queries.")

    with tab4:
        preview_json = df.head(ROW_LIMIT).to_json(orient="records", date_format="iso")
        st.code(preview_json, language="json")
