"""Check Supabase table schemas via direct PostgreSQL connection."""
import psycopg2

conn = psycopg2.connect(
    "postgresql://postgres:DodiroquNew007%3F@db.ctgegqikstoaafpgdkpt.supabase.co:5432/postgres"
)
cur = conn.cursor()

cur.execute("""
    SELECT table_name, column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position
""")
rows = cur.fetchall()

current_table = None
for table, col, dtype, nullable, default in rows:
    if table != current_table:
        print(f"\n=== {table} ===")
        current_table = table
    null_str = "" if nullable == "YES" else " NOT NULL"
    default_str = f" DEFAULT {str(default)[:40]}" if default else ""
    print(f"  {col}: {dtype}{null_str}{default_str}")

conn.close()
print("\nDone.")
