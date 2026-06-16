import asyncio
import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from backend.api.background import ETL_RUNNING, PROGRESS_QUEUES, run_etl_background
from backend.db.connection import get_connection
from backend.graph.model import APP_GRAPH

router = APIRouter()

DB_PATH = os.environ.get("DB_PATH", "data/cmdb.db")


# ─────────────────────────────────────────────
# GET /api/health
# ─────────────────────────────────────────────

@router.get("/api/health")
def health():
    return {
        "status": "ok",
        "graph_loaded": APP_GRAPH is not None,
        "db_path": DB_PATH,
    }


# ─────────────────────────────────────────────
# GET /api/applications
# ─────────────────────────────────────────────

@router.get("/api/applications")
def list_applications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    application_type: Optional[str] = Query(default=None),
    business_process: Optional[str] = Query(default=None),
    company: Optional[str] = Query(default=None),
    baptist_managed: Optional[bool] = Query(default=None),
    q: Optional[str] = Query(default=None),
):
    conn = get_connection(DB_PATH)
    try:
        where_clauses = ["active_status = 1"]
        params: list = []

        if application_type:
            where_clauses.append("application_type = ?")
            params.append(application_type)
        if business_process:
            where_clauses.append("business_process = ?")
            params.append(business_process)
        if company:
            where_clauses.append("company = ?")
            params.append(company)
        if baptist_managed is not None:
            where_clauses.append("baptist_managed = ?")
            params.append(1 if baptist_managed else 0)
        if q:
            where_clauses.append("application_name LIKE ?")
            params.append(f"%{q}%")

        where_sql = " AND ".join(where_clauses)

        total = conn.execute(
            f"SELECT COUNT(*) FROM applications WHERE {where_sql}", params
        ).fetchone()[0]

        offset = (page - 1) * page_size
        rows = conn.execute(
            f"""
            SELECT application_id, application_name, company, publisher,
                   application_type, architecture_type, baptist_managed,
                   business_process, business_owner, install_status, active_status
            FROM applications
            WHERE {where_sql}
            ORDER BY application_name
            LIMIT ? OFFSET ?
            """,
            params + [page_size, offset],
        ).fetchall()

        results = [dict(r) for r in rows]
        pages = max(1, (total + page_size - 1) // page_size)

        return {
            "results": results,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
        }
    finally:
        conn.close()


# ─────────────────────────────────────────────
# GET /api/applications/{application_id}
# ─────────────────────────────────────────────

@router.get("/api/applications/{application_id}")
def get_application(application_id: str):
    conn = get_connection(DB_PATH)
    try:
        row = conn.execute(
            "SELECT * FROM applications WHERE application_id = ? AND active_status = 1",
            (application_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"Application not found: {application_id}")
        return dict(row)
    finally:
        conn.close()


# ─────────────────────────────────────────────
# POST /api/refresh
# ─────────────────────────────────────────────

@router.post("/api/refresh", status_code=202)
async def trigger_refresh(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    global ETL_RUNNING

    # File type check
    filename = file.filename or ""
    if not filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail=f"Only .xlsx files are accepted. Received: {file.content_type}",
        )

    # Concurrent ETL guard
    if ETL_RUNNING:
        raise HTTPException(
            status_code=409,
            detail="An ETL run is already in progress. Wait for completion before uploading a new file.",
        )

    # Save to temp file for background processing
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
    try:
        with os.fdopen(tmp_fd, "wb") as tmp_f:
            content = await file.read()
            tmp_f.write(content)
    except Exception:
        os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    # Early schema validation (synchronous, before triggering background)
    try:
        import pandas as pd
        from backend.etl.ingest import SchemaValidationError, validate_schema
        df = pd.read_excel(tmp_path, engine="openpyxl", nrows=0)
        validate_schema(df)
    except Exception as exc:
        os.unlink(tmp_path)
        if hasattr(exc, "missing"):
            raise HTTPException(
                status_code=400,
                detail="XLSX schema validation failed",
            )
        raise HTTPException(status_code=400, detail=f"Cannot read XLSX: {exc}")

    import backend.api.background as bg_module
    bg_module.ETL_RUNNING = True
    run_id = str(uuid.uuid4())

    background_tasks.add_task(run_etl_background, tmp_path, run_id, DB_PATH)

    return {
        "run_id": run_id,
        "status": "running",
        "message": f"ETL pipeline started. Connect to /ws/refresh?run_id={run_id} for progress.",
    }


# ─────────────────────────────────────────────
# GET /api/refresh/status
# ─────────────────────────────────────────────

@router.get("/api/refresh/status")
def refresh_status():
    conn = get_connection(DB_PATH)
    try:
        row = conn.execute(
            "SELECT run_id, run_at, status, records_loaded, records_skipped, xlsx_hash "
            "FROM etl_runs ORDER BY run_at DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return {
                "run_id": None,
                "run_at": None,
                "status": "never_run",
                "records_loaded": None,
                "records_skipped": None,
                "xlsx_hash": None,
            }
        return dict(row)
    finally:
        conn.close()


# ─────────────────────────────────────────────
# WS /ws/refresh
# ─────────────────────────────────────────────

@router.websocket("/ws/refresh")
async def ws_refresh(websocket: WebSocket, run_id: str = Query(...)):
    await websocket.accept()

    # Wait up to 5s for the queue to be registered by background task
    for _ in range(50):
        if run_id in PROGRESS_QUEUES:
            break
        await asyncio.sleep(0.1)

    queue = PROGRESS_QUEUES.get(run_id)
    if queue is None:
        await websocket.send_text(json.dumps({
            "type": "complete",
            "status": "failed",
            "message": "run_id not found or ETL already completed",
        }))
        await websocket.close()
        return

    try:
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_text(json.dumps(msg))
                if msg.get("type") == "complete":
                    break
            except asyncio.TimeoutError:
                # Send a heartbeat ping to keep connection alive
                await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
