{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- elif 'stg_' in node.path -%}
        {# Route staging models to 'stg' schema #}
        stg
    {%- elif 'marts' in node.path -%}
        {# Route mart models to 'marts' schema #}
        marts
    {%- else -%}
        {# Default fallback #}
        {{ custom_schema_name | as_text }}
    {%- endif -%}
{%- endmacro %}
