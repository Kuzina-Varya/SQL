# run_dm.py
from datetime import date
from run_etl import fill_dm_table
from mysql_loader import load_dm_to_mysql

if __name__ == "__main__":
    # 1. Загрузить данные в DM-схему (звезда)
    fill_dm_table(date(2024, 1, 1), date(2024, 12, 30))

    # 2. Переложить в MySQL
    PG_URL = "postgresql+psycopg2://postgres:0000@localhost:5432/etl_lab"
    load_dm_to_mysql(PG_URL)

    print(" Лабораторная работа успешно выполнена!")