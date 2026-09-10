with source as (

    select * from {{ ref('dim_clients') }}

),

renamed as (

    select
        client_id,
        cast(intake_date as date)      as intake_date,
        gender,
        age_bucket,
        employment_status,
        work_interest,
        job_goal,
        has_resume,
        document_readiness_score,      -- 0-3: SS card + birth cert + state ID held
        date_trunc('month', cast(intake_date as date)) as intake_month

    from source

)

select * from renamed
