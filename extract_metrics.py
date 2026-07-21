
import duckdb, json
con = duckdb.connect(r"C:\Users\modir\James\projects\medicare-claims-analytics\data\healthcare.duckdb", read_only=True)

# KPIs
kpis = con.execute("""
SELECT 
    (SELECT COUNT(*) FROM patients) AS total_patients,
    (SELECT COUNT(*) FROM encounters) AS total_encounters,
    (SELECT COUNT(*) FROM fact_medication) AS total_prescriptions,
    (SELECT ROUND(SUM(total_cost), 0) FROM fact_medication) AS total_revenue,
    (SELECT COUNT(DISTINCT drug_description) FROM fact_medication) AS unique_drugs,
    (SELECT COUNT(*) FROM dim_provider) AS total_providers,
    (SELECT COUNT(*) FROM organizations) AS total_orgs,
    (SELECT COUNT(*) FROM dim_payer) AS total_payers
""").fetchone()

# Top 10 drugs
top_drugs = con.execute("""
SELECT drug_description, COUNT(*) AS fills,
       ROUND(SUM(total_cost), 0) AS revenue
FROM fact_medication WHERE total_cost > 0
GROUP BY drug_description
ORDER BY revenue DESC LIMIT 10
""").fetchall()

# Payer mix
payer_mix = con.execute("""
SELECT dp.payer_name, COUNT(DISTINCT fm.patient_key) AS patients,
       COUNT(*) AS fills, ROUND(SUM(fm.total_cost), 0) AS cost,
       ROUND(SUM(fm.payer_coverage) / NULLIF(SUM(fm.total_cost), 0) * 100, 1) AS cov_pct
FROM fact_medication fm
JOIN dim_payer dp ON fm.payer_key = dp.payer_key
WHERE fm.total_cost > 0
GROUP BY dp.payer_name
ORDER BY cost DESC
""").fetchall()

# Top 10 specialties
specialties = con.execute("""
SELECT dpr.speciality, COUNT(*) AS encounters,
       ROUND(SUM(fe.total_claim_cost), 0) AS cost
FROM fact_encounter fe
JOIN dim_provider dpr ON fe.provider_key = dpr.provider_key
WHERE fe.total_claim_cost > 0
GROUP BY dpr.speciality
ORDER BY encounters DESC LIMIT 10
""").fetchall()

# State distribution
states = con.execute("""
SELECT dp.patient_state, COUNT(*) AS patients
FROM dim_patient dp
GROUP BY dp.patient_state
ORDER BY patients DESC LIMIT 10
""").fetchall()

# Age band distribution
age_bands = con.execute("""
SELECT age_band, COUNT(*) AS patients
FROM dim_patient
GROUP BY age_band
ORDER BY age_band
""").fetchall()

# Monthly trend
trend = con.execute("""
SELECT EXTRACT(YEAR FROM fill_date) AS yr, EXTRACT(MONTH FROM fill_date) AS mo,
       COUNT(*) AS fills, ROUND(SUM(total_cost), 0) AS revenue
FROM fact_medication
GROUP BY yr, mo
ORDER BY yr, mo
""").fetchall()

result = {
    "kpis": dict(zip(["total_patients","total_encounters","total_prescriptions",
                      "total_revenue","unique_drugs","total_providers","total_orgs","total_payers"],
                     kpis)),
    "top_drugs": [{"drug": d, "fills": f, "revenue": r} for d, f, r in top_drugs],
    "payer_mix": [{"payer": p, "patients": pt, "fills": f, "cost": c, "cov_pct": cp} for p, pt, f, c, cp in payer_mix],
    "specialties": [{"specialty": s, "encounters": e, "cost": c} for s, e, c in specialties],
    "states": [{"state": s, "patients": p} for s, p in states],
    "age_bands": [{"age_band": a, "patients": p} for a, p in age_bands],
    "trend": [{"year": int(y), "month": int(m), "fills": f, "revenue": r} for y, m, f, r in trend],
}
con.close()
import json
open(r"C:\Users\modir\James\projects\medicare-claims-analytics\dashboard\data.json", "w").write(json.dumps(result, indent=2))
print("data.json saved")
print(f"KPIs: {result['kpis']}")
