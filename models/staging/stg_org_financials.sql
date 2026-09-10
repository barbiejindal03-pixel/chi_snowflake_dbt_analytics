-- Source: Chicago Help Initiative public IRS Form 990 filings via
-- ProPublica Nonprofit Explorer (EIN 45-2542979). Public record --
-- organization-wide totals, not broken out by individual program.
-- https://projects.propublica.org/nonprofits/organizations/452542979

with source as (

    select * from {{ ref('org_financials') }}

),

renamed as (

    select
        cast(fiscal_year as integer)   as fiscal_year,
        total_revenue,
        total_expenses,
        total_assets,
        net_assets,
        total_revenue - total_expenses as operating_surplus_deficit,
        round(total_expenses::float / nullif(total_revenue, 0), 3) as expense_to_revenue_ratio

    from source

)

select * from renamed
