# Healthcare Claims Analytics — Star Schema

This document defines the star schema built from the Synthea US healthcare dataset (1,171 patients, 53,346 encounters, 42,989 medication claims, 8,376 conditions, 5,855 providers, 1,119 organizations, 10 payers).

## Schema (Kimball-style)

```
                        ┌──────────────────────┐
                        │     dim_date         │
                        │  date_key (PK)       │
                        │  full_date           │
                        │  year, quarter       │
                        │  month_name, day_type│
                        └──────────┬───────────┘
                                   │
                                   │
┌──────────────┐    ┌──────────────┴──────────────┐    ┌──────────────┐
│ dim_patient  │◄───┤       fact_encounter        ├───►│ dim_provider │
│ patient_key  │    │  encounter_key (PK)         │    │ provider_key │
│ gender       │    │  patient_key (FK)           │    │ speciality   │
│ age_band     │    │  provider_key (FK)          │    │ organization │
│ patient_state│    │  payer_key (FK)             │    │ state, city  │
│ coverage_pct │    │  date_key (FK)              │    └──────────────┘
└──────┬───────┘    │  base_cost, total_claim_cost│           │
       │            │  payer_coverage            │           │
       │            │  encounter_class           │           │
       │            │  duration_days             │           │
       │            │  is_fully_covered          │           │
       │            └──────────────┬──────────────┘           │
       │                           │                          │
       │                           ▼                          │
┌──────┴───────┐         ┌────────────────────┐         ┌─────┴────────┐
│ dim_payer    │◄────────┤  fact_medication   │         │dim_diagnosis │
│ payer_key    │         │  fill_date (FK)    │         │diagnosis_key │
│ payer_name   │         │  patient_key (FK)  │         │description   │
│ coverage_pct │         │  payer_key (FK)    │         │occurrence_ct │
│ unique_cust  │         │  drug_description  │         └──────────────┘
└──────────────┘         │  drug_code         │
                         │  base_cost         │
                         │  payer_coverage    │
                         │  total_cost        │
                         │  dispense_count    │
                         │  is_completed      │
                         └────────────────────┘
```

## Table Row Counts (verified)

| Table | Type | Rows | Purpose |
|---|---|---|---|
| `dim_patient` | Dimension | 1,171 | One per patient; age band, gender, state, lifetime expenses |
| `dim_provider` | Dimension | 5,855 | One per provider; specialty, organization, location |
| `dim_payer` | Dimension | 10 | Payer mix (Medicare, BCBS, Medicaid, etc.) |
| `dim_date` | Dimension | 7,672 | 2010-01-01 to 2030-12-31, with month/quarter/day-type |
| `dim_diagnosis` | Dimension | 129 | ICD-10 codes from conditions table |
| **`fact_encounter`** | **Fact** | **53,346** | **Grain: 1 row per encounter** with cost & coverage |
| **`fact_medication`** | **Fact** | **42,989** | **Grain: 1 row per medication fill** with payer coverage |

## Key Business Metrics (sample output)

### Top 10 Drugs by Total Revenue
| Drug | Fills | Revenue | Avg Cost |
|---|---|---|---|
| Simvastatin 10 MG (statin) | 2,273 | $13.4M | $5,891 |
| Hydrochlorothiazide 25 MG (BP) | 3,954 | $9.7M | $2,449 |
| Atenolol/Chlorthalidone (BP combo) | 3,347 | $8.6M | $2,565 |
| Albuterol Inhaler (asthma) | 2,072 | $8.4M | $4,037 |
| Epinephrine Auto-Injector | 107 | $7.1M | $66,446 |
| Humulin Insulin | 3,880 | $3.6M | $927 |
| PACLitaxel 100 MG (chemo) | 541 | $3.6M | $6,644 |

### Payer Mix (revenue)
| Payer | Patients | Fills | Total Cost | Coverage Rate |
|---|---|---|---|---|
| NO_INSURANCE | 584 | 8,495 | $17.1M | 0% |
| **Medicare** | **174** | **12,641** | **$15.1M** | **22.4%** |
| Blue Cross Blue Shield | 221 | 4,882 | $14.1M | 11.3% |
| Medicaid | 340 | 4,459 | $11.9M | 10.7% |
| Humana | 186 | 2,976 | $10.7M | 0% |
| UnitedHealthcare | 215 | 3,056 | $10.5M | 0% |
| Cigna Health | 182 | 2,229 | $8.9M | 0% |
| Aetna | 174 | 1,968 | $6.5M | 0% |
| Anthem | 102 | 1,713 | $4.6M | 0% |
| Dual Eligible | 22 | 570 | $0.8M | 10.2% |

## Key SQL Patterns Used

1. **Star schema with surrogate keys** — `dim_*` joins, no direct CSV joins
2. **Window functions** — 3-month moving average of drug revenue (file 03, query 3)
3. **CTEs** — multi-step analysis (file 03, query 2)
4. **Conditional logic** — `age_band` CASE expression (file 02)
5. **Data quality / governance** — orphan checks, NULL rates, business rules (file 04)
6. **BI-ready views** — denormalized `v_bi_encounter` for direct Power BI consumption (file 05)

## Files

- `sql/01_data_profiling.sql` — initial exploration
- `sql/02_star_schema.sql` — build dim + fact tables
- `sql/03_brand_performance_analytics.sql` — KPIs (mirrors BMS brand performance)
- `sql/04_data_quality_governance.sql` — business rules + data quality
- `sql/05_powerbi_export_views.sql` — denormalized BI views → Parquet/CSV
- `data/healthcare.duckdb` — full 15MB database
- `data/exports/bi_*.csv`, `bi_*.parquet` — Power BI source
