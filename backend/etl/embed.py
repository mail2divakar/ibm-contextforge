"""
Embedding stub for Epic 1.

Epic 3 will fully implement this module using:
  - Vertex AI text-embedding-004 for generating embedding vectors
  - ChromaDB (SQLite-backed, data/chroma/) for local vector storage

ChromaDB collection contract:
  collection_name : "applications"
  document_id     : application_id (UUID)
  document_text   : build_embed_payload(record)  — name + description ONLY
  metadata stored : application_type, business_process, baptist_managed

PII fields EXCLUDED from all embedding payloads:
  business_owner, td_app_owner, primary_engineer, last_updated_by,
  application_url, portfolio_manager

Vertex AI SDK pattern (Epic 3 implementation):
    import vertexai
    from vertexai.language_models import TextEmbeddingModel

    vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=VERTEX_AI_LOCATION)
    model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    embeddings = model.get_embeddings([build_embed_payload(record)])
    vector = embeddings[0].values
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def embed_changed_records(
    records: list[dict],
    db_path: str = "data/cmdb.db",
    chroma_path: str = "data/chroma",
) -> None:
    """No-op stub. Epic 3 replaces this with Vertex AI + ChromaDB upsert."""
    if records:
        logger.info("embed_changed_records: Epic 3 stub — %d records not embedded", len(records))
