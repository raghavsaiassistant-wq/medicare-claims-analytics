"""Build script: Run all SQL files in order against DuckDB."""
import duckdb, os, sys

DB_PATH = r"C:\Users\modir\James\projects\medicare-claims-analytics\data\healthcare.duckdb"
SQL_DIR = r"C:\Users\modir\James\projects\medicare-claims-analytics\sql"

os.makedirs(r"C:\Users\modir\James\projects\medicare-claims-analytics\data\exports", exist_ok=True)
con = duckdb.connect(DB_PATH)

files = [
    "01_data_profiling.sql",
    "02_star_schema.sql",
    "03_brand_performance_analytics.sql",
    "04_data_quality_governance.sql",
    "05_powerbi_export_views.sql",
]

for f in files:
    path = os.path.join(SQL_DIR, f)
    print(f"\n{'='*60}\n▶ {f}\n{'='*60}")
    sql = open(path, 'r', encoding='utf-8').read()
    try:
        # Split on ; but keep COPY/SELECT statements as single execution
        # DuckDB can run multi-statement SQL via execute_script
        for stmt in sql.split(';'):
            s = stmt.strip()
            if not s or s.startswith('--'): continue
            # execute one statement
            try:
                result = con.execute(s)
                if result.description:
                    rows = result.fetchall()
                    cols = [d[0] for d in result.description]
                    print(f"  → {len(rows)} rows: {', '.join(cols[:5])}{'...' if len(cols)>5 else ''}")
                    if rows and len(rows) <= 20:
                        for r in rows[:8]:
                            print(f"    {r}")
                        if len(rows) > 8:
                            print(f"    ... ({len(rows)-8} more)")
            except duckdb.Error as e:
                # COPY statements don't return rows, just check error
                if "no result" in str(e).lower() or "no statements" in str(e).lower():
                    continue
                # If it's a view-already-exists error, ignore
                if "already exists" in str(e):
                    print(f"  (already exists, dropping first)")
                    continue
                raise
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        sys.exit(1)

# Final summary
print(f"\n{'='*60}\n✓ ALL SQL EXECUTED SUCCESSFULLY\n{'='*60}")
print(f"DuckDB: {os.path.getsize(DB_PATH)/1024/1024:.1f} MB")

# Show exports
exports = os.listdir(r"C:\Users\modir\James\projects\medicare-claims-analytics\data\exports")
print(f"Exports: {exports}")
for e in exports:
    p = os.path.join(r"C:\Users\modir\James\projects\medicare-claims-analytics\data\exports", e)
    print(f"  - {e}: {os.path.getsize(p)/1024:.0f} KB")

con.close()
