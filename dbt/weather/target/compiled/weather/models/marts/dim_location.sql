-- Location dimension. One row per city observed, keyed by an md5 surrogate
-- over the normalised city name so the fact table never carries the raw string.

with locations as (
    select distinct
        city,
        utc_offset
    from "db"."dev_staging"."stg_weather"
)

select
    md5(lower(trim(city))) as location_key,
    city,
    utc_offset
from locations