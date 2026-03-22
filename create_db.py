import sqlite3

conn = sqlite3.connect("voting.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS voters")
cursor.execute("DROP TABLE IF EXISTS votes")
cursor.execute("DROP TABLE IF EXISTS migrated_votes")
cursor.execute("DROP TABLE IF EXISTS fraud_logs")

cursor.execute(
    """
CREATE TABLE voters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aadhaar_no TEXT UNIQUE,
    name TEXT,
    dob TEXT,
    city TEXT,
    fingerprint TEXT,
    voted INTEGER DEFAULT 0
)
"""
)

cursor.execute(
    """
CREATE TABLE votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aadhaar_no TEXT,
    candidate TEXT,
    city TEXT
)
"""
)

cursor.execute(
    """
CREATE TABLE migrated_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aadhaar_no TEXT,
    candidate TEXT,
    registered_city TEXT,
    voting_city TEXT
)
"""
)

cursor.execute(
    """
CREATE TABLE fraud_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aadhaar_no TEXT,
    issue TEXT
)
"""
)

conn.commit()
conn.close()

print("✅ Database created successfully!")
