-- dds/04_dm_star_schema.sql

-- 1. Справочники
CREATE TABLE IF NOT EXISTS s_psql_dds.d_client (
    id BIGSERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS s_psql_dds.d_city (
    id BIGSERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS s_psql_dds.d_segment (
    id BIGSERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- 2. Таблица фактов 
CREATE TABLE IF NOT EXISTS s_psql_dds.t_dm_task (
    id BIGSERIAL PRIMARY KEY,
    event_date DATE NOT NULL,
    client_id BIGINT NOT NULL,
    city_id BIGINT NOT NULL,
    segment_id BIGINT NOT NULL,
    income NUMERIC(14,2),
    age INT,
    CONSTRAINT fk_client FOREIGN KEY (client_id) REFERENCES s_psql_dds.d_client(id),
    CONSTRAINT fk_city FOREIGN KEY (city_id) REFERENCES s_psql_dds.d_city(id),
    CONSTRAINT fk_segment FOREIGN KEY (segment_id) REFERENCES s_psql_dds.d_segment(id)
);

-- 3. Функция загрузки данных
CREATE OR REPLACE FUNCTION s_psql_dds.fn_dm_data_load(start_dt DATE, end_dt DATE)
RETURNS VOID AS $$
BEGIN
    -- Вставляем только валидные, очищенные записи
    INSERT INTO s_psql_dds.t_dm_task (
        event_date,
        client_id,
        city_id,
        segment_id,
        income,
        age
    )
    SELECT
        s.event_date,
        c.id AS client_id,
        ci.id AS city_id,
        seg.id AS segment_id,
        s.income,
        s.age
    FROM s_psql_dds.t_sql_source_structured s
    JOIN s_psql_dds.d_client c ON c.name = s.full_name
    JOIN s_psql_dds.d_city ci ON ci.name = s.city
    JOIN s_psql_dds.d_segment seg ON seg.name = s.segment
    WHERE
        s.is_valid = true
        AND s.event_date >= start_dt
        AND s.event_date <= end_dt
        AND s.full_name IS NOT NULL
        AND s.city IS NOT NULL
        AND s.segment IS NOT NULL
        AND s.event_date IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- 4. Представление (витрина)
CREATE OR REPLACE VIEW s_psql_dds.v_dm_task AS
SELECT
    t.id AS task_id,
    t.event_date,
    t.client_id,
    c.name AS client_name,
    t.city_id,
    ci.name AS city_name,
    t.segment_id,
    seg.name AS segment_name,
    t.income,
    t.age
FROM s_psql_dds.t_dm_task t
JOIN s_psql_dds.d_client c ON t.client_id = c.id
JOIN s_psql_dds.d_city ci ON t.city_id = ci.id
JOIN s_psql_dds.d_segment seg ON t.segment_id = seg.id;