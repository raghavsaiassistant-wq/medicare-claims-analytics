
import duckdb, json
con = duckdb.connect(r"C:\Users\modir\James\projects\medicare-claims-analytics\data\healthcare.duckdb", read_only=True)

cities = con.execute("""
    SELECT CITY, COUNT(*) AS c FROM dim_provider
    WHERE CITY IS NOT NULL AND CITY != ''
    GROUP BY CITY ORDER BY c DESC LIMIT 30
""").fetchall()
provider_states = con.execute("""
    SELECT DISTINCT STATE FROM dim_provider WHERE STATE IS NOT NULL AND STATE != '' ORDER BY STATE
""").fetchall()

recent_years = [r[0] for r in con.execute("""
    SELECT DISTINCT year FROM fact_encounter WHERE year >= 2010 ORDER BY year
""").fetchall()]

specialties = [r[0] for r in con.execute("""
    SELECT DISTINCT SPECIALITY FROM dim_provider WHERE SPECIALITY IS NOT NULL ORDER BY SPECIALITY
""").fetchall()]

all_enc_descs = [r[0] for r in con.execute("""
    SELECT encounter_description, COUNT(*) AS c FROM fact_encounter
    WHERE encounter_description IS NOT NULL
    GROUP BY encounter_description ORDER BY c DESC LIMIT 50
""").fetchall()]

all_drugs = [r[0] for r in con.execute("""
    SELECT drug_description, COUNT(*) AS c FROM fact_medication
    WHERE drug_description IS NOT NULL
    GROUP BY drug_description ORDER BY c DESC
""").fetchall()]

all_conditions = [r[0] for r in con.execute("""
    SELECT DESCRIPTION, COUNT(*) AS c FROM conditions
    WHERE DESCRIPTION IS NOT NULL
    GROUP BY DESCRIPTION ORDER BY c DESC LIMIT 100
""").fetchall()]

races = [r[0] for r in con.execute("""
    SELECT DISTINCT RACE FROM dim_patient WHERE RACE IS NOT NULL ORDER BY RACE
""").fetchall()]
genders = [r[0] for r in con.execute("""
    SELECT DISTINCT GENDER FROM dim_patient WHERE GENDER IS NOT NULL ORDER BY GENDER
""").fetchall()]
ethnicity = [r[0] for r in con.execute("""
    SELECT DISTINCT ETHNICITY FROM dim_patient WHERE ETHNICITY IS NOT NULL ORDER BY ETHNICITY
""").fetchall()]

print(f"Cities: {len(cities)}")
print(f"Provider states: {[s[0] for s in provider_states]}")
print(f"Recent years: {len(recent_years)} (range {recent_years[0] if recent_years else '?'}–{recent_years[-1] if recent_years else '?'})")
print(f"Specialties: {len(specialties)}")
print(f"Enc descs: {len(all_enc_descs)}")
print(f"All drugs: {len(all_drugs)}")
print(f"Conditions: {len(all_conditions)}")
print(f"Races: {races}")
print(f"Genders: {genders}")
print(f"Ethnicity: {ethnicity}")

import json
result = {
    "cities": [c[0] for c in cities],
    "provider_states": [s[0] for s in provider_states],
    "years": recent_years,
    "specialties": specialties,
    "encounter_descs": [d[0] for d in all_enc_descs],
    "all_drugs": [d[0] for d in all_drugs],
    "all_conditions": [c[0] for c in all_conditions],
    "races": races,
    "genders": genders,
    "ethnicity": ethnicity,
}
open(r"C:\Users\modir\James\projects\medicare-claims-analytics\data\search_data.json", "w").write(json.dumps(result, indent=2))
print(f"Saved search_data.json")
con.close()
