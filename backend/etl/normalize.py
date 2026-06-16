import hashlib
import logging
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

_COTS_VARIANTS = {"cots", "commercial", "commercial off the shelf", "commercial off-the-shelf"}
_HOMEGROWN_VARIANTS = {"homegrown", "home grown", "custom", "in-house", "inhouse", "internal"}
_MANAGED_TRUE = {"true", "yes", "1", "y"}
_MANAGED_FALSE = {"false", "no", "0", "n"}


def normalize_application_type(raw: object, record_id: str = "") -> Optional[str]:
    if raw is None or (isinstance(raw, float) and raw != raw):  # NaN check
        return None
    value = str(raw).strip().lower()
    if not value:
        return None
    if value in _COTS_VARIANTS:
        return "COTS"
    if value in _HOMEGROWN_VARIANTS:
        return "Homegrown"
    logger.warning("Unknown application_type '%s' for record '%s' — storing NULL", raw, record_id)
    return None


def normalize_baptist_managed(raw: object, record_id: str = "") -> Optional[int]:
    if raw is None or (isinstance(raw, float) and raw != raw):
        return None
    value = str(raw).strip().lower()
    if not value:
        return None
    if value in _MANAGED_TRUE:
        return 1
    if value in _MANAGED_FALSE:
        return 0
    logger.warning("Unknown baptist_managed '%s' for record '%s' — storing NULL", raw, record_id)
    return None


def strip_strings(record: dict) -> dict:
    return {
        k: (v.strip() if isinstance(v, str) else v)
        for k, v in record.items()
    }


def empty_to_none(record: dict) -> dict:
    return {
        k: (None if isinstance(v, str) and v.strip() == "" else v)
        for k, v in record.items()
    }


def compute_content_hash(name: Optional[str], description: Optional[str]) -> str:
    payload = f"{name or ''}{description or ''}"
    return hashlib.sha256(payload.encode()).hexdigest()


def build_embed_payload(record: dict) -> str:
    """
    Returns the text to embed for a given application record.

    EXCLUDED fields (PII / sensitive — must never appear in embedding input or AI payloads):
        - business_owner
        - td_app_owner
        - primary_engineer
        - last_updated_by
        - application_url
        - portfolio_manager
    """
    name = record.get("application_name") or ""
    description = record.get("description") or ""
    return f"{name} {description}".strip()


def generate_or_preserve_uuid(
    application_name: Optional[str],
    company: Optional[str],
    uuid_map: dict,
) -> str:
    key = (
        (application_name or "").strip().lower(),
        (company or "").strip().lower(),
    )
    if key in uuid_map:
        return uuid_map[key]
    return str(uuid.uuid4())
