import streamlit as st
import duckdb
import pandas as pd
import json

DB_PATH = 'src/data/numero.duckdb'
st.title('DuckDB Viewer')

# Connect to DuckDB and get table names
def get_tables():
    with duckdb.connect(DB_PATH) as con:
        tables = con.execute("SHOW TABLES").fetchall()
    return [t[0] for t in tables]

table = get_tables()[0]
# Query data
def get_data(table, limit=100):
    with duckdb.connect(DB_PATH) as con:
        df = con.execute(f"SELECT * FROM {table}").df()
    return df

df = get_data(table)

# Identify JSON columns (by sampling)
def is_json(val):
    if not isinstance(val, str):
        return False
    try:
        json.loads(val)
        return True
    except Exception:
        return False

json_cols = []
if not df.empty:
    for col in df.columns:
        if df[col].apply(is_json).any():
            json_cols.append(col)
# --- ML Table Transformation ---
st.header('Machine Learning Data Table')

if json_cols:
    st.write(f"Detected JSON columns: {', '.join(json_cols)}")
    flat_df = df.copy()
    for col in json_cols:
        try:
            # Parse JSON column
            parsed = flat_df[col].dropna().apply(lambda x: json.loads(x))
            first_val = parsed.iloc[0] if not parsed.empty else None
            # If the JSON is a dict with a key containing a list (e.g., {'films': [...]})
            if isinstance(first_val, dict) and any(isinstance(v, list) for v in first_val.values()):
                # Find the key with a list value
                list_key = next(k for k, v in first_val.items() if isinstance(v, list))
                # Explode the list
                flat_df[list_key] = parsed.apply(lambda d: d.get(list_key, []) if isinstance(d, dict) else [])
                flat_df = flat_df.explode(list_key)
                # Flatten the dicts inside the list
                flat_df = flat_df.reset_index(drop=True)
                json_expanded = pd.json_normalize(flat_df[list_key])
                json_expanded.columns = [f"{col}.{list_key}.{subcol}" for subcol in json_expanded.columns]
                flat_df = flat_df.drop(columns=[col, list_key]).join(json_expanded)
        except Exception as e:
            st.warning(f"Could not flatten column {col}: {e}")
    st.dataframe(flat_df)
    csv = flat_df.to_csv(index=False).encode('utf-8')
    st.download_button('Download ML Table as CSV', csv, file_name='ml_table.csv', mime='text/csv')
else:
    st.dataframe(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button('Download Table as CSV', csv, file_name='table.csv', mime='text/csv')

st.caption('Powered by Streamlit, DuckDB, and Pandas')
print(flat_df.head())  # For debugging purposes