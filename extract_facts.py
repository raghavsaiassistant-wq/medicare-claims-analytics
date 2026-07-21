
import duckdb, json, gzip, os
con = duckdb.connect(r"C:\Users\modir\James\projects\medicare-claims-analytics\data\healthcare.duckdb", read_only=True)

# fact_medication with computed year/month
print("Loading fact_medication...")
meds = con.execute("""
    SELECT
        fm.fill_date,
        EXTRACT(YEAR FROM fm.fill_date) AS yr,
        EXTRACT(MONTH FROM fm.fill_date) AS mo,
        fm.patient_key, fm.payer_key, fm.drug_code, fm.drug_description,
        fm.base_cost, fm.payer_coverage, fm.total_cost, fm.dispense_count, fm.is_completed,
        dp.age_band, dp.GENDER, dp.patient_state, dpy.payer_name, dpy.coverage_rate_pct
    FROM fact_medication fm
    LEFT JOIN dim_patient dp ON fm.patient_key = dp.patient_key
    LEFT JOIN dim_payer dpy ON fm.payer_key = dpy.payer_key
""").fetchall()
print(f"  {len(meds):,} medication rows")
meds_list = []
for r in meds:
    meds_list.append({
        "d": str(r[0])[:10] if r[0] else None,
        "y": int(r[1]) if r[1] is not None else None,
        "m": int(r[2]) if r[2] is not None else None,
        "pk": r[3], "yk": r[4], "dc": r[5], "dd": r[6],
        "bc": float(r[7]) if r[7] is not None else 0,
        "pc": float(r[8]) if r[8] is not None else 0,
        "tc": float(r[9]) if r[9] is not None else 0,
        "di": int(r[10]) if r[10] is not None else 0,
        "ic": int(r[11]) if r[11] is not None else 0,
        "ab": r[12], "g": r[13], "ps": r[14],
        "yn": r[15], "yp": float(r[16]) if r[16] is not None else 0,
    })
gz_path = r"C:\Users\modir\James\projects\medicare-claims-analytics\data\fact_med.json.gz"
with open(gz_path, "wb") as f:
    f.write(gzip.compress(json.dumps(meds_list, separators=(',', ':')).encode('utf-8'), compresslevel=9))
print(f"  fact_med.json.gz: {os.path.getsize(gz_path)/1024:.0f} KB")

# fact_encounter
print("Loading fact_encounter...")
encs = con.execute("""
    SELECT
        fe.encounter_date,
        fe.year, fe.month_num,
        fe.patient_key, fe.provider_key, fe.payer_key,
        fe.encounter_class, fe.encounter_description,
        fe.base_cost, fe.total_claim_cost, fe.payer_coverage, fe.patient_responsibility,
        fe.is_fully_covered, fe.encounter_duration_days,
        dp.age_band, dp.GENDER, dp.patient_state, dpy.payer_name,
        dpr.SPECIALITY, dpr.CITY, dpr.organization_name
    FROM fact_encounter fe
    LEFT JOIN dim_patient dp ON fe.patient_key = dp.patient_key
    LEFT JOIN dim_provider dpr ON fe.provider_key = dpr.provider_key
    LEFT JOIN dim_payer dpy ON fe.payer_key = dpy.payer_key
""").fetchall()
print(f"  {len(encs):,} encounter rows")
encs_list = []
for r in encs:
    encs_list.append({
        "d": str(r[0])[:10] if r[0] else None,
        "y": int(r[1]) if r[1] is not None else None,
        "m": int(r[2]) if r[2] is not None else None,
        "pk": r[3], "prk": r[4], "yk": r[5],
        "ec": r[6], "ed": r[7],
        "bc": float(r[8]) if r[8] is not None else 0,
        "tc": float(r[9]) if r[9] is not None else 0,
        "pc": float(r[10]) if r[10] is not None else 0,
        "pr": float(r[11]) if r[11] is not None else 0,
        "fc": int(r[12]) if r[12] is not None else 0,
        "du": int(r[13]) if r[13] is not None else 0,
        "ab": r[14], "g": r[15], "ps": r[16],
        "yn": r[17], "sp": r[18], "ci": r[19], "org": r[20],
    })
gz_path = r"C:\Users\modir\James\projects\medicare-claims-analytics\data\fact_enc.json.gz"
with open(gz_path, "wb") as f:
    f.write(gzip.compress(json.dumps(encs_list, separators=(',', ':')).encode('utf-8'), compresslevel=9))
print(f"  fact_enc.json.gz: {os.path.getsize(gz_path)/1024:.0f} KB")

# Conditions
print("Loading conditions...")
conds = con.execute("SELECT PATIENT, DESCRIPTION, CODE FROM conditions").fetchall()
print(f"  {len(conds):,} condition rows")
conds_list = [{"pk": r[0], "d": r[1], "c": r[2]} for r in conds]
gz_path = r"C:\Users\modir\James\projects\medicare-claims-analytics\data\conditions.json.gz"
with open(gz_path, "wb") as f:
    f.write(gzip.compress(json.dumps(conds_list, separators=(',', ':')).encode('utf-8'), compresslevel=9))
print(f"  conditions.json.gz: {os.path.getsize(gz_path)/1024:.0f} KB")

con.close()
print("\n✓ All fact data saved (gzipped for fast web load)")
import os
total = sum(os.path.getsize(os.path.join(r"C:\Users\modir\James\projects\medicare-claims-analytics\data", f)) for f in os.listdir(r"C:\Users\modir\James\projects\medicare-claims-analytics\data") if f.endswith('.gz'))
print(f"  Total gzipped facts: {total/1024/1024:.1f} MB")
