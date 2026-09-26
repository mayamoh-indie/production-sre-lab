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

The initial Docker check could not connect to `//./pipe/docker_engine`; local Docker config access was also denied. On the user-requested retry, sandbox checks still returned access denied, but approved execution outside the sandbox reached Docker Desktop successfully. The current blocker was sandbox access, not an unavailable engine. No paid infrastructure was touched.

## Verification ledger

Environment: Windows, Python **3.13.15**. Checks run on 2026-09-26; native HTTP and security checks around **16:54 UTC**. Implementation recorded in commit `dfb0d71` (originally `4baf88e` before the account attribution correction). Initial checks were local; publication and hosted CI evidence are recorded below.

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
| Docker build/start | Follow-up: image built and Compose reported healthy; see Docker evidence below |
| GitHub Actions | Published; Python and container jobs passed in run 36258075951 |
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

This single request timing is diagnostic evidence, not a benchmark or a measured latency SLO. The temporary native server was stopped after verification; no background service was left running. Both virtual environments are ignored by Git. The project is a standalone local repository with implementation and documentation commits; the subsequent publication is recorded below.

Phase 1 handoff: **native, container and hosted-CI baseline complete**. The shared SRE readiness gate remains unmet: end-to-end delivery/observability, real SLO/alert/incident evidence, and the final portfolio review still belong to later phases.

## Interview questions and defensible answers

**Why no database?** The consumer needs an approved build lookup; a versioned read-only artifact is sufficient. Avoiding writes/transactions keeps the exercise focused on deployment and reliability. A database would become useful for authenticated updates, audit history or high update frequency.

**Why readiness and liveness?** Liveness asks whether the process responds. Readiness asks whether the validated catalog is available. Bad configuration should stop startup, not produce partial success. These do not prove end-to-end reachability.

**Why not EKS immediately?** Local kind can demonstrate Kubernetes/Helm/GitOps without recurring AWS cost. Real EKS has a separately billed control plane and workers; I will only claim EKS deployment after actually running and tearing it down.

**How do you avoid misleading latency graphs?** Use seconds and explicit histogram buckets; filter by endpoint/status, account for availability separately, document that timing ends at response creation, and treat missing traffic as no data.

**What did the tests catch?** They rejected a malformed demo commit ID before the app could serve an invalid release artifact. Tests also cover bad JSON, null/blank/types, duplicates, unknown lookups, invalid parameters, telemetry cardinality, log redaction and server-error accounting.

**What is still missing?** Real scrape/dashboard/trace pipeline, Kubernetes/GitOps, an executed incident/postmortem, and cloud lifecycle evidence. These are planned, not completed skills claims.

## Next improvement and handoff

Continue the explicitly separate local Kubernetes/Helm/GitOps phase, including scan/SBOM evidence and immutable image references. Final project descriptions, resume bullets and hiring-manager reviews are deferred until there is sufficient evidence across the full project.

## Docker follow-up — 2026-09-26

User requested another Docker/WSL check. Outside the sandbox, `docker version` reached Docker Desktop 4.90.0, Engine 29.7.2, linux/amd64, context `desktop-linux`. WSL enumeration succeeded: version 2, Ubuntu installed/stopped, `docker-desktop` running. Ubuntu itself was not started or modified.

- `docker compose up --build --wait --wait-timeout 60`: exit 0; built the image and reported container healthy.
- Real HTTP over the published loopback port: live/ready 200; known release 200 with version `2026.09.25`; unknown release 404; invalid environment 422; metrics 200. Request-ID headers were present on non-scrape responses.
- Lookup counter series for 200, 404 and 422 each had value 1.0 after one request per case. Request events appeared in container logs.
- `docker compose exec -T catalog id`: UID/GID 10001 (`appuser`).
- `docker compose exec -T catalog python -m pip check`: no broken requirements.
- Container inspection: read-only root filesystem true, capability drop `["ALL"]`, security option `["no-new-privileges:true"]`; published address `127.0.0.1:8000`.
- `docker compose down --volumes --remove-orphans`: removed this project's container and network. `docker compose ps --all` showed no remaining project containers. The local image/build cache remains available for reuse.

No application or container configuration change was needed. Docker runtime verification is now complete; this is still not a hosted GitHub Actions run, Kubernetes deployment, or AWS deployment.

## Pre-publication review — 2026-09-26

The user authorized a public GitHub repository. Reviewed all 22 tracked files; virtual environments, caches, credentials and private master-context files are not tracked. Gitleaks scanned all three existing commits with default rules and `--redact --log-opts=--all`: exit 0, no leaks found (47.56 KB scanned). Scanner image: `ghcr.io/gitleaks/gitleaks@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f`. A clean scan reduces risk; it does not prove that every possible secret would be detected.

Publication completed after GitHub CLI authentication and authorization of the workflow scope. Hosted workflow evidence follows.


## GitHub publication and CI — 2026-09-26

Public repository: [mayamoh-indie/production-sre-lab](https://github.com/mayamoh-indie/production-sre-lab).

[Actions run 36258075951](https://github.com/mayamoh-indie/production-sre-lab/actions/runs/36258075951) completed successfully. The Python job installed pinned dependencies, checked formatting/lint, ran tests and Bandit, and compiled the code. The container job built the image, waited for readiness, checked the successful lookup and expected 404 over HTTP, read metrics, and removed the Compose resources.

The user requested account-linked commit attribution. Initial commits used the configured name Yash Kaushik, but GitHub did not associate the configured email with the account. Changed author/committer email to `102919441+mayamoh-indie@users.noreply.github.com`, preserving each commit tree, message and timestamp; updated the newly published branch with an explicit force-with-lease. GitHub's commits API then confirmed `mayamoh-indie` for both author and committer on every commit. Repository-local Git identity now uses this address for future commits. No assistant co-author attribution was added.

The initial successful run predates that metadata correction; the subsequent push triggers the same checks again. Future status is visible through the README workflow badge. No AWS resources were deployed, and the larger SRE readiness gate remains open.

## Incremental delivery plan — 2026-09-26

Added `implementation-plan.md` in response to the request for small, comprehensible changes. It maps the existing architecture phases into individual changes with dependencies, review questions, verification and milestone handoffs. Existing history remains intact. The next implementation is A1 (maintain CI action runtimes); this documentation change does not implement later infrastructure.

Decision: pair a behavior change with its relevant tests/docs instead of splitting them into artificial commits. Separate independent concerns such as image scanning and SBOM generation. GitOps rollback must revert desired state; Helm rollback belongs to the earlier pre-Argo exercise. Learning checkpoint: explain why a healthy probe, a successful deployment and an SLO measurement prove different things.
