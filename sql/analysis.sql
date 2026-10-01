-- Example 1: reporting completeness and target attainment use different
-- denominators. Target attainment compares only accepted facility-months.
SELECT
    month_start,
    submitted_facility_months,
    expected_facility_months,
    ROUND(100.0 * submitted_facility_months / expected_facility_months, 1)
        AS reporting_completeness_pct,
    ROUND(100.0 * delivered_doses /
        NULLIF(target_doses_for_accepted_months, 0), 1)
        AS target_attainment_pct
FROM portfolio_health.v_monthly_performance
ORDER BY month_start;

-- Example 2: complex join, aggregation, and window ranking. Areas with the
-- most unresolved facility-months rise to the top of a programme review.
WITH area_issues AS (
    SELECT
        f.area,
        COUNT(*) FILTER (WHERE m.reporting_status = 'missing') AS missing_count,
        COUNT(*) FILTER (WHERE m.reporting_status = 'invalid') AS invalid_count,
        COUNT(*) FILTER (
            WHERE m.reporting_status = 'accepted'
                AND m.accepted_doses < m.target_doses * 0.80
        ) AS below_threshold_count
    FROM portfolio_health.facility_month AS m
    JOIN portfolio_health.facility AS f USING (facility_id)
    WHERE m.month_start >= DATE '2025-01-01'
    GROUP BY f.area
)
SELECT
    area,
    missing_count,
    invalid_count,
    below_threshold_count,
    DENSE_RANK() OVER (
        ORDER BY missing_count + invalid_count + below_threshold_count DESC
    ) AS review_priority_rank
FROM area_issues
ORDER BY review_priority_rank, area;

-- Example 3: inspect raw review decisions behind a facility-month.
SELECT report_id, doses_delivered_text, reported_at_text,
       review_status, issue_code
FROM portfolio_health.report_review
WHERE facility_id = 'F002' AND period = '2025-05'
ORDER BY reported_at_text;
