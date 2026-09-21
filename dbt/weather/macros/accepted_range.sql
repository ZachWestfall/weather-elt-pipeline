{# Local range test so the project builds without installing dbt_utils.
   Fails if any row falls outside the physically plausible bounds — this is
   the test that catches a unit-conversion error, which is the failure mode
   that otherwise looks like perfectly valid data. #}
{% test dbt_utils_accepted_range_fallback(model, column_name, min_value, max_value) %}
    select *
    from {{ model }}
    where {{ column_name }} < {{ min_value }}
       or {{ column_name }} > {{ max_value }}
{% endtest %}
