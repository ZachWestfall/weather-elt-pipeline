
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select temperature_c
from "db"."dev_marts"."fct_weather_observation"
where temperature_c is null



  
  
      
    ) dbt_internal_test