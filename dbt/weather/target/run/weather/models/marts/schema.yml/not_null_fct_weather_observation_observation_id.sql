
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select observation_id
from "db"."dev_marts"."fct_weather_observation"
where observation_id is null



  
  
      
    ) dbt_internal_test