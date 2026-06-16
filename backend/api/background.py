import asyncio
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

ETL_RUNNING: bool = False
PROGRESS_QUEUES: dict[str, asyncio.Queue] = {}


async def run_etl_background(file_path: str, run_id: str, db_path: str = "data/cmdb.db") -> None:
    """
    Background task: run ETL pipeline, broadcast progress via asyncio.Queue,
    clean up temp file and running flag on completion.
    """
    global ETL_RUNNING
    import asyncio as _asyncio

    queue: asyncio.Queue = asyncio.Queue(maxsize=500)
    PROGRESS_QUEUES[run_id] = queue

    loop = asyncio.get_event_loop()

    try:
        # Run the blocking ETL in a thread executor so the event loop stays responsive
        from backend.etl.ingest import run_etl
        await loop.run_in_executor(
            None,
            lambda: run_etl(file_path, db_path=db_path, progress_queue=queue),
        )
    except Exception as exc:
        logger.error("Background ETL error (run_id=%s): %s", run_id, exc)
    finally:
        ETL_RUNNING = False
        # Remove queue after a short delay so WebSocket can drain remaining messages
        await asyncio.sleep(2)
        PROGRESS_QUEUES.pop(run_id, None)
        # Delete temp file
        try:
            os.unlink(file_path)
        except OSError:
            pass
