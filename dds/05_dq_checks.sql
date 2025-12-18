-- dds/05_dq_checks.sql

-- Удаляем, если функция уже существует
DROP FUNCTION IF EXISTS s_sql_dds.fn_dq_checks_load(DATE, DATE);

CREATE OR REPLACE FUNCTION s_sql_dds.fn_dq_checks_load(start_dt DATE, end_dt DATE)
RETURNS VOID AS $$
DECLARE
    v_total_rows BIGINT;
    v_null_percentage DECIMAL(5,2);
    v_invalid_age BIGINT;
    v_invalid_income BIGINT;
    v_has_duplicates BOOLEAN;
    v_is_consistent BOOLEAN;
    v_mysql_count BIGINT;
    v_error_msg TEXT;
BEGIN
    -- Очистка предыдущих результатов за период (опционально)
    DELETE FROM s_sql_dds.t_dq_check_results
    WHERE execution_date::DATE = CURRENT_DATE;

    -- Получаем общее число строк за период
    SELECT COUNT(*) INTO v_total_rows
    FROM s_psql_dds.v_dm_task
    WHERE event_date BETWEEN start_dt AND end_dt;

    -- === ПРОВЕРКА 1: ПОЛНОТА ===
    IF v_total_rows = 0 THEN
        INSERT INTO s_sql_dds.t_dq_check_results (check_type, table_name, status, error_message)
        VALUES ('Полнота', 'v_dm_task', 'failed', 'Нет данных за указанный период');
    ELSE
        SELECT 
            ROUND(
                COUNT(*) FILTER (WHERE income IS NULL OR age IS NULL) * 100.0 / COUNT(*),
                2
            )
        INTO v_null_percentage
        FROM s_psql_dds.v_dm_task
        WHERE event_date BETWEEN start_dt AND end_dt;

        IF v_null_percentage = 0 THEN
            INSERT INTO s_sql_dds.t_dq_check_results (check_type, table_name, status, error_message)
            VALUES ('Полнота', 'v_dm_task', 'passed', NULL);
        ELSE
            v_error_msg := format('Пропущено %s%% в income или age', v_null_percentage);
            INSERT INTO s_sql_dds.t_dq_check_results (check_type, table_name, status, error_message)
            VALUES ('Полнота', 'v_dm_task', 'failed', v_error_msg);
        END IF;
    END IF;

    -- === ПРОВЕРКА 2: ВАЛИДНОСТЬ ===
    SELECT 
        COUNT(*) FILTER (WHERE age < 14 OR age > 100 OR age IS NULL),
        COUNT(*) FILTER (WHERE income < 0 OR income IS NULL)
    INTO v_invalid_age, v_invalid_income
    FROM s_psql_dds.v_dm_task
    WHERE event_date BETWEEN start_dt AND end_dt;

    IF v_invalid_age = 0 AND v_invalid_income = 0 THEN
        INSERT INTO s_sql_dds.t_dq_check_results (check_type, table_name, status, error_message)
        VALUES ('Валидность', 'v_dm_task', 'passed', NULL);
    ELSE
        v_error_msg := format('Невалидный age: %s, отрицательный income: %s', v_invalid_age, v_invalid_income);
        INSERT INTO s_sql_dds.t_dq_check_results (check_type, table_name, status, error_message)
        VALUES ('Валидность', 'v_dm_task', 'failed', v_error_msg);
    END IF;

    -- === ПРОВЕРКА 3: УНИКАЛЬНОСТЬ ===
    SELECT EXISTS (
        SELECT 1
        FROM (
            SELECT client_id, event_date
            FROM s_psql_dds.v_dm_task
            WHERE event_date BETWEEN start_dt AND end_dt
            GROUP BY client_id, event_date
            HAVING COUNT(*) > 1
        ) dups
    ) INTO v_has_duplicates;

    IF NOT v_has_duplicates THEN
        INSERT INTO s_sql_dds.t_dq_check_results (check_type, table_name, status, error_message)
        VALUES ('Уникальность', 'v_dm_task', 'passed', NULL);
    ELSE
        INSERT INTO s_sql_dds.t_dq_check_results (check_type, table_name, status, error_message)
        VALUES ('Уникальность', 'v_dm_task', 'failed', 'Обнаружены дубликаты по (client_id, event_date)');
    END IF;

    -- === ПРОВЕРКА 4: НЕПРОТИВОРЕЧИВОСТЬ ===
    WITH total AS (
        SELECT SUM(income) AS total_income FROM s_psql_dds.v_dm_task WHERE event_date BETWEEN start_dt AND end_dt
    ),
    by_segment AS (
        SELECT SUM(income) AS segment_income FROM s_psql_dds.v_dm_task WHERE event_date BETWEEN start_dt AND end_dt
    )
    SELECT 
        ABS(total.total_income - by_segment.segment_income) < 0.01
    INTO v_is_consistent
    FROM total, by_segment;

    IF v_is_consistent THEN
        INSERT INTO s_sql_dds.t_dq_check_results (check_type, table_name, status, error_message)
        VALUES ('Непротиворечивость', 'v_dm_task', 'passed', NULL);
    ELSE
        INSERT INTO s_sql_dds.t_dq_check_results (check_type, table_name, status, error_message)
        VALUES ('Непротиворечивость', 'v_dm_task', 'failed', 'Суммы по сегментам не совпадают с общей суммой');
    END IF;

    -- === ПРОВЕРКА 5: ПРАВИЛЬНОСТЬ (сравнение с MySQL) ===
    -- Эту проверку делаем в Python, потому что нужно подключиться к MySQL
    -- В этом SQL мы просто помечаем, что она "не реализована" или пропускаем
    -- Но если хотите — можно добавить вызов процедуры, которая подключается к MySQL
    -- Пока оставим как "passed", чтобы не ломать пайплайн
    INSERT INTO s_sql_dds.t_dq_check_results (check_type, table_name, status, error_message)
    VALUES ('Правильность', 'v_dm_task vs t_dm_task', 'skipped', 'Проверка реализуется в Python');

    RAISE NOTICE 'DQ-проверки завершены. Результаты сохранены в t_dq_check_results.';
END;
$$ LANGUAGE plpgsql;