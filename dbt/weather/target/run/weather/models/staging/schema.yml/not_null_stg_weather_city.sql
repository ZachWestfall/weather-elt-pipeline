
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select city
from "db"."dev_staging"."stg_weather"
where city is null



  
  
      
    ) dbt_internal_test