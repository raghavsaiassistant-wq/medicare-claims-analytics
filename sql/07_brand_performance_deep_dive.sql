-- =====================================================================
-- 07_brand_performance_deep_dive.sql
-- Healthcare Claims Analytics — Brand-level performance analytics
-- Author: Raghav Modi | Stack: DuckDB
-- =====================================================================
-- Purpose: Drug-class revenue, adherence, regional mix, payer coverage.
--          Mirrors BMS's brand performance tracking use cases.
-- =====================================================================

-- =====================================================
-- 1. Top 20 drugs by state (drug distribution analysis)
-- =====================================================
WITH top_drugs AS (
    SELECT drug_description
    FROM fact_medication
    WHERE total_cost > 0
    GROUP BY drug_description
    ORDER BY SUM(total_cost) DESC
    LIMIT 20
)
SELECT
    fm.drug_description,
    dp.patient_state,
    COUNT(*)                                  AS fill_count,
    ROUND(SUM(fm.total_cost), 0)              AS revenue
FROM fact_medication fm
JOIN dim_patient dp ON fm.patient_key = dp.patient_key
JOIN top_drugs td ON fm.drug_description = td.drug_description
GROUP BY fm.drug_description, dp.patient_state
ORDER BY revenue DESC
LIMIT 50;

-- =====================================================
-- 2. Drug class revenue rollup (using first word of drug name as class)
-- =====================================================
SELECT
    SPLIT_PART(drug_description, ' ', 1)      AS drug_class,
    COUNT(*)                                  AS fill_count,
    COUNT(DISTINCT drug_description)          AS unique_drugs,
    COUNT(DISTINCT patient_key)               AS unique_patients,
    ROUND(SUM(total_cost), 0)                 AS total_revenue,
    ROUND(AVG(total_cost), 2)                 AS avg_cost_per_fill
FROM fact_medication
WHERE total_cost > 0
GROUP BY drug_class
ORDER BY total_revenue DESC
LIMIT 15;

-- =====================================================
-- 3. Brand adherence proxy: completed vs ongoing prescriptions
--    (Therapy completion = strong proxy for adherence)
-- =====================================================
SELECT
    drug_description,
    COUNT(*)                                  AS total_fills,
    SUM(is_completed)                         AS completed_fills,
    ROUND(100.0 * SUM(is_completed) / COUNT(*), 1) AS adherence_rate_pct,
    ROUND(SUM(CASE WHEN is_completed = 1 THEN total_cost ELSE 0 END), 0) AS completed_revenue
FROM fact_medication
GROUP BY drug_description
HAVING COUNT(*) >= 100
ORDER BY adherence_rate_pct DESC
LIMIT 15;

-- =====================================================
-- 4. Payer coverage by drug (top 10 most-prescribed drugs)
--    (Coverage rate is a key brand strategy KPI)
-- =====================================================
WITH top_drugs AS (
    SELECT drug_description
    FROM fact_medication
    WHERE total_cost > 0
    GROUP BY drug_description
    ORDER BY COUNT(*) DESC
    LIMIT 10
)
SELECT
    fm.drug_description,
    dp.payer_name,
    COUNT(*)                                  AS fill_count,
    ROUND(SUM(fm.total_cost), 0)              AS drug_cost,
    ROUND(SUM(fm.payer_coverage), 0)          AS payer_covered,
    ROUND(100.0 * SUM(fm.payer_coverage) /
          NULLIF(SUM(fm.total_cost), 0), 1)   AS coverage_rate_pct
FROM fact_medication fm
JOIN dim_payer dp ON fm.payer_key = dp.payer_key
JOIN top_drugs td ON fm.drug_description = td.drug_description
WHERE fm.total_cost > 0
GROUP BY fm.drug_description, dp.payer_name
ORDER BY drug_cost DESC
LIMIT 30;
