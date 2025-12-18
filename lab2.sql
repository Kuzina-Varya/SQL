SELECT MIN(event_date), MAX(event_date)
FROM s_psql_dds.t_sql_source_structured
WHERE is_valid = true 
  AND event_date IS NOT NULL;

-- Сколько строк в фактах?
SELECT COUNT(*) FROM s_psql_dds.t_dm_task;

-- Показать первую строку из витрины
SELECT * FROM s_psql_dds.v_dm_task LIMIT 1;


-- Удалите старую
DROP FUNCTION IF EXISTS s_psql_dds.fn_etl_data_load(date, date);


-- Удаляем всю схему целиком (вместе со всеми таблицами, функциями, витринами)
DROP SCHEMA IF EXISTS s_psql_dds CASCADE;

-- Пересоздаём схему пустой
CREATE SCHEMA s_psql_dds;
