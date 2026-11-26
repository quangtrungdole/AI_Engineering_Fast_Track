# Weekly Submission – W03 / Member dlqtrung

**Feature (F01–F04 or Foundation):** Foundation for F01 — project-scoped document retrieval with pgvector

**What I studied (2–3 concepts):**

1. **Embeddings and vector databases:** The DeepLearning.AI vector databases course explains how text is represented as embeddings and searched by vector similarity. I applied this by producing a deterministic local embedding for each chunk and storing it in pgvector's `vector(384)` column. [Vector Databases: from Embeddings to Applications](https://www.deeplearning.ai/courses/vector-databases-embeddings-applications)
2. **Chunking, metadata, and retrieval:** Retrieval depends on splitting source text into retrievable units while preserving document and source metadata. Chunk size is the maximum amount of text represented by one embedding and returned as one result; I selected a 600-token target so a chunk has useful context without combining too many unrelated facts. The 100-token overlap repeats boundary text in the next chunk, reducing the chance that an important sentence is separated from its context. Each chunk stores its document ID, project ID, source path, index, and token offsets. [OpenAI Retrieval guide](https://developers.openai.com/api/docs/guides/retrieval)
3. **Top-k retrieval and Recall@5:** Top-k is the number of highest-similarity chunks returned for one query. I implemented project-scoped retrieval with the default `top_k=5`: a larger value can improve the chance of finding relevant evidence but returns more context for a later answer-generation step. Recall@5 measures whether at least one expected document appears among those five results; I evaluated this across all 20 labeled queries. [OpenAI Retrieval guide](https://developers.openai.com/api/docs/guides/retrieval)

**What I built (summary + key modules):**

- [`app/services/vector_store.py`](../app/services/vector_store.py)
  - Creates the pgvector extension, `document_chunks` table, and HNSW/indexes through `initialize_database()`.
  - Loads manifest entries, chunks UTF-8 text, creates deterministic local embeddings, and upserts records using `(doc_id, chunk_index)`.
  - Searches with the `project_id` predicate in SQL before vector ordering and `LIMIT`, so chunks outside the requested project are not candidates.
  - Provides schema initialization, upsert, search, and document deletion operations.
- [`assignments/w03/ingest_documents.py`](../assignments/w03/ingest_documents.py) initializes the database and ingests all 15 manifest documents without running evaluation.
- [`assignments/w03/evaluate_retrieval.py`](../assignments/w03/evaluate_retrieval.py) calculates Recall@5 for the 20 cases in `data/evaluation/retrieval_gold.json`.
- [`app/retrieval_api.py`](../app/retrieval_api.py) defines `POST /search`, and [`app/main.py`](../app/main.py) mounts the router alongside meeting analysis. The mock Jira routes remain in [`app/mock_jira.py`](../app/mock_jira.py).
- [`tests/test_vector_store.py`](../tests/test_vector_store.py) covers chunking, embedding stability, manifest loading, initialization, upsert/delete, and authorization-aware SQL ordering.

**How to run:**

From the repository root, reset the local training database if a clean start is needed. This removes the local Docker volume:

```bash
docker compose down -v
docker compose up -d db
```

Initialize and ingest the 15 documents, then compute Recall@5:

```bash
python assignments/w03/ingest_documents.py
python assignments/w03/evaluate_retrieval.py
```

Run the main API, which includes the retrieval endpoint, on port 8000:

```bash
uvicorn app.main:app --reload --port 8000
```

Example project-scoped retrieval request:

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H 'Content-Type: application/json' \
  -H 'X-Allowed-Project: ALPHA' \
  -d '{"query":"What is the Alpha UAT sign-off date?", "project_id":"ALPHA"}'
```

**Results:**

| Check | Result |
|---|---:|
| Fixture documents ingested | 15/15 |
| Labeled retrieval queries | 20 |
| Recall@5 | 20/20 (100.0%) |
| Vector-store unit tests | 8 passed |
| Cross-project chunks returned | 0 |

**Known failures / trade-offs:**

- The synthetic fixture documents are shorter than the 600-token chunk target, so each currently becomes one chunk. Longer source documents will exercise overlap and multi-chunk retrieval more fully.
- Local hashing embeddings keep the exercise independent of external APIs, but they are less semantically capable than a governed production embedding model.
- The 20 labeled evaluation cases are synthetic and project-filtered; broader and hidden cases may reveal retrieval gaps not represented by these fixtures.

**Demo link:**
None — local FastAPI and Docker demonstration.

**PR link:**
N/A

**Next action:**
Use the chunking, pgvector retrieval, project-scoped filtering, and Recall@5 evaluation practices learned in Week 3 as the foundation to prepare for and implement the Week 4 assignment.
