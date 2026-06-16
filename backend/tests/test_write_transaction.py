import os
import tempfile
import uuid

import pytest

from backend.db.connection import get_connection, init_db


def _make_record(name: str = "Test App", company: str = "BHMG", app_type: str = "COTS") -> dict:
    app_id = str(uuid.uuid4())
    type_id = str(uuid.uuid4())
    return {
        "application_id": app_id,
        "application_name": name,
        "company": company,
        "publisher": None,
        "description": "Test",
        "updated": None,
        "last_updated_by": None,
        "business_owner": None,
        "td_app_owner": None,
        "primary_engineer": None,
        "support_group": None,
        "active": 1,
        "install_status": "Installed",
        "application_url": None,
        "portfolio_manager": None,
        "application_type": app_type,
        "architecture_type": None,
        "baptist_managed": 1,
        "business_criticality": None,
        "business_process": None,
        "environment": "Production",
        "content_hash": "abc123",
        "_type_id": type_id,
        "_arch_id": None,
        "_process_id": None,
        "_company_id": str(uuid.uuid4()),
    }


@pytest.fixture()
def db(tmp_path):
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


class TestWriteTransaction:
    def test_inserts_records(self, db):
        from backend.db.write_transaction import write_transaction
        records = [_make_record("App A"), _make_record("App B")]
        run_meta = {"run_id": str(uuid.uuid4()), "xlsx_hash": "h1"}

        result = write_transaction(records, run_meta, db_path=db)

        assert result["records_loaded"] == 2
        conn = get_connection(db)
        count = conn.execute("SELECT COUNT(*) FROM applications WHERE active_status=1").fetchone()[0]
        conn.close()
        assert count == 2

    def test_etl_runs_logged(self, db):
        from backend.db.write_transaction import write_transaction
        run_id = str(uuid.uuid4())
        write_transaction([_make_record()], {"run_id": run_id}, db_path=db)

        conn = get_connection(db)
        row = conn.execute("SELECT status FROM etl_runs WHERE run_id=?", (run_id,)).fetchone()
        conn.close()
        assert row["status"] in ("success", "partial")

    def test_upsert_preserves_uuid(self, db):
        from backend.db.write_transaction import write_transaction
        rec = _make_record("Stable App")
        run_id_1 = str(uuid.uuid4())
        write_transaction([rec], {"run_id": run_id_1}, db_path=db)

        # Re-run with same application_id
        run_id_2 = str(uuid.uuid4())
        write_transaction([rec], {"run_id": run_id_2}, db_path=db)

        conn = get_connection(db)
        count = conn.execute(
            "SELECT COUNT(*) FROM applications WHERE application_name='Stable App'"
        ).fetchone()[0]
        conn.close()
        assert count == 1  # no duplicates

    def test_soft_delete_absent_records(self, db):
        from backend.db.write_transaction import write_transaction
        rec_a = _make_record("App A")
        rec_b = _make_record("App B")
        write_transaction([rec_a, rec_b], {"run_id": str(uuid.uuid4())}, db_path=db)

        # Re-ingest with only rec_a → rec_b should be soft-deleted
        write_transaction([rec_a], {"run_id": str(uuid.uuid4())}, db_path=db)

        conn = get_connection(db)
        b_status = conn.execute(
            "SELECT active_status FROM applications WHERE application_id=?", (rec_b["application_id"],)
        ).fetchone()["active_status"]
        conn.close()
        assert b_status == 0
