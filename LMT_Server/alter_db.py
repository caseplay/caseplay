import sys
import os

# add parent dir to path so we can import utils.db
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.db import get_db_connection

def alter_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if remaining_plays exists
        cursor.execute("SHOW COLUMNS FROM users LIKE 'remaining_plays'")
        result = cursor.fetchone()
        if not result:
            cursor.execute("ALTER TABLE users ADD COLUMN remaining_plays INT DEFAULT 1;")
            print("Added remaining_plays column")

        # Check if is_admin exists
        cursor.execute("SHOW COLUMNS FROM users LIKE 'is_admin'")
        result = cursor.fetchone()
        if not result:
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;")
            print("Added is_admin column")

        conn.commit()
        cursor.close()
        conn.close()
        print("Database alter complete.")
    except Exception as e:
        print(f"Error altering database: {e}")

if __name__ == "__main__":
    alter_db()
