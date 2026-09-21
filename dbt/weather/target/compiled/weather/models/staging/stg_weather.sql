-- Staging: type-cast and clean the raw payload. No business logic here —
-- this model exists so the marts never read from the raw table directly,
-- which means a change to the source shape is absorbed in one place.

with source as (
    select * from "db"."dev"."raw_weather_data"
),

cleaned as (
    select
        id                                        as observation_id,
        trim(city)                                as city,
        temperature::numeric                      as temperature_c,
        trim(weather_descriptions)                as weather_description,
        wind_speed::numeric                       as wind_speed_kmh,
        time::timestamp                           as observed_at,
        inserted_at::timestamp                    as loaded_at,
        trim(utc_offset)                          as utc_offset
    from source
    where city is not null
      and temperature is not null
)

select * from cleaned