
  
    

  create  table "db"."dev_marts"."fct_weather_observation__dbt_tmp"
  
  
    as
  
  (
    -- Observation fact. Grain: one row per weather reading.
-- Joins to dim_location on the surrogate key rather than carrying the city
-- string, so a rename in the source does not fan out across the mart.

with observations as (
    select * from "db"."dev_staging"."stg_weather"
)

select
    o.observation_id,
    md5(lower(trim(o.city)))                       as location_key,
    o.observed_at,
    o.loaded_at,
    o.temperature_c,
    round(o.temperature_c * 9.0 / 5.0 + 32, 1)     as temperature_f,
    o.wind_speed_kmh,
    round(o.wind_speed_kmh * 0.621371, 1)          as wind_speed_mph,
    o.weather_description,
    date_trunc('hour', o.observed_at)              as observed_hour,
    o.observed_at::date                            as observed_date
from observations o
  );
  