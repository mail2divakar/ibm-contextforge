import sys
from backend.db.connection import init_db

DB_PATH = "data/cmdb.db"

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else DB_PATH
    init_db(db_path)
    print(f"Schema initialized at {db_path}")
