-- Year-over-year organizational financial trend, from public 990 data.

with financials as (

    select * from {{ ref('stg_org_financials') }}

)

select
    fiscal_year,
    total_revenue,
    total_expenses,
    operating_surplus_deficit,
    expense_to_revenue_ratio,
    net_assets,
    round(
        (total_revenue - lag(total_revenue) over (order by fiscal_year))::float
        / nullif(lag(total_revenue) over (order by fiscal_year), 0),
        3
    ) as revenue_growth_yoy,
    round(
        (total_expenses - lag(total_expenses) over (order by fiscal_year))::float
        / nullif(lag(total_expenses) over (order by fiscal_year), 0),
        3
    ) as expense_growth_yoy

from financials
order by fiscal_year
