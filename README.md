# Document Intelligence Platform

A FastAPI service that ingests invoices, purchase orders and contracts, extracts structured
fields, answers grounded natural-language questions over them, detects drift, and surfaces
analyst-style insights (risk, financial trends, cross-document comparisons). A React console
(`frontend-react/`) sits on top of the API.

- [What it does](#1-what-it-does)
- [Architecture](#2-architecture)
- [API reference](#3-api-reference)
- [Quick start (Docker)](#4-quick-start-docker)
- [Local development (hot reload)](#5-local-development-hot-reload)
- [Using the console](#6-using-the-console)
- [Configuration](#7-configuration)
- [Testing and quality](#8-testing-and-quality)
- [Operations](#9-operations)
- [Troubleshooting](#10-troubleshooting)
- [Known limitations](#11-known-limitations)
- [Before production](#12-before-production)
- [Repository layout](#13-repository-layout)

---

## 1. What it does

| Area | What it does | Key modules |
|---|---|---|
| **Ingestion** | Upload PDF/DOCX (max 10 MB) with extension and content verification, size limits and duplicate detection by content hash | `app/documents/` |
| **Parsing** | Extracts raw text and pages from PDF and DOCX | `app/parsing/` |
| **Classification** | Rule-based document-type detection (invoice, purchase order, contract) | `app/classification/` |
| **Extraction** | Structured field extraction per document type, saved to Postgres | `app/extraction/` |
| **Indexing** | Chunks documents, embeds them, upserts to Qdrant | `app/indexing/` |
| **Retrieval** | Semantic search over indexed chunks with document and type filters | `app/retrieval/` |
| **Routing** | Sends a question to the saved extraction (structured) or to vector search (semantic) | `app/routing/` |
| **QA** | Grounded LLM answers, deterministic evidence verification, prompt-injection guard | `app/qa/` |
| **Analyst** | Per-document and cross-document insights: risk, anomalies, financial trend, completeness, prioritisation | `app/analyst/` |
| **Drift** | Statistical drift detection (PSI) on extraction quality and retrieval metrics against a baseline | `app/drift/` |
| **Storage** | PostgreSQL persistence (documents, extractions, insights, drift) via SQLAlchemy and Alembic | `app/storage/`, `alembic/` |
| **Observability** | Structured JSON logs, Prometheus metrics, request tracing, health checks | `app/observability/` |
| **Security** | Bearer-token auth, separate metrics key, rate limiting, request body limits, secrets validation, audit logging, SSRF guard | `app/security/` |
| **Evaluation** | Extraction, retrieval and grounding benchmarks with regression tracking and quality thresholds | `evaluation/` |
| **Console** | React + Vite UI: Connection, Documents, Document detail, Ask, Insights, Drift, Health | `frontend-react/` |

### How a question is answered

1. The router classifies the question. Questions about fields (total, amount, date, vendor, status)
   are **structured**; summaries, clauses and terms are **semantic**; "compare / across" questions
   are **cross-document** (use the Analyst endpoints for those).
2. **Structured** questions with a processed document ID are answered from that document's saved
   extraction. If there is no document ID or no extraction yet, the question falls back to semantic
   search over the indexed text.
3. **Semantic** questions retrieve the top-K chunks from Qdrant.
4. The LLM (Groq) writes an answer using only that evidence.
5. For semantic answers, a deterministic verifier checks each claim against the evidence and reports
   `verified` plus any `unsupported_claims`. The verifier is strict, so long paraphrased summaries
   often come back unverified.

## 2. Architecture

```
Browser ──► nginx :3000 ──/api/──► FastAPI :8000 ──► PostgreSQL   (documents, extractions, insights, drift)
 (React)                              │           ├─► Qdrant       (chunk embeddings)
                                      │           ├─► Redis        (shared rate limiting)
                                      │           └─► Groq API     (answer generation)
Prometheus ──► /metrics (own bearer key)
```

Docker Compose runs `api`, `frontend`, `postgres`, `qdrant` and `redis`.
`docker-compose.prod.yml` adds resource limits, log rotation and Prometheus.

## 3. API reference

Interactive docs are served at `http://localhost:8000/docs`. Everything except health checks
needs `Authorization: Bearer <API_AUTH_KEY>`; `/metrics` needs `Bearer <METRICS_AUTH_KEY>`.

| Method and path | Purpose |
|---|---|
| `POST /documents/` | Upload a document (multipart, PDF/DOCX, max 10 MB) |
| `GET /documents/` | List documents (`status`, `document_type`, `limit`, `offset`) |
| `GET /documents/{id}` | Document metadata and status |
| `DELETE /documents/{id}` | Delete a document and its stored file |
| `POST /documents/{id}/process` | Parse, classify, extract, and index the document |
| `POST /qa/answer` | Ask a grounded question, optionally scoped by `document_id` and `document_type` |
| `POST /analyst/documents/{id}/analyze` | Generate insights for a document |
| `GET /analyst/documents/{id}/insights` | Stored insights for a document |
| `POST /analyst/compare` | Cross-document comparison insights |
| `POST /analyst/trend` | Trend insights across a document type |
| `GET /analyst/insights` | List insights |
| `POST /drift/baseline` | Establish a drift baseline for a document type |
| `POST /drift/check` | Run a drift check |
| `GET /drift/results` | Drift results |
| `GET /drift/alerts` | Drift alerts |
| `POST /drift/alerts/{id}/acknowledge` | Acknowledge an alert |
| `GET /drift/dashboard` | Drift summary |
| `GET /health/live` | Liveness probe (open) |
| `GET /health/ready` | Readiness probe: checks Postgres and Qdrant (open) |
| `GET /metrics`, `GET /metrics/summary` | Prometheus metrics (separate metrics key) |

Rate limits are per API key (per IP if no key): 120 requests/minute by default and 20/minute
for the expensive routes (QA and analyst).

## 4. Quick start (Docker)

Requirements: Docker with Compose, and a [Groq](https://console.groq.com) API key.

```bash
git clone <repo-url>
cd document-intelligence

# Creates .env with freshly generated secrets; prompts for your Groq key.
python scripts/make_demo_env.py

docker compose up -d --build --wait
docker compose exec api alembic upgrade head
docker compose exec api python scripts/init_qdrant_collection.py

# Optional: load sample documents through the public API
docker compose exec api python scripts/demo_seed.py

curl http://localhost:8000/health/ready
```

Open **http://localhost:3000**. On the Connection page set:

- **API base URL:** `/api` (nginx proxies it to `api:8000`)
- **API key:** the `API_AUTH_KEY` value from your `.env`

If you would rather write `.env` by hand, see [Configuration](#7-configuration) for the required
variables.

## 5. Local development (hot reload)

Run the backend and frontend directly on your machine and keep only the data services in Docker.

**1. Publish the data-service ports.** Create `docker-compose.override.yml` (Compose loads it
automatically) so the host can reach them:

```yaml
services:
  postgres:
    ports: ["127.0.0.1:5432:5432"]
  qdrant:
    ports: ["127.0.0.1:6333:6333"]
  redis:
    ports: ["127.0.0.1:6379:6379"]
```

```bash
docker compose up -d postgres qdrant redis   # not `api`: it would occupy port 8000
```

**2. Point `.env` at localhost:**

```
DATABASE_URL=postgresql+psycopg2://<user>:<password>@localhost:5432/<db>
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379/0
```

**3. Backend** (Python 3.11 or newer):

```bash
pip install -e ".[dev]"
alembic upgrade head
python scripts/init_qdrant_collection.py
uvicorn app.main:app --reload --port 8000
```

**4. Frontend** in a second terminal:

```bash
cd frontend-react
npm install
npm run dev          # http://localhost:5173
```

On the Connection page use API base `http://localhost:8000`. The default CORS list already
allows `http://localhost:5173`; change it with `CORS_ALLOWED_ORIGINS`.

## 6. Using the console

1. **Documents:** upload a file, open it, and click **Process**. A document only has extracted
   fields and searchable chunks after processing (status `ready`).
2. **Ask:** enter a question, optionally a document ID and type. Answers are rendered as Markdown,
   with grounded/verified badges, the verifier's reason, any unsupported claims, and the source
   chunks.
3. **Insights:** generate and browse analyst insights per document, compare documents, view trends.
4. **Drift:** establish baselines, run checks, review and acknowledge alerts.
5. **Health:** readiness of the API and its dependencies.

## 7. Configuration

Set these in `.env` (never commit it). Postgres, Qdrant and Redis are self-hosted through Compose;
the only external service is the LLM provider (Groq).

### Required

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://<user>:<password>@<host>:5432/<db>`. Use `localhost` when running the API directly; Compose overrides it with the `postgres` service name for the api container. |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Credentials for the Compose Postgres. The password must not be a placeholder. |
| `API_AUTH_KEY` | Bearer token clients send. At least 32 characters. Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `QDRANT_URL` | `http://localhost:6333` locally; Compose uses `http://qdrant:6333`. |
| `QDRANT_API_KEY` | Qdrant auth key. You choose it; Compose passes it to Qdrant and refuses to start without it. Required whenever `QDRANT_URL` is not localhost. |
| `LLM_URL` | `https://api.groq.com/openai/v1` |
| `LLM_API_KEY` | Groq API key. Required in staging and production. |

### Optional

| Variable | Purpose | Default |
|---|---|---|
| `METRICS_AUTH_KEY` | Bearer token for `/metrics`. Without it the endpoint returns 503. | unset |
| `CORS_ALLOWED_ORIGINS` | Comma-separated browser origins | `http://localhost:5173,http://127.0.0.1:5173` |
| `REDIS_URL` | Shared rate-limit store. Needed with more than one worker or replica. | in-process limiter |
| `APP_ENV` | `development`, `staging` or `production` (production tightens validation) | `development` |
| `LLM_MODEL` | Groq model | `openai/gpt-oss-120b` |
| `LLM_ENDPOINT` | Path appended to `LLM_URL` | `/chat/completions` |
| `LLM_TIMEOUT` | LLM request timeout (seconds) | `30.0` |
| `LLM_ALLOWED_HOSTS` | Hosts `LLM_URL` may use in staging and production | `api.groq.com` |
| `QDRANT_COLLECTION` | Collection name | `document_chunks` |
| `QDRANT_DISTANCE` | Similarity metric | `Cosine` |
| `QDRANT_TIMEOUT` | Qdrant client timeout (seconds) | `30` |
| `EMBEDDING_DIM` | Embedding size (matches `all-MiniLM-L6-v2`) | `384` |
| `DATABASE_SSLMODE` | `require`, `verify-ca` or `verify-full`. Required once the database host is not local. | unset |
| `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW` | SQLAlchemy pool sizing | `5`, `10` |
| `DATABASE_STATEMENT_TIMEOUT_MS` | Postgres query timeout | `30000` |
| `DATABASE_ECHO` | Log every SQL statement. Must stay `false` in production. | `false` |
| `INTERNAL_SERVICE_HOSTS` | Private hostnames (for example `postgres,qdrant,redis`) exempt from the TLS requirement. Set by Compose. | empty |
| `DRIFT_THRESHOLD_MODERATE`, `DRIFT_THRESHOLD_SIGNIFICANT` | PSI thresholds for drift alerts | `0.1`, `0.2` |
| `TEST_DATABASE_URL` | Postgres for integration tests only | unset |

Script-only variables: `SMOKE_TEST_URL` (smoke test), `API_BASE` (demo seed), `GROQ_API_KEY`
(`make_demo_env.py`).

## 8. Testing and quality

```bash
pip install -e ".[dev]"
pytest -m "not integration"          # fast unit suite
pytest -m integration                # needs TEST_DATABASE_URL and a running Qdrant
ruff check app tests && mypy app     # lint and type check
pip-audit && bandit -r app -ll       # dependency and static security scans
```

Frontend: `cd frontend-react && npm run build`.

## 9. Operations

| Task | Command |
|---|---|
| Post-deploy smoke test (also verifies auth is enforced) | `SMOKE_TEST_URL=... API_AUTH_KEY=... python scripts/smoke_test.py` |
| Establish or refresh a drift baseline | `python scripts/establish_baseline.py <invoice\|purchase_order\|contract>` |
| Offline retrieval evaluation (hit rate, MRR gauges) | `python scripts/run_retrieval_eval.py` |
| Back up Postgres or Qdrant | `scripts/backup_postgres.sh`, `scripts/backup_qdrant.sh` |
| Roll back a deployment | `scripts/rollback.sh` |
| Render a runtime `.env` from a secrets backend | `scripts/render_env.py` |

**Production compose:** `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`.
It adds Prometheus, which scrapes `api:8000/metrics` using the token in `./secrets/metrics_auth_key`.
That file's contents must equal `METRICS_AUTH_KEY`.

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Answer is "I don't have sufficient evidence in the provided document" | The document was never processed, or nothing was indexed | Click **Process** (or `POST /documents/{id}/process`); the response should show `chunks_indexed` above 0 |
| `POST /qa/answer` returns 400 "could not be classified" | Question matched no route and no document ID was given | Add a document ID or make the question more specific |
| `POST /qa/answer` returns 400 "Unsupported query type: cross_document" | Question contains "compare" or "across" | Use `POST /analyst/compare` |
| `POST /qa/answer` returns 503 | LLM or Qdrant unavailable, or the collection does not exist yet | Check `/health/ready`; process at least one document so the collection is created |
| 500 "Database operation failed"; logs show "connection refused" on `localhost:5432` | API running on the host but Postgres port not published | Follow [Local development](#5-local-development-hot-reload) step 1, or run the API in Docker |
| `Address already in use` on port 8000 | The Docker `api` container is running | `docker compose stop api`, or find the owner with `ss -ltnp \| grep :8000` |
| `role "<user>" does not exist` in psql | The Postgres volume was created with different credentials | Use the user from `docker compose exec api env \| grep DATABASE_URL`, or reset with `docker compose down -v` (deletes all data) |
| 502 or "cannot reach the API" through `:3000` | nginx proxy target is wrong | `frontend-react/nginx.conf` must contain `proxy_pass http://api:8000/;`; rebuild with `docker compose up -d --build frontend` |
| 401 from the console | Wrong or missing API key | Re-enter `API_AUTH_KEY` on the Connection page |
| 429 | Rate limit (20 per minute on QA and analyst routes) | Wait for the `Retry-After` period |

Open a SQL shell: `docker compose exec postgres psql -U <user> -d <db>`.

## 11. Known limitations

- **Single shared API key.** There are no user accounts, tenants or per-document ownership; document
  authorisation only checks that the document exists.
- **Strict verifier.** Paraphrased or long summaries usually show as "unverified".
- **Three document types.** Files not classified as invoice, purchase order or contract get no
  extraction (they are still indexed, so semantic questions work).
- **Processing is required.** Extracted fields and searchable text only exist after
  `/documents/{id}/process`.
- **No streaming.** Answers appear when generation finishes.
- **Scans.** Image-only or OCR-heavy documents have not been validated.

## 12. Before production

1. **Authentication model.** Replace the shared key with per-user auth and document ownership if more
   than one party will use the system.
2. **Redis.** Keep `REDIS_URL` set; the container runs multiple workers, and without Redis the rate
   limit is per worker.
3. **Metrics.** Set `METRICS_AUTH_KEY` and keep `secrets/metrics_auth_key` in sync.
4. **LLM model.** Confirm `LLM_MODEL` is available to your Groq account; startup validates the key
   and host, not the model name.
5. **Backups.** Run one real backup and restore against staging before go-live.
6. **Repository hygiene.** Never commit `.env`, `secrets/` or `storage/` (uploaded documents).
7. **CI.** Add a workflow that runs lint, type checks, `pytest -m "not integration"` and
   `npm run build` on every push.

## 13. Repository layout

```
app/                 FastAPI application (api, documents, parsing, classification, extraction,
                     indexing, retrieval, routing, qa, analyst, drift, security, observability, storage)
alembic/             Database migrations
evaluation/          Benchmarks, datasets, regression and quality gates
frontend-react/      React + Vite console (nginx image for Docker)
monitoring/          Prometheus configuration
scripts/             Setup, seeding, smoke test, baselines, backups, rollback
tests/               Unit and integration tests
docs/                PRODUCTION_ARCHITECTURE.md, SECURITY_REVIEW.md
```

See `docs/PRODUCTION_ARCHITECTURE.md` and `docs/SECURITY_REVIEW.md` for design and security notes.