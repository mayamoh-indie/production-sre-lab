# Portfolio notes and evidence

## Phase 1 — 2026-09-26

Project scope: an internal read-only release catalog, with reliability and delivery as the primary product. All project changes stay in `production-sre-lab/`. Shared readiness gate remains open; later engineering projects are not activated. This is portfolio experience and does not replace or inflate professional experience.

Implemented: typed artifact validation and lookup, explicit 404/422 errors, fail-fast startup, health endpoints, request IDs and structured event payloads, bounded Prometheus counter/histogram, unit/API tests, Docker/Compose configuration, CI checks and Bandit. No network calls in catalog calculation; no database or write API needed.

## Decisions and learning

- A validated immutable deployment artifact reduces failure modes and supports rollback. Tradeoff: updates need a restart and approval happens upstream, not in this API.
- Reject duplicate service/environment keys rather than invent first/last-wins semantics. A deployment artifact is an atomic unit; per-record skipping would hide a bad release.
- Metrics need a bounded vocabulary. Route templates avoid one time series per arbitrary service/path, and request IDs belong in logs rather than labels.
- Separate success-conditioned latency and availability; failed requests must not disappear from the reliability story. Empty windows mean no data.
- TestClient exercises the ASGI boundary, but a real local TCP server is also needed to validate launch instructions. Container/hosted CI evidence must be recorded separately.

## Problems encountered

Initial dependency installation hit sandbox socket restrictions. Retried through the approved network permission path and installed successfully into the project virtual environment. Initial API tests rejected the synthetic staging commit ID because its length was not 40; inspected the actual value length, fixed the fixture and reran the tests. Startup error chaining was removed so invalid catalog values do not appear in validation tracebacks.

Docker client exists, but `docker version` could not connect to `//./pipe/docker_engine`; local Docker config access was also denied. Container configuration is not container execution evidence. No paid infrastructure was touched.

## Verification ledger

Environment: Windows, Python **3.13.15**. Checks run on 2026-09-26; native HTTP and security checks around **16:54 UTC**. Implementation recorded in local commit `4baf88e`. No remote or hosted workflow run exists.

| Check | Observed result |
|---|---|
| `python -m pytest -q --tb=short` | 26 passed in 0.35s in `.venv` |
| Fresh `.venv-verify`: install `requirements-dev.lock`, then `pip install --no-deps -e .` | Successful; 26 tests passed again in 0.39s |
| `python -m ruff format --check src tests` | 5 files already formatted |
| `python -m ruff check src tests` | All checks passed |
| `python -m bandit -r src` | No issues; 131 code lines scanned, 0 skipped |
| `python -m pip check` | No broken requirements in both environments |
| `python -m compileall -q .` | Exit 0, including the fresh environment |
| `docker compose config --quiet` | Exit 0; Docker config permission warnings remain |
| Workflow YAML parse and job-key check | Passed; this does not validate GitHub execution |
| Native Uvicorn launch | Application startup complete; loopback port 8000 accepted real HTTP |
| Docker build/start | Not executed: daemon unavailable |
| GitHub Actions | Configured, not executed or published |
| AWS | Pricing research only; no deployed resources |

Tests emit one `StarletteDeprecationWarning`: the installed Starlette TestClient deprecates HTTPX in favor of HTTPX2. The current pinned combination passes; migration of the test client is a future maintenance task. No warning was suppressed.

Actual native HTTP results:

```text
GET /health/live                                      200 {"status":"alive"}
GET /health/ready                                     200 {"status":"ready"}
GET /v1/releases/matchmaking?environment=production    200 version=2026.09.25
GET /v1/releases/unknown?environment=production        404 {"detail":"Release not found"}
GET /v1/releases/matchmaking?environment=dev           422 literal_error on query.environment
GET /metrics                                         200
catalog_http_requests_total{method="GET",route="/v1/releases/{service}",status="200"} 1.0
catalog_http_requests_total{method="GET",route="/v1/releases/{service}",status="404"} 1.0
catalog_http_requests_total{method="GET",route="/v1/releases/{service}",status="422"} 1.0
```

The HTTP check also asserted a response request-ID header for each non-scrape response. A real log event observed from that run:

```text
INFO:     {"event": "http_request", "request_id": "07a4b804-6655-41f6-a1d4-d72f0f150df3", "route": "/v1/releases/{service}", "method": "GET", "status": 200, "duration_seconds": 0.000328}
```

This single request timing is diagnostic evidence, not a benchmark or a measured latency SLO. The temporary native server was stopped after verification; no background service was left running. Both virtual environments are ignored by Git. The project is a standalone local repository with implementation and documentation commits; nothing was published.

Phase 1 handoff: **native baseline complete**, with container-runtime and hosted-CI checks outstanding. The shared SRE readiness gate remains unmet: end-to-end delivery/observability, real SLO/alert/incident evidence, and the final portfolio review still belong to later phases.

## Interview questions and defensible answers

**Why no database?** The consumer needs an approved build lookup; a versioned read-only artifact is sufficient. Avoiding writes/transactions keeps the exercise focused on deployment and reliability. A database would become useful for authenticated updates, audit history or high update frequency.

**Why readiness and liveness?** Liveness asks whether the process responds. Readiness asks whether the validated catalog is available. Bad configuration should stop startup, not produce partial success. These do not prove end-to-end reachability.

**Why not EKS immediately?** Local kind can demonstrate Kubernetes/Helm/GitOps without recurring AWS cost. Real EKS has a separately billed control plane and workers; I will only claim EKS deployment after actually running and tearing it down.

**How do you avoid misleading latency graphs?** Use seconds and explicit histogram buckets; filter by endpoint/status, account for availability separately, document that timing ends at response creation, and treat missing traffic as no data.

**What did the tests catch?** They rejected a malformed demo commit ID before the app could serve an invalid release artifact. Tests also cover bad JSON, null/blank/types, duplicates, unknown lookups, invalid parameters, telemetry cardinality, log redaction and server-error accounting.

**What is still missing?** Verified containers/hosted CI, real scrape/dashboard/trace pipeline, Kubernetes/GitOps, an executed incident/postmortem, and cloud lifecycle evidence. These are planned, not completed skills claims.

## Next improvement and handoff

First verify the container and hosted CI from a clean checkout. Then continue the explicitly separate local Kubernetes/Helm/GitOps phase, including scan/SBOM evidence and immutable image references. Final project descriptions, resume bullets and hiring-manager reviews are deferred until there is sufficient evidence across the full project.
