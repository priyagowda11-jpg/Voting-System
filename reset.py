import sqlite3

# Connect to your database
conn = sqlite3.connect("voting.db")
cursor = conn.cursor()

# Add the missing phone column
try:
    cursor.execute("ALTER TABLE voters ADD COLUMN phone TEXT")
    conn.commit()
    print("✅ Successfully added 'phone' column to voters table!")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("ℹ️ Column 'phone' already exists")
    else:
        print(f"❌ Error: {e}")

conn.close()
