
    
    

select
    observation_id as unique_field,
    count(*) as n_records

from "db"."dev_staging"."stg_weather"
where observation_id is not null
group by observation_id
having count(*) > 1


