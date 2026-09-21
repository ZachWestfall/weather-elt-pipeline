
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    select *
    from "db"."dev_marts"."fct_weather_observation"
    where temperature_c < -90
       or temperature_c > 60

  
  
      
    ) dbt_internal_test