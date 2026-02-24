--dds/lab3.sql
-- Создаём схему, если не существует
CREATE SCHEMA IF NOT EXISTS s_sql_dds;

-- Удаляем старую таблицу (если есть)
DROP TABLE IF EXISTS s_sql_dds.t_dq_check_results;

-- Создаём таблицу для хранения результатов DQ-проверок
CREATE TABLE s_sql_dds.t_dq_check_results (
  check_id SERIAL PRIMARY KEY,
  check_type VARCHAR(100) NOT NULL,      -- например: "Полнота", "Валидность"
  table_name VARCHAR(100) NOT NULL,      -- имя таблицы или витрины
  execution_date TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP,
  status VARCHAR(20) NOT NULL,           -- 'passed', 'failed', 'error'
  error_message TEXT                     -- детали ошибки
);



--проверка
SELECT 
    check_type AS "Тип проверки",
    status AS "Статус",
    error_message AS "Описание ошибки",
    execution_date AS "Время выполнения"
FROM s_sql_dds.t_dq_check_results
ORDER BY execution_date DESC;


SELECT * FROM s_sql_dds.t_dq_check_results;