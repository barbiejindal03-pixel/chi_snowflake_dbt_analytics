with source as (

    select * from {{ ref('fact_visits') }}

),

renamed as (

    select
        visit_id,
        client_id,
        cast(visit_date as date)   as visit_date,
        volunteer,
        resume_done,
        phone_given,
        bus_pass_given,
        service_category,
        date_trunc('month', cast(visit_date as date)) as visit_month

    from source

)

select * from renamed
