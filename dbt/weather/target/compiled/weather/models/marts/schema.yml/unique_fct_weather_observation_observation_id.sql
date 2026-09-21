
    
    

select
    observation_id as unique_field,
    count(*) as n_records

from "db"."dev_marts"."fct_weather_observation"
where observation_id is not null
group by observation_id
having count(*) > 1


