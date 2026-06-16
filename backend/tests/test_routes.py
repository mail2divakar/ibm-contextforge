import os
import tempfile

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.etl.ingest import REQUIRED_COLUMNS


@pytest.fixture()
def db_path(tmp_path):
    from backend.db.connection import init_db
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


@pytest.fixture()
def seeded_db(db_path):
    """DB with two active application records."""
    from backend.db.connection import get_connection
    import uuid as _uuid

    conn = get_connection(db_path)
    for name, app_type in [("App Alpha", "COTS"), ("App Beta", "Homegrown")]:
        conn.execute(
            "INSERT INTO applications (application_id, application_name, company, application_type, active_status) "
            "VALUES (?,?,?,?,1)",
            (str(_uuid.uuid4()), name, "Baptist Hospital", app_type),
        )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture()
def client(seeded_db):
    import backend.api.routes as routes_mod
    routes_mod.DB_PATH = seeded_db
    import backend.main as main_mod
    main_mod.DB_PATH = seeded_db
    from backend.main import app
    return TestClient(app)


class TestHealth:
    def test_health_returns_ok(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "graph_loaded" in data
        assert "db_path" in data


class TestListApplications:
    def test_returns_paginated_results(self, client):
        r = client.get("/api/applications")
        assert r.status_code == 200
        data = r.json()
        assert "results" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data

    def test_total_reflects_seeded_records(self, client):
        r = client.get("/api/applications")
        assert r.json()["total"] == 2

    def test_filter_by_application_type(self, client):
        r = client.get("/api/applications?application_type=COTS")
        data = r.json()
        assert data["total"] == 1
        assert data["results"][0]["application_type"] == "COTS"

    def test_filter_by_q(self, client):
        r = client.get("/api/applications?q=Alpha")
        data = r.json()
        assert data["total"] == 1
        assert "Alpha" in data["results"][0]["application_name"]

    def test_page_size_enforced(self, client):
        r = client.get("/api/applications?page_size=1")
        data = r.json()
        assert len(data["results"]) == 1
        assert data["pages"] == 2

    def test_invalid_page_size_rejected(self, client):
        r = client.get("/api/applications?page_size=300")
        assert r.status_code == 422


class TestGetApplication:
    def test_returns_full_record(self, client, seeded_db):
        from backend.db.connection import get_connection
        conn = get_connection(seeded_db)
        app_id = conn.execute(
            "SELECT application_id FROM applications WHERE application_name = ?", ("App Alpha",)
        ).fetchone()["application_id"]
        conn.close()

        r = client.get(f"/api/applications/{app_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["application_id"] == app_id
        assert data["application_name"] == "App Alpha"

    def test_unknown_id_returns_404(self, client):
        r = client.get("/api/applications/does-not-exist")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()


class TestRefreshStatus:
    def test_never_run_when_empty(self, client):
        r = client.get("/api/refresh/status")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "never_run"
        assert data["run_id"] is None
