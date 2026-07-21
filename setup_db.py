
import duckdb, os
data_dir = r"C:\Users\modir\James\projects\medicare-claims-analytics\data\raw\csv"
db_path = r"C:\Users\modir\James\projects\medicare-claims-analytics\data\healthcare.duckdb"
if os.path.exists(db_path): os.remove(db_path)
con = duckdb.connect(db_path)

files = {
    "patients": "patients.csv", "encounters": "encounters.csv", "medications": "medications.csv",
    "conditions": "conditions.csv", "providers": "providers.csv", "organizations": "organizations.csv",
    "payers": "payers.csv", "procedures": "procedures.csv", "immunizations": "immunizations.csv",
    "allergies": "allergies.csv", "careplans": "careplans.csv", "imaging_studies": "imaging_studies.csv",
    "observations": "observations.csv",
}
for table, f in files.items():
    path = os.path.join(data_dir, f)
    con.execute(f"""CREATE TABLE {table} AS SELECT * FROM read_csv_auto('{path}', header=true, all_varchar=false, sample_size=-1)""")
    n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  {table:20s} -> {n:>10,} rows")

cdc_path = r"C:\Users\modir\James\projects\medicare-claims-analytics\data\cdc_drug_overdose.csv"
con.execute(f"CREATE TABLE cdc_drug_overdose AS SELECT * FROM read_csv_auto('{cdc_path}')")
n = con.execute("SELECT COUNT(*) FROM cdc_drug_overdose").fetchone()[0]
print(f"  cdc_drug_overdose      -> {n:>10,} rows")

con.close()
print(f"\nDuckDB: {os.path.getsize(db_path)/1024/1024:.1f} MB")
