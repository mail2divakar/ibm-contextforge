import pytest
from backend.etl.normalize import (
    build_embed_payload,
    compute_content_hash,
    generate_or_preserve_uuid,
    normalize_application_type,
    normalize_baptist_managed,
    strip_strings,
    empty_to_none,
)


class TestNormalizeApplicationType:
    def test_cots_exact(self):
        assert normalize_application_type("COTS") == "COTS"

    def test_cots_lowercase(self):
        assert normalize_application_type("cots") == "COTS"

    def test_commercial(self):
        assert normalize_application_type("commercial") == "COTS"

    def test_homegrown(self):
        assert normalize_application_type("Homegrown") == "Homegrown"

    def test_custom(self):
        assert normalize_application_type("custom") == "Homegrown"

    def test_none_input(self):
        assert normalize_application_type(None) is None

    def test_empty_string(self):
        assert normalize_application_type("") is None

    def test_unknown_returns_none(self):
        assert normalize_application_type("SaaS") is None

    def test_nan_returns_none(self):
        import math
        assert normalize_application_type(float("nan")) is None


class TestNormalizeBaptistManaged:
    def test_true_string(self):
        assert normalize_baptist_managed("True") == 1

    def test_yes_string(self):
        assert normalize_baptist_managed("Yes") == 1

    def test_one_string(self):
        assert normalize_baptist_managed("1") == 1

    def test_false_string(self):
        assert normalize_baptist_managed("False") == 0

    def test_no_string(self):
        assert normalize_baptist_managed("No") == 0

    def test_zero_string(self):
        assert normalize_baptist_managed("0") == 0

    def test_none_input(self):
        assert normalize_baptist_managed(None) is None

    def test_unknown_returns_none(self):
        assert normalize_baptist_managed("maybe") is None


class TestStripStrings:
    def test_strips_whitespace(self):
        result = strip_strings({"name": "  App  ", "count": 5})
        assert result["name"] == "App"
        assert result["count"] == 5

    def test_handles_none(self):
        result = strip_strings({"name": None})
        assert result["name"] is None


class TestEmptyToNone:
    def test_empty_string_to_none(self):
        result = empty_to_none({"name": ""})
        assert result["name"] is None

    def test_whitespace_to_none(self):
        result = empty_to_none({"name": "   "})
        assert result["name"] is None

    def test_non_empty_kept(self):
        result = empty_to_none({"name": "App"})
        assert result["name"] == "App"


class TestComputeContentHash:
    def test_hash_is_stable(self):
        h1 = compute_content_hash("App", "Description")
        h2 = compute_content_hash("App", "Description")
        assert h1 == h2

    def test_hash_changes_on_name_change(self):
        h1 = compute_content_hash("App A", "Desc")
        h2 = compute_content_hash("App B", "Desc")
        assert h1 != h2

    def test_none_values_handled(self):
        h = compute_content_hash(None, None)
        assert isinstance(h, str) and len(h) == 64


class TestBuildEmbedPayload:
    def test_combines_name_and_description(self):
        record = {
            "application_name": "3D Scanner",
            "description": "Volumetric imaging",
            "business_owner": "Alice",     # PII — must not appear
            "td_app_owner": "Bob",          # PII — must not appear
        }
        payload = build_embed_payload(record)
        assert "3D Scanner" in payload
        assert "Volumetric imaging" in payload
        assert "Alice" not in payload
        assert "Bob" not in payload

    def test_handles_missing_description(self):
        payload = build_embed_payload({"application_name": "App"})
        assert payload == "App"


class TestGenerateOrPreserveUUID:
    def test_generates_new_uuid(self):
        uid = generate_or_preserve_uuid("App", "Co", {})
        assert len(uid) == 36  # UUID v4 format

    def test_preserves_existing_uuid(self):
        existing = "existing-uuid-1234"
        uid = generate_or_preserve_uuid("App", "Co", {("app", "co"): existing})
        assert uid == existing

    def test_case_insensitive_key(self):
        existing = "existing-uuid-1234"
        uid = generate_or_preserve_uuid("APP", "CO", {("app", "co"): existing})
        assert uid == existing
