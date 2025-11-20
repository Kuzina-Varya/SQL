from __future__ import annotations
from typing import Optional, Sequence
import io

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config import (
    PGUSER, PGPASSWORD, PGHOST, PGPORT, PGDATABASE,
    TABLE_UNSTRUCT
)

def make_engine() -> Engine:
    url = f"postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"
    return create_engine(url, future=True)

DDL_SCHEMA = "CREATE SCHEMA IF NOT EXISTS s_psql_dds;"
DDL_UNSTRUCTURED = """
CREATE TABLE IF NOT EXISTS s_psql_dds.t_sql_source_unstructured (
    raw_id         text,
    full_name      text,
    city           text,
    segment        text,
    income         text,
    age            text,
    email          text,
    event_date     text,
    updated_at     text,
    notes          text
);
"""

def ensure_unstructured_table(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text(DDL_SCHEMA))
        conn.execute(text(DDL_UNSTRUCTURED))

_EXPECTED_COLUMNS: Sequence[str] = (
    "raw_id","full_name","city","segment","income",
    "age","email","event_date","updated_at","notes"
)

def _prepare_for_copy(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in _EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Нет колонок: {missing}")
    df = df.loc[:, list(_EXPECTED_COLUMNS)].copy()
    for col in df.columns:
        df[col] = df[col].astype(object).where(df[col].notna(), None)
        df[col] = df[col].astype(str).where(df[col].notna(), None)
    return df

def load_data_to_db(
    df: pd.DataFrame,
    table_fullname: str = TABLE_UNSTRUCT,
    engine: Optional[Engine] = None,
    ensure_table: bool = True,
) -> int:
    eng = engine or make_engine()
    if ensure_table:
        ensure_unstructured_table(eng)

    df_prepared = _prepare_for_copy(df)

    buf = io.StringIO()
    df_prepared.to_csv(buf, index=False, header=True)
    buf.seek(0)

    copy_sql = f"COPY {table_fullname} ({', '.join(_EXPECTED_COLUMNS)}) FROM STDIN WITH CSV HEADER"

    raw_conn = eng.raw_connection()
    try:
        with raw_conn.cursor() as cur:
            cur.copy_expert(copy_sql, buf)
        raw_conn.commit()
    finally:
        raw_conn.close()

    return len(df_prepared)
