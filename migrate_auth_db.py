import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "app.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print(f"Database: {DB_PATH}")

cursor.execute("PRAGMA table_info(users)")
columns = [row[1] for row in cursor.fetchall()]

print("Existing users columns:")
print(columns)

migrations = {
    "full_name": "TEXT",
    "phone_number": "TEXT",
    "password_hash": "TEXT",
    "auth_provider": "TEXT",
    "provider_id": "TEXT",
    "created_at": "DATETIME",
}

for column, column_type in migrations.items():
    if column not in columns:
        print(f"Adding column: {column}")

        if column == "created_at":
            cursor.execute(
                """
                ALTER TABLE users
                ADD COLUMN created_at DATETIME
                DEFAULT CURRENT_TIMESTAMP
                """
            )
        else:
            cursor.execute(
                f"""
                ALTER TABLE users
                ADD COLUMN {column} {column_type}
                """
            )
    else:
        print(f"Already exists: {column}")

cursor.execute("PRAGMA table_info(users)")
current_columns = [row[1] for row in cursor.fetchall()]

if "email" in current_columns:
    cursor.execute(
        """
        UPDATE users
        SET full_name = COALESCE(NULLIF(full_name, ''), email)
        WHERE full_name IS NULL OR full_name = ''
        """
    )

cursor.execute(
    """
    UPDATE users
    SET auth_provider = 'password'
    WHERE auth_provider IS NULL OR auth_provider = ''
    """
)

conn.commit()

cursor.execute("PRAGMA table_info(users)")
final_columns = [row[1] for row in cursor.fetchall()]

print("\nFinal users columns:")
for column in final_columns:
    print(" -", column)

conn.close()

print("\nMigration completed successfully.")