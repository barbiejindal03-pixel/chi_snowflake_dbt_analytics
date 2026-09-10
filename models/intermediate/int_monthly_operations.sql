-- one row per month: visits, unique/new clients, services delivered.
-- basically the "NUMBER OF VISITORS ANALYSIS" tab from the old sheet,
-- just calculated here instead of by hand.

with visits as (

    select * from {{ ref('stg_visits') }}

),

clients as (

    select * from {{ ref('stg_clients') }}

),

monthly_visits as (

    select
        visit_month,
        count(*)                                as total_visits,
        count(distinct client_id)               as unique_clients_served,
        sum(case when phone_given = 1 then 1 else 0 end)      as phones_given,
        sum(case when bus_pass_given = 1 then 1 else 0 end)   as bus_passes_given,
        sum(case when resume_done = 'Yes / Done' then 1 else 0 end) as resumes_completed

    from visits
    group by 1

),

monthly_new_clients as (

    select
        intake_month,
        count(*) as new_clients

    from clients
    group by 1

)

select
    coalesce(mv.visit_month, mnc.intake_month) as activity_month,
    mv.total_visits,
    mv.unique_clients_served,
    mnc.new_clients,
    mv.phones_given,
    mv.bus_passes_given,
    mv.resumes_completed

from monthly_visits mv
full outer join monthly_new_clients mnc
    on mv.visit_month = mnc.intake_month
order by 1
