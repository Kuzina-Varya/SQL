# run_dm.py

from datetime import date
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

# Импортируем из той же папки
from mysql_loader import load_dm_to_mysql

# Добавляем корень проекта в путь
project_root = Path(__file__).resolve().parent.parent
import sys
sys.path.append(str(project_root))

from run_etl import fill_dm_table

if __name__ == "__main__":
    # 1. Заполнить DM-слой
    fill_dm_table(date(2024, 1, 1), date(2024, 12, 31))
    
    # 2. Перенести в MySQL
    PG_URL = "postgresql+psycopg2://postgres:0000@localhost:5432/etl_lab"
    load_dm_to_mysql(PG_URL)
    
    # 3. ЗАПУСК DQ-ПРОВЕРОК
    engine = create_engine(PG_URL)
    with engine.begin() as conn:
        dq_sql_path = project_root / "dds" / "05_dq_checks.sql"
        dq_sql = dq_sql_path.read_text(encoding="utf-8")
        conn.execute(text(dq_sql))
        conn.execute(text("SELECT s_sql_dds.fn_dq_checks_load(:start_dt, :end_dt);"), {
            "start_dt": date(2024, 1, 1),
            "end_dt": date(2024, 12, 31)
        })
    
    # 4. ПРОВЕРКА 5: ПРАВИЛЬНОСТЬ (PostgreSQL ↔ MySQL)
    print(" Проверка правильности: сравнение количества строк...")
    
    # Подключаемся к PostgreSQL
    pg_engine = create_engine(PG_URL)
    
    # Подключаемся к MySQL
    mysql_url = "mysql+mysqlconnector://root:0000@localhost:3306/etl_lab"
    mysql_engine = create_engine(mysql_url)
    
    # 1. Прочитать количество строк из PostgreSQL
    pg_count = pd.read_sql_query("SELECT COUNT(*) AS cnt FROM s_psql_dds.v_dm_task", pg_engine).iloc[0, 0]
    
    # 2. Прочитать количество строк из MySQL
    mysql_count = pd.read_sql_query("SELECT COUNT(*) AS cnt FROM t_dm_task", mysql_engine).iloc[0, 0]
    
    # 3. Сравнить и сохранить результат в PostgreSQL
    status = 'passed' if pg_count == mysql_count else 'failed'
    error_msg = None if status == 'passed' else f"PostgreSQL: {pg_count}, MySQL: {mysql_count}"
    
    # Вставить в таблицу DQ-результатов
    with pg_engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO s_sql_dds.t_dq_check_results (check_type, table_name, status, error_message)
            VALUES ('Правильность', 'v_dm_task vs t_dm_task', :status, :error_msg)
        """), {"status": status, "error_msg": error_msg})
    
    print(f"Проверка правильности завершена. Статус: {status}")
    print(" Лабораторная работа №3 (DQ) успешно выполнена!")