-- =====================================================================
-- 04_data_quality_governance.sql
-- Healthcare Claims Analytics — Data quality + governance checks
-- Author: Raghav Modi | Stack: DuckDB
-- =====================================================================
-- Purpose: Business-rule validations, null checks, and referential
--          integrity. Mirrors BMS's "data governance" and "business
--          rules" responsibilities.
-- =====================================================================

-- =====================================================
-- 1. Referential integrity: orphan check
--    Every fact row must resolve to a dimension row.
-- =====================================================
SELECT 'orphan_encounters_no_patient' AS check_name, COUNT(*) AS violations
FROM fact_encounter fe
WHERE fe.patient_key NOT IN (SELECT patient_key FROM dim_patient)
UNION ALL
SELECT 'orphan_meds_no_patient', COUNT(*)
FROM fact_medication fm
WHERE fm.patient_key NOT IN (SELECT patient_key FROM dim_patient)
UNION ALL
SELECT 'orphan_encounters_no_provider', COUNT(*)
FROM fact_encounter fe
WHERE fe.provider_key NOT IN (SELECT provider_key FROM dim_provider)
UNION ALL
SELECT 'orphan_encounters_no_payer', COUNT(*)
FROM fact_encounter fe
WHERE fe.payer_key IS NOT NULL
  AND fe.payer_key NOT IN (SELECT payer_key FROM dim_payer);

-- =====================================================
-- 2. Business rule: payer coverage cannot exceed total claim cost
-- =====================================================
SELECT
    encounter_key,
    patient_key,
    total_claim_cost,
    payer_coverage,
    ROUND(payer_coverage - total_claim_cost, 2) AS overpayment_amt
FROM fact_encounter
WHERE payer_coverage > total_claim_cost
LIMIT 20;

-- =====================================================
-- 3. Data quality: NULL rate by column (per table)
-- =====================================================
SELECT 'encounters' AS tbl, 'REASONCODE' AS col,
       ROUND(SUM(CASE WHEN REASONCODE IS NULL OR REASONCODE = '' THEN 1 ELSE 0 END)::DOUBLE / COUNT(*) * 100, 1) AS null_pct
FROM encounters
UNION ALL
SELECT 'encounters', 'PAYER', ROUND(SUM(CASE WHEN PAYER IS NULL OR PAYER = '' THEN 1 ELSE 0 END)::DOUBLE / COUNT(*) * 100, 1) FROM encounters
UNION ALL
SELECT 'medications', 'REASONCODE', ROUND(SUM(CASE WHEN REASONCODE IS NULL OR REASONCODE = '' THEN 1 ELSE 0 END)::DOUBLE / COUNT(*) * 100, 1) FROM medications
UNION ALL
SELECT 'medications', 'STOP', ROUND(SUM(CASE WHEN STOP IS NULL OR STOP = '' THEN 1 ELSE 0 END)::DOUBLE / COUNT(*) * 100, 1) FROM medications
UNION ALL
SELECT 'patients', 'DEATHDATE', ROUND(SUM(CASE WHEN DEATHDATE IS NULL OR DEATHDATE = '' THEN 1 ELSE 0 END)::DOUBLE / COUNT(*) * 100, 1) FROM patients;

-- =====================================================
-- 4. Duplicates check: encounter IDs should be unique
-- =====================================================
SELECT
    'duplicate_encounters' AS check_name,
    COUNT(*) - COUNT(DISTINCT encounter_key) AS violations
FROM fact_encounter;

-- =====================================================
-- 5. Cost reasonableness: flag encounters with $0 or negative cost
-- =====================================================
SELECT
    encounter_class,
    COUNT(*) AS zero_or_neg_cost_count
FROM fact_encounter
WHERE total_claim_cost <= 0
GROUP BY encounter_class
ORDER BY zero_or_neg_cost_count DESC;
