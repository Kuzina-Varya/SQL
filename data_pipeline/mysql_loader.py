# data_pipeline/mysql_loader.py

#mysql -u root -p
#USE etl_lab;
#DESCRIBE t_dm_task;
#SELECT * FROM t_dm_task LIMIT 10;
import mysql.connector
from sqlalchemy import create_engine
import pandas as pd

def load_dm_to_mysql(
    pg_engine_str: str,
    mysql_host: str = "localhost",
    mysql_user: str = "root",
    mysql_password: str = "0000",  
    mysql_db: str = "etl_lab",
    mysql_table: str = "t_dm_task"
):
    # 1. Читаем витрину из PostgreSQL
    pg_engine = create_engine(pg_engine_str)
    df = pd.read_sql_query("SELECT * FROM s_psql_dds.v_dm_task", pg_engine)

    if df.empty:
        print(" Витрина v_dm_task пуста — перекладка не выполнена.")
        return

    # 2. Подключаемся к MySQL
    mysql_conn = mysql.connector.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password,
        database=mysql_db
    )
    cursor = mysql_conn.cursor()  # ← вот эта строка обязана быть!

    # 3. Создаём таблицу (если не существует)
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS `{mysql_table}` (
        task_id BIGINT AUTO_INCREMENT PRIMARY KEY,
        event_date DATE NOT NULL,
        client_id BIGINT,
        client_name VARCHAR(255),
        city_id BIGINT,
        city_name VARCHAR(255),
        segment_id BIGINT,
        segment_name VARCHAR(255),
        income DECIMAL(14,2) DEFAULT NULL,
        age INT DEFAULT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor.execute(create_table_sql)
    cursor.execute(f"TRUNCATE TABLE `{mysql_table}`")  # для повторного запуска

    # 4. Безопасная вставка с обработкой NULL
    insert_sql = f"""
    INSERT INTO `{mysql_table}` (
        event_date, client_id, client_name, city_id, city_name,
        segment_id, segment_name, income, age
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    def safe_val(val):
        return None if pd.isna(val) else val

    for _, row in df.iterrows():
        cursor.execute(insert_sql, (
            row['event_date'],
            safe_val(row['client_id']),
            safe_val(row['client_name']),
            safe_val(row['city_id']),
            safe_val(row['city_name']),
            safe_val(row['segment_id']),
            safe_val(row['segment_name']),
            safe_val(row['income']),
            safe_val(row['age'])
        ))

    mysql_conn.commit()
    cursor.close()
    mysql_conn.close()
    print(f" Данные переложены в MySQL таблицу `{mysql_table}` ({len(df)} строк)")