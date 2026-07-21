
import duckdb, os
db_path = r"C:\Users\modir\James\projects\medicare-claims-analytics\data\healthcare.duckdb"
cdc_csv = r"C:\Users\modir\James\projects\medicare-claims-analytics\data\cdc_drug_overdose.csv"
con = duckdb.connect(db_path)
con.execute(f"CREATE TABLE cdc_drug_overdose AS SELECT * FROM read_csv_auto('{cdc_csv}')")
n = con.execute("SELECT COUNT(*) FROM cdc_drug_overdose").fetchone()[0]
print(f"cdc_drug_overdose -> {n} rows")
print(f"DuckDB: {os.path.getsize(db_path)/1024/1024:.1f} MB")
