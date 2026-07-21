"""Run all SQL files in order + extract new metrics for dashboard v2."""
import duckdb, os, json, csv

DB_PATH = r"C:\Users\modir\James\projects\medicare-claims-analytics\data\healthcare.duckdb"
SQL_DIR = r"C:\Users\modir\James\projects\medicare-claims-analytics\sql"
con = duckdb.connect(DB_PATH)

# Run new files (06 and 07)
for f in ["06_therapeutic_area_analytics.sql", "07_brand_performance_deep_dive.sql"]:
    path = os.path.join(SQL_DIR, f)
    print(f"\n▶ {f}")
    sql = open(path, 'r', encoding='utf-8').read()
    for stmt in sql.split(';'):
        s = stmt.strip()
        if not s or s.startswith('--'): continue
        try:
            result = con.execute(s)
            if result.description:
                rows = result.fetchall()
                cols = [d[0] for d in result.description]
                print(f"  → {len(rows)} rows: {cols[:5]}")
                if rows and len(rows) <= 12:
                    for r in rows[:5]:
                        print(f"    {r}")
        except duckdb.Error as e:
            if "no result" in str(e).lower(): continue
            print(f"  ✗ {e}")

# Now extract metrics for dashboard v2
print("\n=== EXTRACTING DASHBOARD V2 METRICS ===")

# Therapeutic area top 15 by patient count
ta_patients = con.execute("""
    SELECT DESCRIPTION, COUNT(DISTINCT PATIENT) AS patient_count
    FROM conditions
    GROUP BY DESCRIPTION
    ORDER BY patient_count DESC
    LIMIT 15
""").fetchall()

# Therapeutic area top 15 by encounter cost
ta_enc_cost = con.execute("""
    WITH cond_patients AS (SELECT DISTINCT DESCRIPTION, PATIENT FROM conditions)
    SELECT cp.DESCRIPTION, COUNT(DISTINCT fe.patient_key) AS patients,
           ROUND(SUM(fe.total_claim_cost), 0) AS total_cost,
           ROUND(AVG(fe.total_claim_cost), 0) AS avg_cost
    FROM cond_patients cp
    JOIN fact_encounter fe ON cp.PATIENT = fe.patient_key
    WHERE fe.total_claim_cost > 0
    GROUP BY cp.DESCRIPTION
    ORDER BY total_cost DESC
    LIMIT 15
""").fetchall()

# ICD-10 chapter distribution
icd10 = con.execute("""
    SELECT SUBSTR(CAST(CODE AS VARCHAR), 1, 1) AS chapter,
           COUNT(DISTINCT PATIENT) AS patients,
           COUNT(DISTINCT CODE) AS distinct_conditions
    FROM conditions GROUP BY chapter
    ORDER BY patients DESC LIMIT 10
""").fetchall()

# Drug class revenue
drug_class = con.execute("""
    SELECT SPLIT_PART(drug_description, ' ', 1) AS drug_class,
           COUNT(*) AS fills, ROUND(SUM(total_cost), 0) AS revenue
    FROM fact_medication WHERE total_cost > 0
    GROUP BY drug_class ORDER BY revenue DESC LIMIT 15
""").fetchall()

# Top 10 drugs adherence
adherence = con.execute("""
    SELECT drug_description, COUNT(*) AS fills,
           ROUND(100.0 * SUM(is_completed) / COUNT(*), 1) AS adherence_pct
    FROM fact_medication GROUP BY drug_description
    HAVING COUNT(*) >= 100
    ORDER BY adherence_pct DESC LIMIT 10
""").fetchall()

# Save to a new data file
metrics_v2 = {
    "ta_patients": [{"condition": c, "patients": p} for c, p in ta_patients],
    "ta_enc_cost": [{"condition": c, "patients": p, "total_cost": tc, "avg_cost": ac} for c, p, tc, ac in ta_enc_cost],
    "icd10": [{"chapter": ch, "patients": p, "conditions": dc} for ch, p, dc in icd10],
    "drug_class": [{"class": cls, "fills": f, "revenue": r} for cls, f, r in drug_class],
    "adherence": [{"drug": d, "fills": f, "adherence_pct": a} for d, f, a in adherence],
}
# Merge with v1 metrics
v1 = json.load(open(r"C:\Users\modir\James\projects\medicare-claims-analytics\dashboard\data.json"))
v1.update(metrics_v2)
open(r"C:\Users\modir\James\projects\medicare-claims-analytics\data.json", "w").write(json.dumps(v1, indent=2))
print(f"\n✓ data.json updated with v2 metrics ({len(v1)} sections)")
print(f"  TA top: {ta_patients[0][0][:50]} = {ta_patients[0][1]:,} patients")
print(f"  Drug class top: {drug_class[0][0]} = ${drug_class[0][2]:,}")
print(f"  Best adherence: {adherence[0][0][:50]} = {adherence[0][2]}%")

con.close()
