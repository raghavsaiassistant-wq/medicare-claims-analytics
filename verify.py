
import duckdb, os
db = r"C:\Users\modir\James\projects\medicare-claims-analytics\data\healthcare.duckdb"
con = duckdb.connect(db)
print("=== TOP 10 DRUGS BY TOTAL REVENUE ===")
rows = con.execute("""
    SELECT drug_description, COUNT(*) AS fills,
           ROUND(SUM(total_cost), 2) AS revenue,
           ROUND(AVG(total_cost), 2) AS avg_cost
    FROM fact_medication
    WHERE total_cost > 0
    GROUP BY drug_description
    ORDER BY revenue DESC
    LIMIT 10
""").fetchall()
for r in rows: print(r)
print("\n=== PAYER COVERAGE BREAKDOWN ===")
rows = con.execute("""
    SELECT payer_name, COUNT(DISTINCT fm.patient_key) AS patients,
           COUNT(*) AS fills, ROUND(SUM(fm.total_cost), 2) AS total_cost,
           ROUND(SUM(fm.payer_coverage) / NULLIF(SUM(fm.total_cost), 0) * 100, 1) AS cov_pct
    FROM fact_medication fm
    JOIN dim_payer dp ON fm.payer_key = dp.payer_key
    WHERE fm.total_cost > 0
    GROUP BY payer_name
    ORDER BY total_cost DESC
""").fetchall()
for r in rows: print(r)
print("\n=== ORPHAN CHECK ===")
rows = con.execute("""
    SELECT 'orphan_encounters_no_patient' AS chk, COUNT(*) AS v
    FROM fact_encounter fe
    WHERE fe.patient_key NOT IN (SELECT patient_key FROM dim_patient)
""").fetchall()
for r in rows: print(r)

# Now re-export bi_encounter.parquet (the COPY failed silently earlier?)
con.execute("COPY (SELECT * FROM v_bi_encounter) TO 'C:/Users/modir/James/projects/medicare-claims-analytics/data/exports/bi_encounter.parquet' (FORMAT PARQUET)")
con.close()
print("\n✓ All checks done. Exports:")
import os
for f in os.listdir(r"C:\Users\modir\James\projects\medicare-claims-analytics\data\exports"):
    p = os.path.join(r"C:\Users\modir\James\projects\medicare-claims-analytics\data\exports", f)
    print(f"  - {f}: {os.path.getsize(p)/1024:.0f} KB")
