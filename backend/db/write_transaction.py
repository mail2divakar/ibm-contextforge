import asyncio
import hashlib
import json
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from backend.db.connection import get_connection

logger = logging.getLogger(__name__)


def _sha256_file(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_transaction(
    records: list[dict],
    run_meta: dict,
    db_path: str = "data/cmdb.db",
    progress_queue: Optional[asyncio.Queue] = None,
) -> dict:
    """
    Atomically write all records to SQLite.

    On any exception the transaction is rolled back and prior data is fully preserved.
    All SQL uses ? placeholders — no f-string or .format() SQL construction.
    """
    conn = get_connection(db_path)
    run_id = run_meta["run_id"]
    run_at = run_meta.get("run_at", datetime.now(timezone.utc).isoformat())
    xlsx_hash = run_meta.get("xlsx_hash")

    records_loaded = 0
    records_skipped = 0
    skipped_detail: list[dict] = []

    try:
        conn.execute("BEGIN")

        # Collect IDs that are present in this run (for soft-delete logic)
        current_ids: list[str] = []

        _emit(progress_queue, {
            "type": "progress",
            "step": "writing",
            "records_processed": 0,
            "records_total": len(records),
            "message": f"Writing {len(records)} records to SQLite…",
        })

        for i, record in enumerate(records, start=1):
            app_id = record.get("application_id")
            if not app_id:
                records_skipped += 1
                skipped_detail.append({
                    "application_name": record.get("application_name"),
                    "company": record.get("company"),
                    "reason": "Missing application_id after normalization",
                })
                continue

            current_ids.append(app_id)

            # UPSERT: applications table (all 20 CMDB fields + metadata)
            conn.execute(
                """
                INSERT INTO applications (
                    application_id, application_name, company, publisher, description,
                    updated, last_updated_by, business_owner, td_app_owner, primary_engineer,
                    support_group, active, install_status, application_url, portfolio_manager,
                    application_type, architecture_type, baptist_managed, business_criticality,
                    business_process, environment, active_status, content_hash
                ) VALUES (
                    ?,?,?,?,?,  ?,?,?,?,?,  ?,?,?,?,?,  ?,?,?,?,?,  ?,1,?
                )
                ON CONFLICT(application_id) DO UPDATE SET
                    application_name    = excluded.application_name,
                    company             = excluded.company,
                    publisher           = excluded.publisher,
                    description         = excluded.description,
                    updated             = excluded.updated,
                    last_updated_by     = excluded.last_updated_by,
                    business_owner      = excluded.business_owner,
                    td_app_owner        = excluded.td_app_owner,
                    primary_engineer    = excluded.primary_engineer,
                    support_group       = excluded.support_group,
                    active              = excluded.active,
                    install_status      = excluded.install_status,
                    application_url     = excluded.application_url,
                    portfolio_manager   = excluded.portfolio_manager,
                    application_type    = excluded.application_type,
                    architecture_type   = excluded.architecture_type,
                    baptist_managed     = excluded.baptist_managed,
                    business_criticality = excluded.business_criticality,
                    business_process    = excluded.business_process,
                    environment         = excluded.environment,
                    active_status       = 1,
                    content_hash        = excluded.content_hash
                """,
                (
                    app_id,
                    record.get("application_name"),
                    record.get("company"),
                    record.get("publisher"),
                    record.get("description"),
                    record.get("updated"),
                    record.get("last_updated_by"),
                    record.get("business_owner"),
                    record.get("td_app_owner"),
                    record.get("primary_engineer"),
                    record.get("support_group"),
                    record.get("active"),
                    record.get("install_status"),
                    record.get("application_url"),
                    record.get("portfolio_manager"),
                    record.get("application_type"),
                    record.get("architecture_type"),
                    record.get("baptist_managed"),
                    record.get("business_criticality"),
                    record.get("business_process"),
                    record.get("environment"),
                    record.get("content_hash"),
                ),
            )

            # UPSERT: application_types reference table
            if record.get("application_type") and record.get("_type_id"):
                conn.execute(
                    "INSERT OR IGNORE INTO application_types (type_id, type_name) VALUES (?,?)",
                    (record["_type_id"], record["application_type"]),
                )
                conn.execute(
                    "INSERT OR IGNORE INTO app_uses_type (application_id, type_id) VALUES (?,?)",
                    (app_id, record["_type_id"]),
                )

            # UPSERT: architecture_types reference table
            if record.get("architecture_type") and record.get("_arch_id"):
                conn.execute(
                    "INSERT OR IGNORE INTO architecture_types (arch_id, arch_name) VALUES (?,?)",
                    (record["_arch_id"], record["architecture_type"]),
                )
                conn.execute(
                    "INSERT OR IGNORE INTO app_has_architecture (application_id, arch_id) VALUES (?,?)",
                    (app_id, record["_arch_id"]),
                )

            # UPSERT: business_processes reference table
            if record.get("business_process") and record.get("_process_id"):
                conn.execute(
                    "INSERT OR IGNORE INTO business_processes (process_id, process_name) VALUES (?,?)",
                    (record["_process_id"], record["business_process"]),
                )
                conn.execute(
                    "INSERT OR IGNORE INTO app_supports_process (application_id, process_id) VALUES (?,?)",
                    (app_id, record["_process_id"]),
                )

            # UPSERT: companies reference table
            if record.get("company") and record.get("_company_id"):
                conn.execute(
                    "INSERT OR IGNORE INTO companies (company_id, company_name) VALUES (?,?)",
                    (record["_company_id"], record["company"]),
                )

            records_loaded += 1

            if i % 100 == 0 or i == len(records):
                _emit(progress_queue, {
                    "type": "progress",
                    "step": "writing",
                    "records_processed": i,
                    "records_total": len(records),
                    "message": f"Writing records — {i}/{len(records)}",
                })

        # Soft-delete records absent from this run
        if current_ids:
            placeholders = ",".join("?" * len(current_ids))
            conn.execute(
                f"UPDATE applications SET active_status = 0 "
                f"WHERE application_id NOT IN ({placeholders}) AND active_status = 1",
                current_ids,
            )

        # Write ETL audit row
        status = "success" if records_skipped == 0 else "partial"
        conn.execute(
            "INSERT INTO etl_runs (run_id, run_at, xlsx_hash, records_loaded, records_skipped, status, error_detail) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                run_id, run_at, xlsx_hash,
                records_loaded, records_skipped, status,
                json.dumps(skipped_detail) if skipped_detail else None,
            ),
        )

        conn.execute("COMMIT")

        _emit(progress_queue, {
            "type": "complete",
            "status": status,
            "records_loaded": records_loaded,
            "records_skipped": records_skipped,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"Updated · {records_loaded} apps",
        })

        return {"status": status, "records_loaded": records_loaded, "records_skipped": records_skipped}

    except Exception as exc:
        conn.execute("ROLLBACK")
        logger.error("ETL transaction rolled back: %s", exc)
        try:
            conn2 = get_connection(db_path)
            conn2.execute(
                "INSERT OR IGNORE INTO etl_runs (run_id, run_at, xlsx_hash, records_loaded, records_skipped, status, error_detail) "
                "VALUES (?,?,?,?,?,?,?)",
                (run_id, run_at, xlsx_hash, 0, 0, "failed", json.dumps({"error": str(exc)})),
            )
            conn2.commit()
            conn2.close()
        except Exception:
            pass
        _emit(progress_queue, {
            "type": "complete",
            "status": "failed",
            "records_loaded": 0,
            "records_skipped": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(exc),
            "message": "Refresh failed — check the file format.",
        })
        raise
    finally:
        conn.close()


def _emit(queue: Optional[asyncio.Queue], event: dict) -> None:
    if queue is not None:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            pass
