
import duckdb, json
con = duckdb.connect(r"C:\Users\modir\James\projects\medicare-claims-analytics\data\healthcare.duckdb", read_only=True)

# All payers
payers = [r[0] for r in con.execute("SELECT payer_name FROM dim_payer WHERE payer_name IS NOT NULL ORDER BY payer_name").fetchall()]

# All states
states = [r[0] for r in con.execute("SELECT DISTINCT patient_state FROM dim_patient WHERE patient_state IS NOT NULL ORDER BY patient_state").fetchall()]

# All age bands
age_bands = [r[0] for r in con.execute("SELECT DISTINCT age_band FROM dim_patient WHERE age_band IS NOT NULL ORDER BY age_band").fetchall()]

# Encounter classes
enc_classes = [r[0] for r in con.execute("SELECT DISTINCT encounter_class FROM fact_encounter WHERE encounter_class IS NOT NULL ORDER BY encounter_class").fetchall()]

# Top 30 drug classes for filter (no need for all 134)
drug_classes = [r[0] for r in con.execute("""
    SELECT SPLIT_PART(drug_description, ' ', 1) AS cls, COUNT(*) AS c
    FROM fact_medication WHERE total_cost > 0
    GROUP BY cls HAVING c > 100 ORDER BY c DESC LIMIT 30
""").fetchall()]

# Encounter descriptions (top 20)
enc_descs = [r[0] for r in con.execute("""
    SELECT encounter_description, COUNT(*) AS c FROM fact_encounter
    WHERE encounter_description IS NOT NULL
    GROUP BY encounter_description ORDER BY c DESC LIMIT 20
""").fetchall()]

print(f"Payers: {len(payers)}")
print(f"States: {len(states)}")
print(f"Age bands: {len(age_bands)}")
print(f"Encounter classes: {len(enc_classes)}")
print(f"Drug classes: {len(drug_classes)}")
print(f"Encounter descs: {len(enc_descs)}")

# Year range
years = [r[0] for r in con.execute("SELECT DISTINCT year FROM fact_encounter ORDER BY year").fetchall()]
print(f"Years: {years}")

result = {
    "payers": payers,
    "states": states,
    "age_bands": age_bands,
    "encounter_classes": enc_classes,
    "drug_classes": [d[0] for d in drug_classes],
    "encounter_descs": [d[0] for d in enc_descs],
    "years": years,
}
open(r"C:\Users\modir\James\projects\medicare-claims-analytics\data\filters.json", "w").write(json.dumps(result, indent=2))
print("Saved filters.json")
con.close()
