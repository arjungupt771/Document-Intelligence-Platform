# Security Architecture Review — Document Intelligence Platform

## Trust boundaries
1. **Client → API** — untrusted. Mitigated by: bearer auth (app/security/auth.py),
   rate limiting, request body size limit.
2. **Uploaded file → parsers/extractors** — untrusted content, trusted-looking
   extension. Mitigated by: extension allowlist, size limit, content
   verification (parse-to-validate), path-traversal-safe storage.
3. **Retrieved document text → LLM prompt** — untrusted, and this boundary is
   easy to miss because the text looks like "our own data." A malicious or
   adversarially-crafted document is attacker-controlled input to the LLM.
   Mitigated by: prompt delimiting + injection scanning (app/qa/injection_guard.py).
4. **App → PostgreSQL / Qdrant** — semi-trusted infra, but credentials and
   network exposure still matter. Mitigated by: SSL enforcement, no
   credentials in URLs logged, parameterized queries via SQLAlchemy ORM
   (no raw string SQL found in repository.py — keep it that way).

## Known gaps (tracked, not yet fixed)
- No multi-tenancy / per-user ownership model yet — authorization is
  existence-based (see app/security/authorization.py docstring). Acceptable
  for current single-tenant deployment; **must** be revisited before onboarding
  a second customer/tenant.
- Single static API key, not per-client keys — no ability to revoke one
  caller without rotating for everyone. Fine for internal/service-to-service
  use; not fine for third-party API consumers.
- No WAF / TLS termination is assumed to be handled by the deployment
  environment (reverse proxy) — this app does not terminate TLS itself.

## Prioritized findings (this review)
| # | Finding | Severity | Fix |
|---|---|---|---|
| 1 | No startup validation of secrets — app boots with weak/missing API key | High | app/security/secrets.py (Batch 1) |
| 2 | No rate limiting — QA/analyst endpoints are LLM-cost and DoS exposed | High | app/security/rate_limit.py (Batch 1) |
| 3 | No structured security audit trail | Medium | app/security/audit_log.py (Batch 1) |
| 4 | Document text is interpolated into LLM prompts without injection defense | Medium | app/qa/injection_guard.py (Batch 1) |
| 5 | DATABASE_SSLMODE is optional even for non-local hosts | Medium | this batch |
| 6 | No enforced Qdrant auth for non-local URLs | Low (partially mitigated already — see config.py) | this batch |