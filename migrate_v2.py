"""Run this once to add v2 columns to existing database."""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "tiktok_analyzer.db")


def migrate():
    if not os.path.exists(DB_PATH):
        print("No database found. It will be created fresh on next app start.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    new_cols = [
        ("version_number", "INTEGER DEFAULT 1"),
        ("hook_style", "TEXT"),
        ("is_favorite", "BOOLEAN DEFAULT 0"),
        ("current_script", "TEXT"),
    ]
    for col_name, col_type in new_cols:
        try:
            cursor.execute(f"ALTER TABLE adaptations ADD COLUMN {col_name} {col_type}")
            print(f"Added column adaptations.{col_name}")
        except sqlite3.OperationalError:
            print(f"Column adaptations.{col_name} already exists")

    cursor.execute("UPDATE adaptations SET current_script = adapted_script WHERE current_script IS NULL")
    print(f"Backfilled current_script for {cursor.rowcount} rows")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cross_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_ids TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created table cross_analyses")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adaptation_id INTEGER NOT NULL REFERENCES adaptations(id),
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created table chat_messages")

    conn.commit()
    conn.close()
    print("Migration complete!")


if __name__ == "__main__":
    migrate()
