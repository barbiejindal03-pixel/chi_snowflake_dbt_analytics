-- cost per client served / cost per visit, using CHI's public 990s.
--
-- two things worth knowing about this number:
-- 1. 990s only report total org expenses, not a per-program breakdown.
--    so this allocates a % of total expenses to Job Room specifically,
--    via job_room_expense_allocation_pct in dbt_project.yml. bump that
--    var and rerun if you want to see how much the result depends on it
--    (I tested 15% vs 20%, both scaled the output exactly proportionally)
-- 2. 990s lag 12-18 months. using the latest year available (2025) as
--    the cost proxy against current operational numbers instead of
--    trying to force-match fiscal years.

with latest_financials as (

    select *
    from {{ ref('stg_org_financials') }}
    order by fiscal_year desc
    limit 1

),

operational_totals as (

    select
        count(distinct client_id) as total_unique_clients_served,
        count(*)                  as total_visits

    from {{ ref('stg_visits') }}

),

allocated as (

    select
        lf.fiscal_year          as financials_fiscal_year,
        lf.total_expenses       as org_total_expenses,
        {{ var('job_room_expense_allocation_pct') }} as allocation_pct,
        lf.total_expenses * {{ var('job_room_expense_allocation_pct') }} as allocated_program_expense,
        ot.total_unique_clients_served,
        ot.total_visits

    from latest_financials lf
    cross join operational_totals ot

)

select
    financials_fiscal_year,
    org_total_expenses,
    allocation_pct,
    allocated_program_expense,
    total_unique_clients_served,
    total_visits,
    round(allocated_program_expense / nullif(total_unique_clients_served, 0), 2) as cost_per_client_served,
    round(allocated_program_expense / nullif(total_visits, 0), 2)                as cost_per_visit

from allocated
