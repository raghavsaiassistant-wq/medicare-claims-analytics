-- =====================================================================
-- 06_therapeutic_area_analytics.sql
-- Healthcare Claims Analytics — Therapeutic-area rollups
-- Author: Raghav Modi | Stack: DuckDB
-- =====================================================================
-- Purpose: Aggregate encounters and medications BY ICD-10 diagnosis
--          description. Mirrors BMS's "therapeutic area" and
--          "brand performance" analytics for oncology, cardiology, etc.
-- =====================================================================

-- =====================================================
-- 1. Top 15 conditions by total patient count
--    (the "therapeutic area leaderboard")
-- =====================================================
SELECT
    DESCRIPTION                                AS therapeutic_area,
    COUNT(DISTINCT PATIENT)                    AS patient_count,
    COUNT(DISTINCT ENCOUNTER)                  AS encounter_count,
    COUNT(*)                                   AS condition_record_count
FROM conditions
GROUP BY DESCRIPTION
ORDER BY patient_count DESC
LIMIT 15;

-- =====================================================
-- 2. Top 15 conditions by total encounter cost
--    (where the dollars go by therapeutic area)
-- =====================================================
WITH cond_patients AS (
    -- Map condition -> patient so we can join to encounter cost
    SELECT DISTINCT DESCRIPTION, PATIENT
    FROM conditions
),
enc_costs AS (
    SELECT
        cp.DESCRIPTION                          AS therapeutic_area,
        COUNT(DISTINCT fe.patient_key)          AS patient_count,
        COUNT(*)                                AS encounter_count,
        ROUND(SUM(fe.total_claim_cost), 2)      AS total_encounter_cost,
        ROUND(SUM(fe.payer_coverage), 2)        AS total_payer_coverage,
        ROUND(AVG(fe.total_claim_cost), 2)      AS avg_cost_per_encounter
    FROM cond_patients cp
    JOIN fact_encounter fe ON cp.PATIENT = fe.patient_key
    WHERE fe.total_claim_cost > 0
    GROUP BY cp.DESCRIPTION
)
SELECT * FROM enc_costs
ORDER BY total_encounter_cost DESC
LIMIT 15;

-- =====================================================
-- 3. Top 15 conditions by medication cost
--    (therapeutic-area pharmacy spend)
-- =====================================================
SELECT
    m.REASONDESCRIPTION                        AS therapeutic_area,
    COUNT(DISTINCT m.PATIENT)                  AS patient_count,
    COUNT(*)                                  AS fill_count,
    ROUND(SUM(m.TOTALCOST), 2)                 AS total_drug_cost,
    ROUND(AVG(m.TOTALCOST), 2)                 AS avg_cost_per_fill
FROM medications m
WHERE m.REASONDESCRIPTION IS NOT NULL
  AND m.TOTALCOST > 0
GROUP BY m.REASONDESCRIPTION
ORDER BY total_drug_cost DESC
LIMIT 15;
