# Production Architecture

## Components
- **API** (this app): stateless FastAPI, horizontally scalable behind a load balancer.
  State lives only in Postgres/Qdrant, never in-process (see 16.14 note on the
  rate limiter needing Redis once you run >1 replica).
- **PostgreSQL**: structured data (documents, extractions, insights, drift).
- **Qdrant**: vector store for chunk embeddings.
- **Redis**: shared rate-limit state (required at >1 replica); part of the
  Compose stack, and the API waits for it to be healthy before starting.
- **Groq API** (external, HTTPS): hosted LLM inference via the OpenAI-compatible
  Chat Completions API (model `openai/gpt-oss-120b`). No GPU, local model, or
  model volume is needed. `LLM_URL` must be HTTPS and its host must be on the
  allowlist (`api.groq.com` by default, override with `LLM_ALLOWED_HOSTS`);
  `LLM_API_KEY` is required in production/staging and the app refuses to start
  without it. Provider failures surface as `LLMTimeoutError` /
  `LLMConnectionError` / `LLMResponseError` and the QA API returns 503.

## Environments
`APP_ENV` = `development` | `staging` | `production` (see app/security/secrets.py,
already enforces stricter checks at `production`).

## Data flow
Client → [LB] → API replica(s) → Postgres / Qdrant / Redis
                                     │
                                     └── HTTPS → Groq API
API replicas share no state except through Postgres, Qdrant, and Redis.
Inside Docker Compose the API addresses backing services by service name
(`postgres`, `qdrant`, `redis`), never `localhost`.

## Deployment target
This baseline uses Docker Compose for staging and a single-host production
(simplest thing that works). If/when you outgrow single-host, the same
images move to Kubernetes with no code changes — only the deploy workflow
and health-check wiring change.