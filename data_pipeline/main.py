from __future__ import annotations
import argparse
from datetime import date

from gen_data import get_dataset, break_dataset
from load import make_engine, load_data_to_db
from run_etl import fill_structured_table
from config import (
    HISTORICITY, GEN_START, GEN_END, SEED_CLEAN, SEED_BREAK,
    NULL_RATE, WHITESPACE_RATE, TYPO_RATE, BAD_EMAIL_RATE,
    NEG_INCOME_RATE, HUGE_INCOME_RATE, BAD_AGE_RATE, OUT_OF_RANGE_DATE_RATE, DUPLICATE_RATE
)

def etl(
    n_rows: int = 1000,
    historicity: str = HISTORICITY,
    gen_start: str = GEN_START,
    gen_end: str = GEN_END,
    seed_clean: int = SEED_CLEAN,
    seed_break: int = SEED_BREAK,
    etl_start: str = GEN_START,
    etl_end: str = GEN_END,
    save_csv: str | None = None,
) -> None:
    # 1) генерация
    df_clean = get_dataset(
        n_rows=n_rows, historicity=historicity,
        date_from=gen_start, date_to=gen_end, seed=seed_clean
    )
    # 2) поломка
    df_broken = break_dataset(
        df_clean,
        null_rate=NULL_RATE,
        whitespace_rate=WHITESPACE_RATE,
        typo_rate=TYPO_RATE,
        bad_email_rate=BAD_EMAIL_RATE,
        negative_income_rate=NEG_INCOME_RATE,
        huge_income_rate=HUGE_INCOME_RATE,
        bad_age_rate=BAD_AGE_RATE,
        out_of_range_date_rate=OUT_OF_RANGE_DATE_RATE,
        duplicate_rate=DUPLICATE_RATE,
        seed=seed_break
    )

    if save_csv:
        df_broken.to_csv(save_csv, index=False, encoding="utf-8")
        print(f"[info] Сырой датасет сохранён → {save_csv}")

    # 3) загрузка сырца в БД
    engine = make_engine()
    rows = load_data_to_db(df_broken, engine=engine, ensure_table=True)
    print(f"[ok] В t_sql_source_unstructured загружено строк: {rows}")

    # 4) запуск SQL-функции
    fill_structured_table(
        start_date=date.fromisoformat(etl_start),
        end_date=date.fromisoformat(etl_end),
        engine=engine,
        set_search_path=True,
    )
    print("[ok] SQL-очистка завершена.")

def _cli() -> None:
    p = argparse.ArgumentParser(description="ETL: генерация → поломка → загрузка → SQL-очистка")
    p.add_argument("--rows", type=int, default=1000)
    p.add_argument("--historicity", choices=["type1", "type2"], default=HISTORICITY)
    p.add_argument("--gen-start", default=GEN_START)
    p.add_argument("--gen-end",   default=GEN_END)
    p.add_argument("--etl-start", default=GEN_START)
    p.add_argument("--etl-end",   default=GEN_END)
    p.add_argument("--save-csv",  default=None)
    args = p.parse_args()

    etl(
        n_rows=args.rows,
        historicity=args.historicity,
        gen_start=args.gen_start,
        gen_end=args.gen_end,
        etl_start=args.etl_start,
        etl_end=args.etl_end,
        save_csv=args.save_csv,
    )

if __name__ == "__main__":
    _cli()
