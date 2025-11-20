CREATE OR REPLACE FUNCTION s_psql_dds.fn_etl_data_load(start_date date, end_date date)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  INSERT INTO s_psql_dds.t_sql_source_structured
  (raw_id, full_name, city, segment, income, age, email, event_date, updated_at, notes, is_valid)
  SELECT
    NULLIF(trim(raw_id), '')::bigint as raw_id,
    NULLIF(trim(full_name), '')      as full_name,

    CASE
      WHEN lower(regexp_replace(city, '\s+', ' ', 'g')) IN ('moscow','moskva','msc','mos0w','mos cow') THEN 'Moscow'
      WHEN lower(regexp_replace(city, '\s+', ' ', 'g')) IN ('saint-petersburg','spb','sankt-peterburg','st.petersburg','saint petersburg') THEN 'Saint-Petersburg'
      ELSE initcap(trim(city))
    END as city,

    CASE lower(trim(segment))
      WHEN 'retail' THEN 'retail'
      WHEN 'b2b'    THEN 'B2B'
      WHEN 'vip'    THEN 'VIP'
      ELSE 'other'
    END as segment,

    CASE
      WHEN (NULLIF(trim(income), '') ~ '^[+-]?\d+(\.\d+)?$') THEN
        GREATEST(0, LEAST(10000000, (NULLIF(trim(income), '')::numeric)))
      ELSE NULL
    END as income,

    CASE
      WHEN (NULLIF(trim(age), '') ~ '^\d+$') AND (NULLIF(trim(age), '')::int BETWEEN 14 AND 100)
        THEN (NULLIF(trim(age), '')::int)
      ELSE NULL
    END as age,

    CASE
      WHEN trim(email) ~* '^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$' THEN lower(trim(email))
      ELSE NULL
    END as email,

    CASE
      WHEN NULLIF(trim(event_date), '') ~ '^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$'
        THEN
          CASE
            WHEN to_date(trim(event_date), 'YYYY-MM-DD') BETWEEN start_date AND end_date
              THEN to_date(trim(event_date), 'YYYY-MM-DD')
            ELSE NULL
          END
      ELSE NULL
    END as event_date,

    CASE
      WHEN NULLIF(trim(updated_at), '') ~ '^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])\s+(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$'
        THEN to_timestamp(trim(updated_at), 'YYYY-MM-DD HH24:MI:SS')
      WHEN NULLIF(trim(updated_at), '') ~ '^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$'
        THEN to_timestamp(trim(updated_at), 'YYYY-MM-DD')
      ELSE now()
    END as updated_at,

    NULLIF(trim(notes), '') as notes,

    (
      NULLIF(trim(raw_id), '') IS NOT NULL
      AND (NULLIF(trim(full_name), '') IS NOT NULL)
    ) as is_valid

  FROM s_psql_dds.t_sql_source_unstructured src
  WHERE
    (
      CASE
        WHEN NULLIF(trim(event_date), '') ~ '^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$'
          THEN to_date(trim(event_date), 'YYYY-MM-DD') BETWEEN start_date AND end_date
        WHEN NULLIF(trim(event_date), '') IS NULL
          THEN TRUE
        ELSE FALSE
      END
    )
  ;

  -- удалим дубликаты по raw_id, оставив самую свежую запись
  WITH ranked AS (
    SELECT id, row_number() OVER (PARTITION BY raw_id ORDER BY updated_at DESC, id DESC) AS rn
    FROM s_psql_dds.t_sql_source_structured
  )
  DELETE FROM s_psql_dds.t_sql_source_structured t
  USING ranked r
  WHERE t.id = r.id AND r.rn > 1;

END;
$$;
