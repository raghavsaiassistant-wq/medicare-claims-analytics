-- =====================================================================
-- 03_brand_performance_analytics.sql
-- Healthcare Claims Analytics — Brand/medication performance KPIs
-- Author: Raghav Modi | Stack: DuckDB
-- =====================================================================
-- Purpose: Brand-level performance analytics on medication claims.
--          Mirrors BMS Commercialization use cases:
--          "brand performance tracking and analytics delivery".
-- =====================================================================

-- =====================================================
-- 1. Top 25 drugs by total claims cost (the "brand leaderboard")
-- =====================================================
SELECT
    drug_description,
    COUNT(*)                          AS fill_count,
    COUNT(DISTINCT patient_key)       AS unique_patients,
    ROUND(SUM(base_cost), 2)          AS total_base_cost,
    ROUND(SUM(payer_coverage), 2)     AS total_payer_coverage,
    ROUND(SUM(total_cost), 2)         AS total_revenue,
    ROUND(AVG(total_cost), 2)         AS avg_cost_per_fill
FROM fact_medication
WHERE total_cost > 0
GROUP BY drug_description
ORDER BY total_revenue DESC
LIMIT 25;

-- =====================================================
-- 2. Therapeutic-area rollup: top 20 condition descriptions
--    and their total cost of care (encounters + medications)
-- =====================================================
WITH condition_costs AS (
    SELECT
        c.DESCRIPTION  AS condition_description,
        COUNT(DISTINCT c.PATIENT) AS patient_count,
        COUNT(DISTINCT c.ENCOUNTER) AS encounter_count
    FROM conditions c
    GROUP BY c.DESCRIPTION
),
medication_costs AS (
    SELECT
        m.REASONDESCRIPTION AS condition_description,
        ROUND(SUM(m.TOTALCOST), 2) AS med_total_cost
    FROM medications m
    WHERE m.REASONDESCRIPTION IS NOT NULL
    GROUP BY m.REASONDESCRIPTION
)
SELECT
    cc.condition_description,
    cc.patient_count,
    cc.encounter_count,
    COALESCE(mc.med_total_cost, 0) AS medication_cost
FROM condition_costs cc
LEFT JOIN medication_costs mc ON cc.condition_description = mc.condition_description
ORDER BY cc.patient_count DESC
LIMIT 20;

-- =====================================================
-- 3. Monthly brand performance trend (drug fills over time)
--    Window function: 3-month moving average of revenue
-- =====================================================
WITH monthly_drug AS (
    SELECT
        drug_description,
        EXTRACT(YEAR FROM fill_date) AS yr,
        EXTRACT(MONTH FROM fill_date) AS mo,
        COUNT(*) AS fill_count,
        ROUND(SUM(total_cost), 2) AS monthly_revenue
    FROM fact_medication
    GROUP BY drug_description, yr, mo
),
top_drugs AS (
    SELECT drug_description
    FROM monthly_drug
    GROUP BY drug_description
    ORDER BY SUM(monthly_revenue) DESC
    LIMIT 5
)
SELECT
    md.drug_description,
    md.yr,
    md.mo,
    md.fill_count,
    md.monthly_revenue,
    ROUND(AVG(md.monthly_revenue) OVER (
        PARTITION BY md.drug_description
        ORDER BY md.yr, md.mo
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS moving_avg_3mo_revenue
FROM monthly_drug md
INNER JOIN top_drugs td ON md.drug_description = td.drug_description
ORDER BY md.drug_description, md.yr, md.mo;

-- =====================================================
-- 4. Payer coverage rate by drug (key commercial KPI)
--    Answers: "What % of this drug's cost is covered by payer?"
-- =====================================================
SELECT
    payer_name,
    COUNT(DISTINCT fm.patient_key)   AS patient_count,
    COUNT(*)                         AS fill_count,
    ROUND(SUM(fm.total_cost), 2)     AS total_drug_cost,
    ROUND(SUM(fm.payer_coverage), 2) AS total_covered,
    ROUND(SUM(fm.payer_coverage) / NULLIF(SUM(fm.total_cost), 0) * 100, 1) AS coverage_rate_pct
FROM fact_medication fm
JOIN dim_payer dp ON fm.payer_key = dp.payer_key
WHERE fm.total_cost > 0
GROUP BY payer_name
ORDER BY total_drug_cost DESC;

-- =====================================================
-- 5. Drug adherence proxy: % of medications with a STOP date
--    (Completed courses = proxy for patient adherence)
-- =====================================================
SELECT
    drug_description,
    COUNT(*) AS total_fills,
    SUM(is_completed) AS completed_fills,
    ROUND(SUM(is_completed)::DOUBLE / COUNT(*) * 100, 1) AS adherence_rate_pct
FROM fact_medication
GROUP BY drug_description
HAVING COUNT(*) >= 50
ORDER BY adherence_rate_pct DESC
LIMIT 15;
