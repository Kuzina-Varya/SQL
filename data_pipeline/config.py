from __future__ import annotations


# ==== Postgres (читаем из переменных окружения или даём дефолты) ====
PGUSER = "postgres"
PGPASSWORD = "0000"
PGHOST = "localhost"
PGPORT =  "5432"
PGDATABASE =  "etl_lab"

SCHEMA = "s_psql_dds"
TABLE_UNSTRUCT = f"{SCHEMA}.t_sql_source_unstructured"
TABLE_STRUCT   = f"{SCHEMA}.t_sql_source_structured"

# ==== Параметры генерации (дефолты, можно менять) ====
SEED_CLEAN = int("42")
SEED_BREAK = int( "43")
HISTORICITY = "type2" # 'type1' | 'type2'
GEN_START =  "2024-01-01"
GEN_END   =  "2024-12-31"

# ==== Доли «поломок» по умолчанию ====
NULL_RATE = float( "0.05")
WHITESPACE_RATE = float( "0.10")
TYPO_RATE = float( "0.05")
BAD_EMAIL_RATE = float( "0.05")
NEG_INCOME_RATE = float( "0.02")
HUGE_INCOME_RATE = float( "0.02")
BAD_AGE_RATE = float( "0.03")
OUT_OF_RANGE_DATE_RATE = float( "0.04")
DUPLICATE_RATE = float( "0.05")
