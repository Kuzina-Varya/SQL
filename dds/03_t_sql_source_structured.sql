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
