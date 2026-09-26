# Telemetry and reliability contract

## Implemented

`catalog_http_requests_total{route,method,status}` counts HTTP responses and unhandled handler exceptions (as 500). `catalog_http_request_duration_seconds` records time through response creation with buckets including 0.25 seconds. It does not measure the client's network time or completion of a streamed response body. This API returns small JSON responses, not streams.

Routes use templates such as `/v1/releases/{service}`; unmatched paths use `unmatched`. Service names, raw URLs, request IDs, query strings and other caller-controlled values are never metric labels. Method labels use a finite allowlist plus `OTHER`. Health/docs traffic is counted separately and can be filtered; `/metrics` is excluded to avoid self-generated traffic. No process-global collector registry is shared between app instances.

Each non-scrape request emits an event with a JSON payload containing `request_id`, route template, bounded method, status and duration. Uvicorn's default logger prefixes the JSON message; the whole log line is not strict JSON. Access logs are disabled by the documented command to avoid logging query strings. A newly generated `X-Request-ID` header lets a client correlate normal responses with events; incoming IDs are not trusted. Unhandled exceptions are counted/logged but the outer server error response does not receive this header. Error tracebacks and startup logs are separate from request events.

## Proposed SLOs — not measured or enforced yet

Scope: `GET /v1/releases/{service}`, over a rolling 30 days, across all replicas. Exclude 4xx client errors, health, docs and scrapes from eligible requests; track the 4xx rate separately because a catalog regression could manifest as 404. Eligibility is 2xx or 5xx responses. External probes are required to detect outages that cannot emit application counters.

- Availability: `2xx / (2xx + 5xx) >= 99.9%`. Error budget: `0.001 * eligible requests`. At 100,000 eligible requests, 100 failures exhaust the budget.
- Latency: `successful requests <= 250 ms / successful requests >= 99%`. Budget: `0.01 * successful requests`. This is a separate success-conditioned latency SLO, not an availability substitute.
- Zero eligible requests: **no data**, not 100% available. Zero successful requests: latency is **no data**, while availability reflects failures if present. Alert separately on missing scrapes and synthetic probe failure.
- Histogram bucket counts define the threshold directly; no percentile interpolation convention is needed. A later p95 dashboard must label Prometheus histogram quantiles as estimates.

When implemented, availability burn rate is `(5xx / eligible) / 0.001`. Proposed fast page: burn >14.4 in both 1h and 5m windows; slow page: >6 in both 6h and 30m. Gate ratio alerts on observed traffic, and add probe/missing-data alerts so low-volume outages are not hidden. Unit-test recording rules for zero traffic, absent series, all-success and all-failure cases before enabling them.

Phase 3 adds Prometheus scraping, Grafana dashboards, traces via OpenTelemetry, tested alert rules and a reproducible bounded fault. Phase 1 contains no scraper, dashboard, trace backend or executed incident drill, and no measured SLO attainment claim.
