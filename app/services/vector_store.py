"""Local embedding, ingestion, and project-scoped pgvector retrieval.

This module deliberately uses a deterministic, local hashing embedding rather
than a hosted embedding API.  It keeps the Week 3 exercise runnable without
credentials while pgvector remains responsible for persistence and similarity
search.  Swap ``embed_text`` for an approved embedding model in production.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
from typing import Any, Iterable

from dotenv import load_dotenv
import psycopg


# Load the repository's local configuration when this service runs standalone.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

EMBEDDING_DIMENSIONS = 384
DEFAULT_DATABASE_URL = "postgresql://training:training@localhost:5432/aibootcamp"
DEFAULT_CHUNK_SIZE = 600
DEFAULT_CHUNK_OVERLAP = 100
MAX_TOP_K = 50
_TOKEN_RE = re.compile(r"[A-Za-z0-9_-]+")


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    project_id: str
    source_path: str
    chunk_index: int
    start_token: int
    end_token: int
    text: str


@dataclass(frozen=True)
class SearchResult:
    text: str
    doc_id: str
    project_id: str
    source_path: str
    chunk_index: int
    start_token: int
    end_token: int
    distance: float


def database_url() -> str:
    """Return the local training DB URL, allowing a ``DATABASE_URL`` override."""
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def chunk_text(
    text: str, *, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP
) -> list[tuple[int, int, str]]:
    """Split text into overlapping, approximately token-sized chunks.

    Fixture documents shorter than ``chunk_size`` produce one chunk.  Token
    offsets are retained as source locations for each returned result.
    """
    if not 500 <= chunk_size <= 800:
        raise ValueError("chunk_size must be between 500 and 800 tokens")
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")
    words = text.split()
    if not words:
        return []
    chunks: list[tuple[int, int, str]] = []
    step = chunk_size - overlap
    for start in range(0, len(words), step):
        end = min(start + chunk_size, len(words))
        chunks.append((start, end, " ".join(words[start:end])))
        if end == len(words):
            break
    return chunks


def embed_text(text: str, *, dimensions: int = EMBEDDING_DIMENSIONS) -> list[float]:
    """Create a stable normalized hashing embedding without a network call."""
    if dimensions <= 0:
        raise ValueError("dimensions must be positive")
    vector = [0.0] * dimensions
    tokens = _tokens(text)
    # Bigrams preserve a small amount of phrase information (e.g. "uat sign").
    features = tokens + [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]
    for feature in features:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "big")
        index = value % dimensions
        vector[index] += 1.0 if value & 1 else -1.0
    norm = math.sqrt(sum(value * value for value in vector))
    return vector if norm == 0 else [value / norm for value in vector]


def _vector_literal(values: Iterable[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def _connect(dsn: str | None = None) -> psycopg.Connection[Any]:
    return psycopg.connect(dsn or database_url())


def create_schema(conn: Any) -> None:
    """Create the pgvector extension and chunk table if they do not exist."""
    with conn.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id BIGSERIAL PRIMARY KEY,
                doc_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                source_path TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                start_token INTEGER NOT NULL,
                end_token INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding vector({EMBEDDING_DIMENSIONS}) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                UNIQUE (doc_id, chunk_index)
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS document_chunks_project_idx "
            "ON document_chunks (project_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx "
            "ON document_chunks USING hnsw (embedding vector_cosine_ops)"
        )
    conn.commit()


def initialize_database(*, dsn: str | None = None) -> None:
    """Create the vector schema during database setup, before ingestion begins."""
    with _connect(dsn) as conn:
        create_schema(conn)


def chunks_from_manifest(manifest_path: str | Path) -> list[Chunk]:
    """Load every manifest document and attach its project/source metadata."""
    manifest = Path(manifest_path)
    root = manifest.resolve().parents[2]
    records = json.loads(manifest.read_text(encoding="utf-8"))
    chunks: list[Chunk] = []
    for record in records:
        source_path = str(record["path"])
        text = (root / source_path).read_text(encoding="utf-8")
        for index, (start, end, content) in enumerate(chunk_text(text)):
            chunks.append(
                Chunk(
                    doc_id=record["doc_id"], project_id=record["project_id"],
                    source_path=source_path, chunk_index=index, start_token=start,
                    end_token=end, text=content,
                )
            )
    return chunks


def upsert_chunks(chunks: Iterable[Chunk], *, dsn: str | None = None) -> int:
    """Insert/update chunks in an initialized vector database.

    Call :func:`initialize_database` once when setting up a new database.
    """
    materialized = list(chunks)
    with _connect(dsn) as conn:
        with conn.cursor() as cursor:
            for chunk in materialized:
                cursor.execute(
                    """
                    INSERT INTO document_chunks
                    (doc_id, project_id, source_path, chunk_index, start_token, end_token, content, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)
                    ON CONFLICT (doc_id, chunk_index) DO UPDATE SET
                        project_id = EXCLUDED.project_id, source_path = EXCLUDED.source_path,
                        start_token = EXCLUDED.start_token, end_token = EXCLUDED.end_token,
                        content = EXCLUDED.content, embedding = EXCLUDED.embedding
                    """,
                    (chunk.doc_id, chunk.project_id, chunk.source_path, chunk.chunk_index,
                     chunk.start_token, chunk.end_token, chunk.text,
                     _vector_literal(embed_text(chunk.text))),
                )
        conn.commit()
    return len(materialized)


def ingest_manifest(manifest_path: str | Path, *, dsn: str | None = None) -> int:
    """Read manifest files, chunk them, and upsert the resulting records."""
    return upsert_chunks(chunks_from_manifest(manifest_path), dsn=dsn)


def delete_document(doc_id: str, *, dsn: str | None = None) -> int:
    """Delete all indexed chunks for one document and return the count removed."""
    if not doc_id.strip():
        raise ValueError("doc_id must not be empty")
    with _connect(dsn) as conn, conn.cursor() as cursor:
        cursor.execute("DELETE FROM document_chunks WHERE doc_id = %s", (doc_id,))
        deleted = cursor.rowcount
        conn.commit()
    return deleted


def search(
    query: str, project_id: str, *, top_k: int = 5, dsn: str | None = None
) -> list[SearchResult]:
    """Return nearest chunks, filtering by project inside the SQL query.

    The ``WHERE project_id = %s`` predicate is intentionally applied before
    pgvector ordering and ``LIMIT``.  No unauthorized vectors are candidates.
    """
    if not query.strip():
        raise ValueError("query must not be empty")
    if not project_id.strip():
        raise ValueError("project_id must not be empty")
    if not 1 <= top_k <= MAX_TOP_K:
        raise ValueError(f"top_k must be between 1 and {MAX_TOP_K}")
    query_vector = _vector_literal(embed_text(query))
    with _connect(dsn) as conn, conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT content, doc_id, project_id, source_path, chunk_index,
                   start_token, end_token, embedding <=> %s::vector AS distance
            FROM document_chunks
            WHERE project_id = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (query_vector, project_id.upper(), query_vector, top_k),
        )
        return [SearchResult(*row) for row in cursor.fetchall()]
