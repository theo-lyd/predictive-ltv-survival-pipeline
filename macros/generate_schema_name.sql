{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if 'staging' in node.path or 'intermediate' in node.path -%}
        {# Route staging models to silver schema (Medallion trusted zone) #}
        silver
    {%- elif 'marts' in node.path -%}
        {# Route mart models to gold schema (Medallion semantic layer) #}
        gold
    {%- elif custom_schema_name is none -%}
        {# No custom schema specified, use default #}
        {{ default_schema }}
    {%- else -%}
        {# Default fallback to bronze for raw sources (not recommended for production) #}
        bronze
    {%- endif -%}
{%- endmacro %}
