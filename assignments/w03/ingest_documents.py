"""Initialize pgvector and ingest all documents from the Week 3 manifest.

Usage: python assignments/w03/ingest_documents.py
"""
from __future__ import annotations

from pathlib import Path
import sys

# Locate the repository root so the script works from any current directory.
ROOT = Path(__file__).resolve().parents[2]
# Make project packages, including ``app``, importable when run as a script.
sys.path.insert(0, str(ROOT))

from app.services.vector_store import initialize_database, ingest_manifest


# Point to the 15 synthetic documents described by the manifest.
MANIFEST = ROOT / "data/documents/manifest.json"


def main() -> None:
    # Create the pgvector extension, table, and indexes before writing chunks.
    initialize_database()
    # Chunk and upsert every manifest document, then report the write count.
    indexed = ingest_manifest(MANIFEST)
    print(f"Indexed chunks: {indexed}")


if __name__ == "__main__":
    main()
