from pathlib import Path
from unittest.mock import patch

import pytest

from app.services import vector_store


class Cursor:
    def __init__(self, rows=None):
        self.calls = []
        self.rows = rows or []
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchall(self):
        return self.rows


class Connection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commits += 1


def test_chunk_text_uses_overlap_and_preserves_offsets():
    text = " ".join(f"token{i}" for i in range(900))
    chunks = vector_store.chunk_text(text, chunk_size=500, overlap=100)
    assert [(start, end) for start, end, _ in chunks] == [(0, 500), (400, 900)]


def test_chunk_text_rejects_size_outside_requirement():
    with pytest.raises(ValueError, match="500 and 800"):
        vector_store.chunk_text("text", chunk_size=499)


def test_embedding_is_deterministic_and_normalized():
    first = vector_store.embed_text("UAT sign-off date")
    assert first == vector_store.embed_text("UAT sign-off date")
    assert len(first) == vector_store.EMBEDDING_DIMENSIONS
    assert sum(value * value for value in first) == pytest.approx(1.0)


def test_manifest_loads_all_15_fixture_documents():
    manifest = Path(__file__).resolve().parents[1] / "data/documents/manifest.json"
    chunks = vector_store.chunks_from_manifest(manifest)
    assert len(chunks) == 15
    assert {chunk.project_id for chunk in chunks} == {"ALPHA", "BETA", "GAMMA"}


def test_search_filters_project_in_sql_before_vector_ordering():
    cursor = Cursor([("Alpha text", "REQ-01", "ALPHA", "data/a.md", 0, 0, 8, 0.12)])
    with patch.object(vector_store, "_connect", return_value=Connection(cursor)):
        results = vector_store.search("alpha UAT", "alpha")
    assert results[0].project_id == "ALPHA"
    sql, params = cursor.calls[0]
    assert "WHERE project_id = %s" in sql
    assert sql.index("WHERE project_id = %s") < sql.index("ORDER BY")
    assert params[1] == "ALPHA"
    assert params[-1] == 5


def test_upsert_writes_vector_and_metadata():
    cursor = Cursor()
    connection = Connection(cursor)
    chunk = vector_store.Chunk("REQ-01", "ALPHA", "data/a.md", 0, 0, 3, "alpha text")
    with patch.object(vector_store, "_connect", return_value=connection):
        assert vector_store.upsert_chunks([chunk]) == 1
    inserts = [call for call in cursor.calls if "INSERT INTO document_chunks" in call[0]]
    assert len(inserts) == 1
    assert inserts[0][1][:3] == ("REQ-01", "ALPHA", "data/a.md")


def test_initialize_database_creates_schema_once_before_ingestion():
    cursor = Cursor()
    connection = Connection(cursor)
    with patch.object(vector_store, "_connect", return_value=connection):
        vector_store.initialize_database()
    statements = [sql for sql, _ in cursor.calls]
    assert any("CREATE TABLE IF NOT EXISTS document_chunks" in sql for sql in statements)
    assert not any("INSERT INTO document_chunks" in sql for sql in statements)


def test_delete_document_removes_only_its_chunks():
    cursor = Cursor()
    cursor.rowcount = 2
    with patch.object(vector_store, "_connect", return_value=Connection(cursor)):
        assert vector_store.delete_document("REQ-01") == 2
    assert cursor.calls == [("DELETE FROM document_chunks WHERE doc_id = %s", ("REQ-01",))]
