# W03 — Project-scoped pgvector retrieval

This implementation indexes the 15 synthetic files in `data/documents/` and
retrieves document chunks only from the requested project. It does not generate
an answer; it returns evidence chunks for a later RAG step.

## 1. Reset and set up the vector database

The following reset removes the existing local PostgreSQL Docker volume. Use it
only for this training database; any data stored in it will be deleted.

```bash
docker compose down -v
docker compose up -d db
```

Run the ingestion-only script. It calls `initialize_database()` to create the
`vector` extension, `document_chunks` table, and indexes, then upserts all 15
documents from `data/documents/manifest.json`.

```bash
python assignments/w03/ingest_documents.py
```

## 2. Compute Recall@5 on the 20 labeled queries

`data/evaluation/retrieval_gold.json` contains 20 labeled retrieval queries.
Run the evaluator with its default `top_k=5` after completing the ingestion
step above:

```bash
python assignments/w03/evaluate_retrieval.py
```

It prints one `HIT` or `MISS` per query and a final `Recall@5` score. Pass a
different value from 1–50 only when evaluating another cutoff:

```bash
python assignments/w03/evaluate_retrieval.py 10
```

## 3. Run the search API

Start the API in a separate terminal after the vector database is set up:

```bash
uvicorn app.mock_jira:app --reload --port 8001
```

This single server exposes both the existing mock Jira routes and the Week 3
`/search` route on port `8001`.

Query it with an authorization header that matches the requested project:

```bash
curl -X POST http://127.0.0.1:8001/search \
  -H 'Content-Type: application/json' -H 'X-Allowed-Project: ALPHA' \
  -d '{"query":"What is the Alpha UAT date?", "project_id":"ALPHA"}'
```

## Database schema

### `document_chunks`

```sql
CREATE TABLE document_chunks (
  id          BIGSERIAL PRIMARY KEY,
  doc_id      TEXT NOT NULL,
  project_id  TEXT NOT NULL,
  source_path TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  start_token INTEGER NOT NULL,
  end_token   INTEGER NOT NULL,
  content     TEXT NOT NULL,
  embedding   vector(384) NOT NULL,
  UNIQUE (doc_id, chunk_index)
);
```

`project_id` identifies the retrieval scope. `doc_id` and `chunk_index` make a
chunk unique; `source_path`, `start_token`, and `end_token` identify its origin.
`content` is the returned text, and `embedding` stores its 384-dimension vector.

One row represents one retrievable chunk rather than an entire document. This
allows vector search to return the specific passage that best matches a query.
The `project_id` is stored with every chunk so PostgreSQL can filter access
before similarity ranking. Source and token-offset fields make each result
traceable to its original document, while `UNIQUE (doc_id, chunk_index)` makes
ingestion idempotent: re-ingesting the same chunk updates it instead of adding
a duplicate.

### Indexes

```sql
CREATE INDEX document_chunks_project_idx
  ON document_chunks (project_id);

CREATE INDEX document_chunks_embedding_idx
  ON document_chunks USING hnsw (embedding vector_cosine_ops);
```

- **document_chunks_project_idx**: speeds up the `WHERE project_id = ...` filter
that enforces project-scoped retrieval. 
- **document_chunks_embedding_idx**: is an
HNSW approximate-nearest-neighbor index: it speeds up finding the closest
embeddings without comparing every chunk. `vector_cosine_ops` configures that
index for cosine distance, which is well suited to semantic search.

## Project-scoped retrieval

The retrieval SQL applies `WHERE project_id = %s` before vector ordering and
`LIMIT`. Thus pgvector scores only permitted-project chunks, rather than
retrieving every project and filtering afterward. `top_k` defaults to 5 and is
an API input (1–50). Returned records include source and token-offset metadata.

