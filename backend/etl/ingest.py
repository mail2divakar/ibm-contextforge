import asyncio
import hashlib
import logging
import uuid
from pathlib import Path
from typing import Optional

import pandas as pd

from backend.db.connection import get_connection
from backend.db.write_transaction import write_transaction
from backend.etl.embed import embed_changed_records
from backend.etl.normalize import (
    build_embed_payload,
    compute_content_hash,
    empty_to_none,
    generate_or_preserve_uuid,
    normalize_application_type,
    normalize_baptist_managed,
    strip_strings,
)
from backend.graph.model import reload_graph

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "Application Name",
    "Company",
    "Publisher",
    "Description",
    "Updated",
    "Last Updated By",
    "Business Owner",
    "T&D Application Owner",
    "Primary Engineer",
    "Application Support Group",
    "Active",
    "Install Status",
    "Application URL",
    "Application Portfolio Manager",
    "Application Type",
    "Architecture Type",
    "Baptist Managed",
    "Business Criticality",
    "Business Process",
    "Environment",
]


class SchemaValidationError(ValueError):
    def __init__(self, missing: list[str]):
        self.missing = missing
        super().__init__(f"Missing columns: {missing}")


def validate_schema(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise SchemaValidationError(missing)


def _build_uuid_map(db_path: str) -> dict:
    """Load existing (name, company) → application_id mapping from SQLite."""
    try:
        conn = get_connection(db_path)
        rows = conn.execute(
            "SELECT application_name, company, application_id FROM applications"
        ).fetchall()
        conn.close()
        return {
            (
                (r["application_name"] or "").strip().lower(),
                (r["company"] or "").strip().lower(),
            ): r["application_id"]
            for r in rows
        }
    except Exception:
        return {}


def _build_ref_maps(db_path: str) -> tuple[dict, dict, dict, dict]:
    """Load existing reference entity (name → id) maps for upsert logic."""
    try:
        conn = get_connection(db_path)
        type_map = {r["type_name"]: r["type_id"] for r in conn.execute("SELECT type_id, type_name FROM application_types")}
        arch_map = {r["arch_name"]: r["arch_id"] for r in conn.execute("SELECT arch_id, arch_name FROM architecture_types")}
        proc_map = {r["process_name"]: r["process_id"] for r in conn.execute("SELECT process_id, process_name FROM business_processes")}
        comp_map = {r["company_name"]: r["company_id"] for r in conn.execute("SELECT company_id, company_name FROM companies")}
        conn.close()
        return type_map, arch_map, proc_map, comp_map
    except Exception:
        return {}, {}, {}, {}


def parse_row(row: pd.Series, uuid_map: dict, type_map: dict, arch_map: dict, proc_map: dict, comp_map: dict) -> dict:
    name = str(row.get("Application Name", "") or "").strip() or None
    company = str(row.get("Company", "") or "").strip() or None
    app_type = normalize_application_type(row.get("Application Type"), record_id=str(name))
    baptist = normalize_baptist_managed(row.get("Baptist Managed"), record_id=str(name))
    description = str(row.get("Description", "") or "").strip() or None
    arch_type = str(row.get("Architecture Type", "") or "").strip() or None
    business_process = str(row.get("Business Process", "") or "").strip() or None

    app_id = generate_or_preserve_uuid(name, company, uuid_map)
    uuid_map[((name or "").lower(), (company or "").lower())] = app_id

    # Resolve or create reference entity IDs
    type_id = None
    if app_type:
        if app_type not in type_map:
            type_map[app_type] = str(uuid.uuid4())
        type_id = type_map[app_type]

    arch_id = None
    if arch_type:
        if arch_type not in arch_map:
            arch_map[arch_type] = str(uuid.uuid4())
        arch_id = arch_map[arch_type]

    process_id = None
    if business_process:
        if business_process not in proc_map:
            proc_map[business_process] = str(uuid.uuid4())
        process_id = proc_map[business_process]

    company_id = None
    if company:
        if company not in comp_map:
            comp_map[company] = str(uuid.uuid4())
        company_id = comp_map[company]

    return {
        "application_id": app_id,
        "application_name": name,
        "company": company,
        "publisher": str(row.get("Publisher", "") or "").strip() or None,
        "description": description,
        "updated": str(row.get("Updated", "") or "").strip() or None,
        "last_updated_by": str(row.get("Last Updated By", "") or "").strip() or None,
        "business_owner": str(row.get("Business Owner", "") or "").strip() or None,
        "td_app_owner": str(row.get("T&D Application Owner", "") or "").strip() or None,
        "primary_engineer": str(row.get("Primary Engineer", "") or "").strip() or None,
        "support_group": str(row.get("Application Support Group", "") or "").strip() or None,
        "active": int(row.get("Active", 1)) if row.get("Active") is not None else None,
        "install_status": str(row.get("Install Status", "") or "").strip() or None,
        "application_url": str(row.get("Application URL", "") or "").strip() or None,
        "portfolio_manager": str(row.get("Application Portfolio Manager", "") or "").strip() or None,
        "application_type": app_type,
        "architecture_type": arch_type,
        "baptist_managed": baptist,
        "business_criticality": str(row.get("Business Criticality", "") or "").strip() or None,
        "business_process": business_process,
        "environment": str(row.get("Environment", "") or "").strip() or None,
        "content_hash": compute_content_hash(name, description),
        # Internal reference IDs (used by write_transaction for edge tables)
        "_type_id": type_id,
        "_arch_id": arch_id,
        "_process_id": process_id,
        "_company_id": company_id,
    }


def run_etl(
    file_path: str,
    db_path: str = "data/cmdb.db",
    progress_queue: Optional[asyncio.Queue] = None,
) -> dict:
    """
    Full ETL pipeline: read XLSX → validate → normalize → write SQLite → reload graph.
    Returns {"status": ..., "records_loaded": ..., "records_skipped": ...}.
    Raises SchemaValidationError on bad schema (before touching the DB).
    """
    import uuid as _uuid
    from datetime import datetime, timezone

    run_id = str(_uuid.uuid4())

    _emit(progress_queue, {
        "type": "progress",
        "step": "reading",
        "records_processed": 0,
        "records_total": 0,
        "message": "Reading XLSX…",
    })

    logger.info("ETL starting: %s", file_path)
    df = pd.read_excel(file_path, engine="openpyxl")

    validate_schema(df)

    xlsx_hash = _hash_file(file_path)
    total = len(df)

    _emit(progress_queue, {
        "type": "progress",
        "step": "normalizing",
        "records_processed": 0,
        "records_total": total,
        "message": f"Normalizing {total} records…",
    })

    uuid_map = _build_uuid_map(db_path)
    type_map, arch_map, proc_map, comp_map = _build_ref_maps(db_path)

    records = []
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        rec = parse_row(row, uuid_map, type_map, arch_map, proc_map, comp_map)
        records.append(rec)
        if i % 250 == 0 or i == total:
            _emit(progress_queue, {
                "type": "progress",
                "step": "normalizing",
                "records_processed": i,
                "records_total": total,
                "message": f"Normalizing fields — {i}/{total} records",
            })

    run_meta = {
        "run_id": run_id,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "xlsx_hash": xlsx_hash,
    }

    result = write_transaction(records, run_meta, db_path=db_path, progress_queue=progress_queue)

    # Reload graph after successful write
    try:
        reload_graph(db_path)
    except Exception as exc:
        logger.warning("Graph reload failed after ETL: %s", exc)

    # Embed changed records (Epic 3 stub — no-op in Epic 1)
    try:
        embed_changed_records(records, db_path=db_path)
    except Exception as exc:
        logger.warning("Embed step failed (stub): %s", exc)

    logger.info("ETL complete: loaded=%d, skipped=%d", result["records_loaded"], result["records_skipped"])
    return result


def _emit(queue: Optional[asyncio.Queue], event: dict) -> None:
    if queue is not None:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            pass


def _hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
