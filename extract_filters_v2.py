
import duckdb, json
con = duckdb.connect(r"C:\Users\modir\James\projects\medicare-claims-analytics\data\healthcare.duckdb", read_only=True)
out = {
    "payers": [r[0] for r in con.execute("SELECT payer_name FROM dim_payer ORDER BY payer_name").fetchall()],
    "states": [r[0] for r in con.execute("SELECT DISTINCT patient_state FROM dim_patient WHERE patient_state IS NOT NULL ORDER BY patient_state").fetchall()],
    "age_bands": ['0-17','18-34','35-49','50-64','65-79','80+'],
    "encounter_classes": [r[0] for r in con.execute("SELECT DISTINCT encounter_class FROM fact_encounter WHERE encounter_class IS NOT NULL ORDER BY encounter_class").fetchall()],
    "encounter_descs": [r[0] for r in con.execute("SELECT encounter_description, COUNT(*) AS c FROM fact_encounter WHERE encounter_description IS NOT NULL GROUP BY encounter_description ORDER BY c DESC LIMIT 50").fetchall()],
    "years": [r[0] for r in con.execute("SELECT DISTINCT year FROM fact_encounter WHERE year >= 2010 ORDER BY year").fetchall()],
    "cities": [r[0] for r in con.execute("SELECT DISTINCT city, COUNT(*) AS c FROM dim_provider WHERE city IS NOT NULL AND city != '' GROUP BY city ORDER BY c DESC LIMIT 30").fetchall()],
    "specialties": [r[0] for r in con.execute("SELECT DISTINCT speciality, COUNT(*) AS c FROM dim_provider WHERE speciality IS NOT NULL GROUP BY speciality ORDER BY c DESC LIMIT 30").fetchall()],
    "genders": [r[0] for r in con.execute("SELECT DISTINCT gender FROM dim_patient WHERE gender IS NOT NULL ORDER BY gender").fetchall()],
    "races": [r[0] for r in con.execute("SELECT DISTINCT race FROM dim_patient WHERE race IS NOT NULL ORDER BY race").fetchall()],
    "ethnicity": [r[0] for r in con.execute("SELECT DISTINCT ethnicity FROM dim_patient WHERE ethnicity IS NOT NULL ORDER BY ethnicity").fetchall()],
}
open(r"C:\Users\modir\James\projects\medicare-claims-analytics\data\filters.json","w").write(json.dumps(out, indent=2))
print("Wrote filters.json with keys:", list(out.keys()))
for k, v in out.items():
    print(f"  {k}: {len(v)} items")
con.close()
