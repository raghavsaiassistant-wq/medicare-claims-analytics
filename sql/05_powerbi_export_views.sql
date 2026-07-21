-- =====================================================================
-- 05_powerbi_export_views.sql
-- Healthcare Claims Analytics — Flatten star schema for Power BI
-- Author: Raghav Modi | Stack: DuckDB
-- =====================================================================
-- Purpose: Create denormalized views that Power BI can consume directly.
--          Each row of v_bi_encounter contains everything Power BI needs
--          for a slicer/filter/measure — no joins at refresh time.
-- =====================================================================

-- =====================================================
-- View 1: Encounter-level BI view (the main dashboard source)
-- =====================================================
DROP VIEW IF EXISTS v_bi_encounter;
CREATE VIEW v_bi_encounter AS
SELECT
    fe.encounter_key,
    fe.encounter_date,
    fe.year,
    fe.month_num,
    fe.date_key,
    dd.month_name,
    dd.quarter,
    dd.day_type,
    fe.encounter_class,
    fe.encounter_description,
    fe.base_cost,
    fe.total_claim_cost,
    fe.payer_coverage,
    fe.patient_responsibility,
    fe.is_fully_covered,
    fe.encounter_duration_days,
    dp.age_band,
    dp.gender          AS patient_gender,
    dp.race            AS patient_race,
    dp.patient_state,
    dp.is_deceased,
    dp.lifetime_healthcare_expenses,
    dp.coverage_rate_pct AS patient_lifetime_coverage_pct,
    dpr.speciality     AS provider_specialty,
    dpr.organization_name,
    dpr.city           AS provider_city,
    dpr.state          AS provider_state,
    dpy.payer_name,
    dpy.coverage_rate_pct AS payer_coverage_pct
FROM fact_encounter fe
LEFT JOIN dim_date       dd  ON fe.date_key = dd.date_key
LEFT JOIN dim_patient    dp  ON fe.patient_key = dp.patient_key
LEFT JOIN dim_provider   dpr ON fe.provider_key = dpr.provider_key
LEFT JOIN dim_payer      dpy ON fe.payer_key = dpy.payer_key;

-- =====================================================
-- View 2: Medication-level BI view
-- =====================================================
DROP VIEW IF EXISTS v_bi_medication;
CREATE VIEW v_bi_medication AS
SELECT
    fm.fill_date,
    EXTRACT(YEAR  FROM fm.fill_date) AS year,
    EXTRACT(MONTH FROM fm.fill_date) AS month_num,
    fm.drug_description,
    fm.drug_code,
    fm.base_cost,
    fm.payer_coverage,
    fm.total_cost,
    fm.dispense_count,
    fm.is_completed,
    dp.age_band,
    dp.gender AS patient_gender,
    dp.patient_state,
    dpy.payer_name,
    dpy.coverage_rate_pct AS payer_coverage_pct
FROM fact_medication fm
LEFT JOIN dim_patient dp  ON fm.patient_key = dp.patient_key
LEFT JOIN dim_payer    dpy ON fm.payer_key = dpy.payer_key;

-- =====================================================
-- Materialize to Parquet for fast Power BI load
-- =====================================================
COPY (SELECT * FROM v_bi_encounter)  TO 'C:/Users/modir/James/projects/medicare-claims-analytics/data/exports/bi_encounter.parquet'  (FORMAT PARQUET);
COPY (SELECT * FROM v_bi_medication) TO 'C:/Users/modir/James/projects/medicare-claims-analytics/data/exports/bi_medication.parquet' (FORMAT PARQUET);
COPY (SELECT * FROM v_bi_encounter)  TO 'C:/Users/modir/James/projects/medicare-claims-analytics/data/exports/bi_encounter.csv'      (HEADER, DELIMITER ',');
COPY (SELECT * FROM v_bi_medication) TO 'C:/Users/modir/James/projects/medicare-claims-analytics/data/exports/bi_medication.csv'     (HEADER, DELIMITER ',');
