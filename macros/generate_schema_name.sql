{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {# No custom schema specified, use default #}
        {{ default_schema }}
    {%- elif 'staging' in node.path -%}
        {# Route staging models to silver schema (Medallion trusted zone) #}
        silver
    {%- elif 'marts' in node.path -%}
        {# Route mart models to gold schema (Medallion semantic layer) #}
        gold
    {%- else -%}
        {# Default fallback to bronze for raw sources (not recommended for production) #}
        bronze
    {%- endif -%}
{%- endmacro %}
