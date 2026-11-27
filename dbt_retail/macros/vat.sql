{% macro vat_from_gross(amount, rate=0.13) -%}
    round({{ amount }} - {{ amount }} / (1 + {{ rate }}), 2)
{%- endmacro %}