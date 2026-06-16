import os
import tempfile

import pandas as pd
import pytest

from backend.etl.ingest import REQUIRED_COLUMNS, SchemaValidationError, validate_schema


def _make_df(extra_cols: list[str] | None = None, missing_cols: list[str] | None = None) -> pd.DataFrame:
    cols = list(REQUIRED_COLUMNS)
    if extra_cols:
        cols += extra_cols
    if missing_cols:
        cols = [c for c in cols if c not in missing_cols]
    return pd.DataFrame(columns=cols)


class TestValidateSchema:
    def test_valid_schema_passes(self):
        df = _make_df()
        validate_schema(df)  # must not raise

    def test_extra_columns_allowed(self):
        df = _make_df(extra_cols=["Extra Column"])
        validate_schema(df)  # must not raise

    def test_missing_one_column_raises(self):
        df = _make_df(missing_cols=["Application Name"])
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema(df)
        assert "Application Name" in exc_info.value.missing

    def test_missing_multiple_columns_raises(self):
        df = _make_df(missing_cols=["Application Name", "Company", "Business Owner"])
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema(df)
        assert len(exc_info.value.missing) == 3

    def test_error_message_lists_missing_columns(self):
        df = _make_df(missing_cols=["Application Name"])
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_schema(df)
        assert "Application Name" in str(exc_info.value)


class TestRunETLIntegration:
    """Integration tests that require a temp XLSX and a temp SQLite DB."""

    def _write_xlsx(self, rows: list[dict]) -> str:
        df = pd.DataFrame(rows)
        fd, path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd)
        df.to_excel(path, index=False, engine="openpyxl")
        return path

    def _make_valid_row(self, name: str = "Test App", company: str = "Baptist Hospital") -> dict:
        return {col: "" for col in REQUIRED_COLUMNS} | {
            "Application Name": name,
            "Company": company,
            "Application Type": "COTS",
            "Baptist Managed": "Yes",
            "Business Process": "Imaging",
            "Description": "Test description",
            "Architecture Type": "Web Based",
        }

    def test_etl_loads_records(self):
        from backend.db.connection import init_db
        from backend.etl.ingest import run_etl

        xlsx_path = self._write_xlsx([self._make_valid_row("App A"), self._make_valid_row("App B")])
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        os.unlink(db_path)

        try:
            init_db(db_path)
            result = run_etl(xlsx_path, db_path=db_path)
            assert result["records_loaded"] == 2
            assert result["status"] in ("success", "partial")
        finally:
            os.unlink(xlsx_path)
            try:
                os.unlink(db_path)
            except FileNotFoundError:
                pass

    def test_etl_uuid_stability(self):
        from backend.db.connection import get_connection, init_db
        from backend.etl.ingest import run_etl

        row = self._make_valid_row("Stable App", "BHMG")
        xlsx_path = self._write_xlsx([row])
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        os.unlink(db_path)

        try:
            init_db(db_path)
            run_etl(xlsx_path, db_path=db_path)

            conn = get_connection(db_path)
            uid_first = conn.execute(
                "SELECT application_id FROM applications WHERE application_name = ?", ("Stable App",)
            ).fetchone()["application_id"]
            conn.close()

            # Re-ingest same file
            run_etl(xlsx_path, db_path=db_path)

            conn = get_connection(db_path)
            uid_second = conn.execute(
                "SELECT application_id FROM applications WHERE application_name = ?", ("Stable App",)
            ).fetchone()["application_id"]
            conn.close()

            assert uid_first == uid_second
        finally:
            os.unlink(xlsx_path)
            try:
                os.unlink(db_path)
            except FileNotFoundError:
                pass

    def test_malformed_xlsx_rejected(self):
        from backend.db.connection import init_db
        from backend.etl.ingest import SchemaValidationError, run_etl

        bad_df = pd.DataFrame({"WrongColumn": ["a"]})
        fd, bad_path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd)
        bad_df.to_excel(bad_path, index=False, engine="openpyxl")

        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        os.unlink(db_path)

        try:
            init_db(db_path)
            with pytest.raises(SchemaValidationError):
                run_etl(bad_path, db_path=db_path)
        finally:
            os.unlink(bad_path)
            try:
                os.unlink(db_path)
            except FileNotFoundError:
                pass

    def test_soft_delete_on_re_ingest(self):
        from backend.db.connection import get_connection, init_db
        from backend.etl.ingest import run_etl

        row_a = self._make_valid_row("App Alpha")
        row_b = self._make_valid_row("App Beta")

        xlsx_both = self._write_xlsx([row_a, row_b])
        xlsx_only_a = self._write_xlsx([row_a])

        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        os.unlink(db_path)

        try:
            init_db(db_path)
            run_etl(xlsx_both, db_path=db_path)
            run_etl(xlsx_only_a, db_path=db_path)

            conn = get_connection(db_path)
            beta = conn.execute(
                "SELECT active_status FROM applications WHERE application_name = ?", ("App Beta",)
            ).fetchone()
            conn.close()

            assert beta["active_status"] == 0  # soft-deleted
        finally:
            for p in [xlsx_both, xlsx_only_a]:
                try:
                    os.unlink(p)
                except FileNotFoundError:
                    pass
            try:
                os.unlink(db_path)
            except FileNotFoundError:
                pass
