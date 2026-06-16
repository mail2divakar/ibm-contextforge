import argparse
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from backend.db.connection import init_db
from backend.etl.ingest import SchemaValidationError, run_etl

DB_PATH = "data/cmdb.db"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Load a Baptist Health CMDB XLSX export into the knowledge graph database."
    )
    parser.add_argument("--file", required=True, help="Path to the CMDB .xlsx export file")
    parser.add_argument("--db", default=DB_PATH, help="SQLite database path (default: data/cmdb.db)")
    args = parser.parse_args()

    init_db(args.db)

    print(f"Validating schema…")
    try:
        result = run_etl(args.file, db_path=args.db)
    except SchemaValidationError as exc:
        print(f"ERROR: Schema validation failed. Missing columns: {exc.missing}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"ERROR: File not found: {args.file}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: ETL failed — {exc}", file=sys.stderr)
        return 1

    print(
        f"SUCCESS: {result['records_loaded']} records loaded. "
        f"{result['records_skipped']} skipped."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
