import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.db.connection import init_db
from backend.graph.model import reload_graph

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("DB_PATH", "data/cmdb.db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db(DB_PATH)
    try:
        reload_graph(DB_PATH)
        logger.info("networkx graph loaded at startup")
    except Exception as exc:
        logger.warning("Graph load skipped at startup (DB may be empty): %s", exc)
    yield
    # Shutdown — nothing to clean up


app = FastAPI(
    title="IT Application Knowledge Graph",
    description="Baptist Health South Florida CMDB — GraphRAG platform (Epic 1)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
