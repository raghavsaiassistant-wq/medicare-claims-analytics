-- =====================================================================
-- 02_star_schema.sql
-- Healthcare Claims Analytics — Build the star schema for BI
-- Author: Raghav Modi | Stack: DuckDB
-- =====================================================================
-- Purpose: Transform 13 source tables into a clean star schema
--          (fact_encounter + 5 dimensions) optimized for Power BI.
-- Pattern: Standard Kimball star schema — 1 fact, N dimensions.
-- =====================================================================

-- =====================================================
-- DIM_PATIENT: One row per patient with derived attributes
-- =====================================================
DROP TABLE IF EXISTS dim_patient;
CREATE TABLE dim_patient AS
SELECT
    p.Id                            AS patient_key,
    p.GENDER,
    p.RACE,
    p.ETHNICITY,
    p.STATE                         AS patient_state,
    p.COUNTY                        AS patient_county,
    DATE_DIFF('year', p.BIRTHDATE::DATE, CURRENT_DATE) AS age_years,
    CASE
        WHEN DATE_DIFF('year', p.BIRTHDATE::DATE, CURRENT_DATE) < 18 THEN '0-17'
        WHEN DATE_DIFF('year', p.BIRTHDATE::DATE, CURRENT_DATE) BETWEEN 18 AND 34 THEN '18-34'
        WHEN DATE_DIFF('year', p.BIRTHDATE::DATE, CURRENT_DATE) BETWEEN 35 AND 49 THEN '35-49'
        WHEN DATE_DIFF('year', p.BIRTHDATE::DATE, CURRENT_DATE) BETWEEN 50 AND 64 THEN '50-64'
        WHEN DATE_DIFF('year', p.BIRTHDATE::DATE, CURRENT_DATE) BETWEEN 65 AND 79 THEN '65-79'
        ELSE '80+'
    END                             AS age_band,
    CASE WHEN p.DEATHDATE IS NOT NULL THEN 1 ELSE 0 END AS is_deceased,
    p.DEATHDATE::DATE               AS death_date,
    p.HEALTHCARE_EXPENSES           AS lifetime_healthcare_expenses,
    p.HEALTHCARE_COVERAGE           AS lifetime_payer_coverage,
    ROUND(p.HEALTHCARE_COVERAGE / NULLIF(p.HEALTHCARE_EXPENSES, 0) * 100, 1) AS coverage_rate_pct
FROM patients p;

-- =====================================================
-- DIM_PROVIDER: One row per provider with specialty + org
-- =====================================================
DROP TABLE IF EXISTS dim_provider;
CREATE TABLE dim_provider AS
SELECT
    pr.Id            AS provider_key,
    pr.NAME          AS provider_name,
    pr.GENDER        AS provider_gender,
    pr.SPECIALITY,
    pr.ADDRESS,
    pr.CITY,
    pr.STATE,
    pr.ZIP,
    pr.UTILIZATION   AS provider_utilization,
    o.NAME           AS organization_name,
    o.REVENUE        AS organization_revenue,
    o.UTILIZATION    AS organization_utilization
FROM providers pr
LEFT JOIN organizations o ON pr.ORGANIZATION = o.Id;

-- =====================================================
-- DIM_PAYER: One row per payer with coverage ratios
-- =====================================================
DROP TABLE IF EXISTS dim_payer;
CREATE TABLE dim_payer AS
SELECT
    py.Id              AS payer_key,
    py.NAME            AS payer_name,
    py.STATE_HEADQUARTERED,
    py.AMOUNT_COVERED,
    py.AMOUNT_UNCOVERED,
    ROUND(py.AMOUNT_COVERED / NULLIF(py.AMOUNT_COVERED + py.AMOUNT_UNCOVERED, 0) * 100, 1)
                        AS coverage_rate_pct,
    py.UNIQUE_CUSTOMERS,
    py.COVERED_ENCOUNTERS,
    py.UNCOVERED_ENCOUNTERS,
    py.COVERED_MEDICATIONS,
    py.COVERED_PROCEDURES,
    py.QOLS_AVG
FROM payers py;

-- =====================================================
-- DIM_DATE: Date dimension from 2010-01-01 to 2030-12-31
-- =====================================================
DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date AS
WITH date_spine AS (
    SELECT UNNEST(generate_series(DATE '2010-01-01', DATE '2030-12-31', INTERVAL 1 DAY)) AS date_day
)
SELECT
    CAST(strftime(date_day, '%Y%m%d') AS INTEGER)   AS date_key,
    date_day                                         AS full_date,
    EXTRACT(YEAR FROM date_day)                      AS year,
    EXTRACT(QUARTER FROM date_day)                   AS quarter,
    EXTRACT(MONTH FROM date_day)                     AS month_num,
    strftime(date_day, '%B')                         AS month_name,
    EXTRACT(WEEK FROM date_day)                      AS week_num,
    EXTRACT(DAY FROM date_day)                       AS day_of_month,
    strftime(date_day, '%A')                         AS day_name,
    CASE WHEN strftime(date_day, '%w') IN ('0','6') THEN 'Weekend' ELSE 'Weekday' END AS day_type
FROM date_spine;

-- =====================================================
-- DIM_DIAGNOSIS: From conditions table (ICD-10 codes)
-- =====================================================
DROP TABLE IF EXISTS dim_diagnosis;
CREATE TABLE dim_diagnosis AS
SELECT
    CODE             AS diagnosis_key,
    DESCRIPTION      AS diagnosis_description,
    COUNT(*)         AS occurrence_count
FROM conditions
GROUP BY CODE, DESCRIPTION
ORDER BY occurrence_count DESC;

-- =====================================================
-- FACT_ENCOUNTER: One row per encounter (grain = encounter)
-- This is the central fact table. ~53K rows.
-- =====================================================
DROP TABLE IF EXISTS fact_encounter;
CREATE TABLE fact_encounter AS
SELECT
    e.Id                              AS encounter_key,
    e.PATIENT                         AS patient_key,
    e.PROVIDER                        AS provider_key,
    e.PAYER                           AS payer_key,
    e.ORGANIZATION                    AS organization_key,
    e.ENCOUNTERCLASS                  AS encounter_class,
    e.CODE                            AS encounter_code,
    e.DESCRIPTION                     AS encounter_description,
    CAST(e.START AS DATE)             AS encounter_date,
    CAST(strftime(e.START::TIMESTAMP, '%Y%m%d') AS INTEGER) AS date_key,
    EXTRACT(YEAR FROM e.START::TIMESTAMP)  AS year,
    EXTRACT(MONTH FROM e.START::TIMESTAMP) AS month_num,
    ROUND(e.BASE_ENCOUNTER_COST, 2)   AS base_cost,
    ROUND(e.TOTAL_CLAIM_COST, 2)      AS total_claim_cost,
    ROUND(e.PAYER_COVERAGE, 2)        AS payer_coverage,
    ROUND(e.TOTAL_CLAIM_COST - e.PAYER_COVERAGE, 2) AS patient_responsibility,
    CASE WHEN e.PAYER_COVERAGE >= e.TOTAL_CLAIM_COST THEN 1 ELSE 0 END AS is_fully_covered,
    DATEDIFF('day', e.START::TIMESTAMP, e.STOP::TIMESTAMP) AS encounter_duration_days
FROM encounters e;

-- =====================================================
-- FACT_MEDICATION: One row per medication fill (grain = fill)
-- ~43K rows. Central to brand performance analytics.
-- =====================================================
DROP TABLE IF EXISTS fact_medication;
CREATE TABLE fact_medication AS
SELECT
    m.START                           AS fill_date,
    CAST(strftime(m.START::TIMESTAMP, '%Y%m%d') AS INTEGER) AS date_key,
    m.PATIENT                         AS patient_key,
    m.PAYER                           AS payer_key,
    m.ENCOUNTER                       AS encounter_key,
    m.CODE                            AS drug_code,
    m.DESCRIPTION                     AS drug_description,
    m.REASONCODE                      AS reason_diagnosis_code,
    m.REASONDESCRIPTION               AS reason_description,
    ROUND(m.BASE_COST, 2)             AS base_cost,
    ROUND(m.PAYER_COVERAGE, 2)        AS payer_coverage,
    ROUND(m.TOTALCOST, 2)             AS total_cost,
    m.DISPENSES                       AS dispense_count,
    CASE WHEN m.STOP IS NOT NULL THEN 1 ELSE 0 END AS is_completed
FROM medications m;

-- ---------- Verify the schema ----------
SELECT 'dim_patient'       AS tbl, COUNT(*) AS rows FROM dim_patient
UNION ALL SELECT 'dim_provider',    COUNT(*) FROM dim_provider
UNION ALL SELECT 'dim_payer',       COUNT(*) FROM dim_payer
UNION ALL SELECT 'dim_date',        COUNT(*) FROM dim_date
UNION ALL SELECT 'dim_diagnosis',   COUNT(*) FROM dim_diagnosis
UNION ALL SELECT 'fact_encounter',  COUNT(*) FROM fact_encounter
UNION ALL SELECT 'fact_medication', COUNT(*) FROM fact_medication
ORDER BY tbl;
