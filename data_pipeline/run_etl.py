from __future__ import annotations
from typing import Optional
from datetime import date
import argparse

from sqlalchemy import text
from sqlalchemy.engine import Engine
from pathlib import Path

from load import make_engine
from config import TABLE_STRUCT

DDL_SCHEMA = "CREATE SCHEMA IF NOT EXISTS s_psql_dds;"
DDL_STRUCTURED = """
CREATE TABLE IF NOT EXISTS s_psql_dds.t_sql_source_structured (
    id            bigserial PRIMARY KEY,
    raw_id        bigint,
    full_name     text,
    city          text,
    segment       text,
    income        numeric(14,2),
    age           int,
    email         text,
    event_date    date,
    updated_at    timestamp,
    notes         text,
    is_valid      boolean DEFAULT true,
    load_dttm     timestamp DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_struct_rawid ON s_psql_dds.t_sql_source_structured(raw_id);
"""

def _parse_date(s: str) -> date:
    try:
        return date.fromisoformat(s)
    except Exception as e:
        raise argparse.ArgumentTypeError(f"Неверная дата '{s}', нужен формат YYYY-MM-DD") from e

def fill_structured_table(
    start_date: date,
    end_date: date,
    engine: Optional[Engine] = None,
    set_search_path: bool = True,
) -> None:
    eng = engine or make_engine()
    with eng.begin() as conn:
        if set_search_path:
            conn.execute(text("SET search_path TO s_psql_dds, public"))

        # гарантируем наличие схемы/таблицы
        conn.execute(text(DDL_SCHEMA))
        conn.execute(text(DDL_STRUCTURED))

        # гарантируем наличие функции: читаем и выполняем SQL-скрипт
        sql_fn_path = Path(__file__).resolve().parent.parent / "dds" / "fn_etl_data_load.sql"
        sql_fn = sql_fn_path.read_text(encoding="utf-8").replace('%', '%%')
        conn.exec_driver_sql(sql_fn)


        before = conn.execute(text(f"SELECT count(*) FROM {TABLE_STRUCT}")).scalar_one_or_none() or 0

        conn.execute(
            text("SELECT s_psql_dds.fn_etl_data_load(:start_date, :end_date)"),
            {"start_date": start_date, "end_date": end_date},
        )

        after = conn.execute(text(f"SELECT count(*) FROM {TABLE_STRUCT}")).scalar_one_or_none() or 0

    print(f"[OK] fn_etl_data_load: добавлено {after - before} строк (было {before} → стало {after}).")

def main() -> None:
    p = argparse.ArgumentParser(description="Запуск SQL-ETL (очистка и загрузка в structured)")
    p.add_argument("--start", required=True, type=_parse_date)
    p.add_argument("--end",   required=True, type=_parse_date)
    args = p.parse_args()

    fill_structured_table(args.start, args.end)

if __name__ == "__main__":
    main()
