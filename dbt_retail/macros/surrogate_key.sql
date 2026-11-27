{% macro surrogate_key(columns) -%}
    md5(
        {%- for c in columns -%}
            coalesce(cast({{ c }} as varchar), '')
            {%- if not loop.last %} || '|' || {% endif -%}
        {%- endfor -%}
    )
{%- endmacro %}