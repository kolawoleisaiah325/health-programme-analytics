-- PostgreSQL schema for fictional portfolio data only.
CREATE SCHEMA IF NOT EXISTS portfolio_health;

CREATE TABLE IF NOT EXISTS portfolio_health.facility (
    facility_id TEXT PRIMARY KEY,
    facility_name TEXT NOT NULL,
    area TEXT NOT NULL,
    facility_type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS portfolio_health.facility_month (
    facility_id TEXT NOT NULL REFERENCES portfolio_health.facility(facility_id),
    month_start DATE NOT NULL,
    target_doses INTEGER NOT NULL CHECK (target_doses >= 0),
    reporting_status TEXT NOT NULL
        CHECK (reporting_status IN ('accepted', 'missing', 'invalid')),
    submission_count INTEGER NOT NULL CHECK (submission_count >= 0),
    selected_report_id TEXT,
    accepted_doses INTEGER CHECK (accepted_doses >= 0),
    variance_doses INTEGER,
    PRIMARY KEY (facility_id, month_start),
    CHECK (
        (reporting_status = 'accepted' AND accepted_doses IS NOT NULL
            AND selected_report_id IS NOT NULL)
        OR (reporting_status <> 'accepted' AND accepted_doses IS NULL
            AND selected_report_id IS NULL)
    )
);

-- The source row number is the key so even a repeated or blank report ID
-- remains visible in the audit trail instead of disappearing during loading.
CREATE TABLE IF NOT EXISTS portfolio_health.report_review (
    source_row_number INTEGER PRIMARY KEY,
    report_id TEXT,
    facility_id TEXT,
    period TEXT,
    doses_delivered_text TEXT,
    reported_at_text TEXT,
    review_status TEXT NOT NULL
        CHECK (review_status IN ('accepted', 'superseded', 'rejected')),
    issue_code TEXT
);

CREATE INDEX IF NOT EXISTS facility_month_area_date_idx
    ON portfolio_health.facility_month(month_start, reporting_status);

CREATE OR REPLACE VIEW portfolio_health.v_monthly_performance AS
SELECT
    m.month_start,
    COUNT(*) AS expected_facility_months,
    COUNT(*) FILTER (WHERE m.submission_count > 0) AS submitted_facility_months,
    COUNT(*) FILTER (WHERE m.reporting_status = 'accepted') AS accepted_facility_months,
    COUNT(*) FILTER (WHERE m.reporting_status = 'missing') AS missing_facility_months,
    COUNT(*) FILTER (WHERE m.reporting_status = 'invalid') AS invalid_facility_months,
    SUM(m.accepted_doses) AS delivered_doses,
    SUM(m.target_doses) FILTER (WHERE m.reporting_status = 'accepted')
        AS target_doses_for_accepted_months
FROM portfolio_health.facility_month AS m
GROUP BY m.month_start;

CREATE OR REPLACE VIEW portfolio_health.v_facility_followup AS
SELECT
    f.area,
    f.facility_name,
    m.facility_id,
    m.month_start,
    m.reporting_status,
    m.accepted_doses,
    m.target_doses,
    CASE
        WHEN m.reporting_status = 'missing' THEN 'Request missing report'
        WHEN m.reporting_status = 'invalid' THEN 'Resolve rejected submission'
        WHEN m.accepted_doses < m.target_doses * 0.80
            THEN 'Review performance with facility'
        ELSE 'No immediate follow-up'
    END AS recommended_followup
FROM portfolio_health.facility_month AS m
JOIN portfolio_health.facility AS f USING (facility_id);

CREATE OR REPLACE VIEW portfolio_health.v_facility_trend AS
SELECT
    m.facility_id,
    m.month_start,
    m.reporting_status,
    m.accepted_doses,
    LAG(m.accepted_doses) OVER (
        PARTITION BY m.facility_id ORDER BY m.month_start
    ) AS prior_month_accepted_doses
FROM portfolio_health.facility_month AS m;
