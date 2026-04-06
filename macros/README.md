# Macros for the predictive LTV pipeline

## Common utility macros

### generate_schema_name(custom_schema_name, node)
Override default schema naming to implement:
- `stg_*` models -> `stg` schema
- `fct_*` and `dim_*` models -> `marts` schema
- other models -> default schema

### get_date_columns(table_name)
Utility to identify and cast all date/timestamp columns in a source table.
