-- monthly ops table, ready for dashboards/BI. same numbers as the old
-- manual tab, just tested and version controlled now.
--
-- excludes the current month on purpose -- it's always partial since the
-- month isn't over, so it'd otherwise show a fake drop at the end of
-- every chart. the filter checks against current_date() so it keeps
-- working correctly next month too, didn't hardcode a date.

select
    activity_month,
    total_visits,
    unique_clients_served,
    coalesce(new_clients, 0) as new_clients,
    phones_given,
    bus_passes_given,
    resumes_completed,
    round(resumes_completed::float / nullif(unique_clients_served, 0), 3) as resume_completion_rate

from {{ ref('int_monthly_operations') }}
where activity_month < date_trunc('month', current_date())
