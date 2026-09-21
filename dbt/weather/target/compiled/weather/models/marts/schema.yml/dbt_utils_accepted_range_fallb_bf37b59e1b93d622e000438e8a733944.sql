
    select *
    from "db"."dev_marts"."fct_weather_observation"
    where temperature_c < -90
       or temperature_c > 60
