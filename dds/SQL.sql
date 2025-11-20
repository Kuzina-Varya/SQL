SELECT schema_name FROM information_schema.schemata WHERE schema_name='s_psql_dds';
SELECT COUNT(*) FROM s_psql_dds.t_sql_source_unstructured;
SELECT COUNT(*) FROM s_psql_dds.t_sql_source_structured;
SELECT * FROM s_psql_dds.t_sql_source_unstructured;
SELECT * FROM s_psql_dds.t_sql_source_structured;