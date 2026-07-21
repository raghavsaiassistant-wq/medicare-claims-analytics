
import duckdb
con = duckdb.connect(r"C:\Users\modir\James\projects\medicare-claims-analytics\data\healthcare.duckdb", read_only=True)
print("=== TOP 15 THERAPEUTIC AREAS (patient count) ===")
for r in con.execute(open(r"C:\Users\modir\James\projects\medicare-claims-analytics\sql\06_therapeutic_area_analytics.sql").read().split(";")[0]+";").fetchall():
    print(f"  {r[0][:50]:50s} patients={r[1]:>5,}")

print("\n=== TOP 10 ICD-10 CHAPTERS ===")
sql = """
SELECT
    SUBSTR(CODE, 1, 1) AS icd10_chapter,
    COUNT(DISTINCT PATIENT) AS patient_count,
    COUNT(DISTINCT CODE) AS distinct_conditions
FROM conditions
GROUP BY icd10_chapter
ORDER BY patient_count DESC
LIMIT 10
"""
for r in con.execute(sql).fetchall():
    print(f"  Chapter {r[0]:3s}  patients={r[1]:>5,}  distinct_conditions={r[2]}")

print("\n=== TOP 15 DRUG CLASSES BY REVENUE ===")
sql = """
SELECT
    SPLIT_PART(drug_description, ' ', 1) AS drug_class,
    COUNT(*) AS fills,
    ROUND(SUM(total_cost), 0) AS revenue
FROM fact_medication
WHERE total_cost > 0
GROUP BY drug_class
ORDER BY revenue DESC
LIMIT 15
"""
for r in con.execute(sql).fetchall():
    print(f"  {r[0][:20]:20s} fills={r[1]:>6,}  revenue=${r[2]:>12,}")

print("\n=== TOP 15 BRAND ADHERENCE ===")
sql = """
SELECT drug_description, COUNT(*) AS fills,
       ROUND(100.0 * SUM(is_completed) / COUNT(*), 1) AS adherence_pct
FROM fact_medication
GROUP BY drug_description
HAVING COUNT(*) >= 100
ORDER BY adherence_pct DESC
LIMIT 10
"""
for r in con.execute(sql).fetchall():
    print(f"  {r[0][:50]:50s} fills={r[1]:>5,}  adherence={r[2]}%")
con.close()
