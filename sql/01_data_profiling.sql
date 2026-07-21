-- =====================================================================
-- 01_data_profiling.sql
-- Healthcare Claims Analytics — initial data quality + business profiling
-- Author: Raghav Modi | Stack: DuckDB on Synthea US healthcare dataset
-- =====================================================================
-- Purpose: Profile all 13 source tables to understand data shape,
--          null rates, and business-relevant distributions before
--          building the star schema.
-- =====================================================================

-- ---------- Table row counts ----------
SELECT 'patients'        AS table_name, COUNT(*) AS row_count FROM patients
UNION ALL SELECT 'encounters',    COUNT(*) FROM encounters
UNION ALL SELECT 'medications',   COUNT(*) FROM medications
UNION ALL SELECT 'conditions',    COUNT(*) FROM conditions
UNION ALL SELECT 'providers',     COUNT(*) FROM providers
UNION ALL SELECT 'organizations', COUNT(*) FROM organizations
UNION ALL SELECT 'payers',        COUNT(*) FROM payers
UNION ALL SELECT 'procedures',    COUNT(*) FROM procedures
UNION ALL SELECT 'immunizations', COUNT(*) FROM immunizations
UNION ALL SELECT 'allergies',     COUNT(*) FROM allergies
UNION ALL SELECT 'careplans',     COUNT(*) FROM careplans
UNION ALL SELECT 'imaging_studies', COUNT(*) FROM imaging_studies
UNION ALL SELECT 'observations',  COUNT(*) FROM observations
UNION ALL SELECT 'cdc_drug_overdose', COUNT(*) FROM cdc_drug_overdose
ORDER BY row_count DESC;

-- ---------- Cost distribution check (critical for claim analytics) ----------
SELECT
    MIN(BASE_ENCOUNTER_COST) AS min_cost,
    ROUND(AVG(BASE_ENCOUNTER_COST), 2) AS avg_cost,
    ROUND(MEDIAN(BASE_ENCOUNTER_COST), 2) AS median_cost,
    MAX(BASE_ENCOUNTER_COST) AS max_cost,
    ROUND(SUM(BASE_ENCOUNTER_COST), 2) AS total_cost
FROM encounters
WHERE BASE_ENCOUNTER_COST > 0;

-- ---------- Date range of activity ----------
SELECT
    MIN(START::DATE) AS earliest_encounter,
    MAX(START::DATE) AS latest_encounter,
    DATE_DIFF('day', MIN(START::DATE), MAX(START::DATE)) AS day_span
FROM encounters;

-- ---------- Patient demographics (essential for patient segmentation) ----------
SELECT
    GENDER,
    RACE,
    COUNT(*) AS patient_count
FROM patients
GROUP BY GENDER, RACE
ORDER BY patient_count DESC
LIMIT 20;

-- ---------- Top payers by covered revenue (US healthcare payer mix) ----------
SELECT
    p.NAME AS payer_name,
    p.AMOUNT_COVERED,
    p.AMOUNT_UNCOVERED,
    ROUND(p.AMOUNT_COVERED / NULLIF(p.AMOUNT_COVERED + p.AMOUNT_UNCOVERED, 0) * 100, 1) AS coverage_pct,
    p.UNIQUE_CUSTOMERS,
    p.COVERED_ENCOUNTERS,
    p.COVERED_MEDICATIONS
FROM payers p
ORDER BY p.AMOUNT_COVERED DESC;
