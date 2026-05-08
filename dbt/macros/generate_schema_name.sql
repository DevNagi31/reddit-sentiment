{# Use the model's configured `schema:` verbatim instead of dbt's default
   `<target>_<schema>` (which would give us `main_marts` etc.). #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
