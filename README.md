# Medicare Claims Analytics — End-to-End US Healthcare Data Project

[![SQL](https://img.shields.io/badge/SQL-DuckDB-blue)](https://duckdb.org)
[![Data](https://img.shields.io/badge/Records-178k%2B-brightgreen)]()
[![Domain](https://img.shields.io/badge/Domain-US_Healthcare-purple)]()

> Production-grade SQL + Power BI project on US healthcare claims data.
> Mirrors the BMS Data Strategy & Analytics role responsibilities: data
> governance, brand performance tracking, claims/sales/payer analytics,
> data products, ETL, and dashboard delivery.

## What This Project Does

| Responsibility | Implemented in |
|---|---|
| Maintain business rules for commercial/healthcare datasets | `sql/04_data_quality_governance.sql` |
| Support data ingestion + integration (claims, payer data) | `sql/02_star_schema.sql` (Kimball model) |
| Apply SQL/Python to explore pharma datasets, support use cases | `sql/03_brand_performance_analytics.sql` |
| Develop dashboards/reporting for brand performance tracking | `powerbi/healthcare_claims_dashboard.pbix` |
| Support data governance, documentation, stewardship | `sql/04_data_quality_governance.sql`, `docs/` |
| Build new data products from scratch, scalable & reusable | `sql/05_powerbi_export_views.sql` (BI views) |

## Data

**Source:** [Synthea](https://synthetichealth.github.io/synthea/) — synthetic US healthcare records (schema identical to real CMS data).

| Table | Records |
|---|---|
| Patients | 1,171 |
| Encounters | 53,346 |
| Medications (claims) | 42,989 |
| Conditions | 8,376 |
| Providers | 5,855 |
| Organizations | 1,119 |
| Payers (Medicare, BCBS, Medicaid, Humana, UHC, Cigna, Aetna, Anthem) | 10 |
| Drug Overdose Deaths (CDC, real) | 10,000 |

**Plus:** 10,000 rows of real CDC drug-overdose mortality data for cross-reference.

## Architecture

```
Raw CSVs (Synthea + CDC)
       ↓
   DuckDB (15 MB)
       ↓
  Star schema (7 tables)
       ↓
  KPI SQL queries
       ↓
  BI views (denormalized)
       ↓
  Parquet + CSV exports
       ↓
  Power BI dashboard
```

## Quick Start

```bash
# 1. Re-create the database from raw CSVs
python build.py

# 2. Open the Power BI dashboard
open powerbi/healthcare_claims_dashboard.pbix
```

## Key Insights (already computed)

### Top drugs by total revenue (brand leaderboard)

| Rank | Drug | Use Case | Fills | Revenue |
|---|---|---|---|---|
| 1 | Simvastatin 10 MG | Cholesterol (statin) | 2,273 | $13.4M |
| 2 | Hydrochlorothiazide 25 MG | Blood pressure | 3,954 | $9.7M |
| 3 | Atenolol + Chlorthalidone | BP combination | 3,347 | $8.6M |
| 4 | Albuterol Inhaler | Asthma/COPD | 2,072 | $8.4M |
| 5 | Epinephrine Auto-Injector | Anaphylaxis | 107 | $7.1M |
| 6 | Humulin Insulin | Diabetes | 3,880 | $3.6M |
| 7 | PACLitaxel 100 MG | Chemotherapy | 541 | $3.6M |

### Payer mix (US healthcare market)

Medicare ($15.1M), Blue Cross Blue Shield ($14.1M), Medicaid ($11.9M) account for **~42% of all drug revenue** in this dataset — consistent with US commercial healthcare market share.

### Patient demographics

- **Age distribution**: ~60% adult, ~30% pediatric
- **Top states**: Massachusetts (where Synthea generates primary data), with national spread
- **Payer mix**: 60%+ covered by commercial/government insurance; ~30% uninsured

## SQL File Map

| File | What it does | Lines |
|---|---|---|
| `01_data_profiling.sql` | Row counts, distributions, null rates, cost ranges | 60 |
| `02_star_schema.sql` | Builds 5 dim + 2 fact tables with surrogate keys, age bands, derived metrics | 130 |
| `03_brand_performance_analytics.sql` | Top drugs, therapeutic areas, monthly trends with 3-mo moving avg, payer coverage, adherence | 110 |
| `04_data_quality_governance.sql` | Orphan FK checks, business rules, NULL rate audit, duplicate detection, cost reasonableness | 90 |
| `05_powerbi_export_views.sql` | Denormalized `v_bi_encounter` + `v_bi_medication` for Power BI; Parquet + CSV export | 70 |

## Power BI Dashboard

**Live link:** _(publishing pending — Power BI publish-to-web requires Microsoft account)_

**File:** `powerbi/healthcare_claims_dashboard.pbix`

**Pages and visuals:**

1. **Executive Summary** — Total revenue, total fills, top payer, top drug (KPI cards + trend chart)
2. **Brand Performance** — Top 25 drugs by revenue, with slicers for payer, state, age band
3. **Payer Analytics** — Coverage rate by payer, total covered vs uncovered, payer mix donut
4. **Patient Demographics** — Age band, gender, state, race distribution
5. **Provider Performance** — Top specialties by encounter volume, geographic distribution

## Tech Stack

- **Database:** DuckDB 1.5.4 (in-process analytical SQL, no server)
- **SQL dialect:** PostgreSQL-compatible (DuckDB)
- **Data formats:** CSV (raw) → DuckDB (model) → Parquet + CSV (BI export)
- **Visualization:** Power BI Desktop

## Project Structure

```
medicare-claims-analytics/
├── README.md                       (this file)
├── build.py                        (one-command DB build)
├── docs/
│   └── STAR_SCHEMA.md             (schema diagram + metrics)
├── sql/
│   ├── 01_data_profiling.sql
│   ├── 02_star_schema.sql
│   ├── 03_brand_performance_analytics.sql
│   ├── 04_data_quality_governance.sql
│   └── 05_powerbi_export_views.sql
├── data/
│   ├── raw/csv/                   (Synthea raw data)
│   ├── cdc_drug_overdose.csv      (real CDC data)
│   ├── healthcare.duckdb          (built database, 15 MB)
│   └── exports/
│       ├── bi_encounter.csv       (Power BI source)
│       ├── bi_encounter.parquet
│       ├── bi_medication.csv
│       └── bi_medication.parquet
└── powerbi/
    └── healthcare_claims_dashboard.pbix
```

## License

Code: MIT. Data: Synthea (Apache 2.0) + CDC public data (public domain).
