# Local operating runbook

This is a Phase 1 diagnostic guide, not evidence of an incident simulation.

1. Check `/health/live` and `/health/ready` locally. No connection means inspect process startup/output and port 8000; a status response means HTTP reached the process.
2. Request the known `matchmaking`/`production` entry. A 404 means a valid key is absent; a 422 means the service/environment input failed validation. Compare with the checked-in catalog before changing code.
3. Correlate the returned `X-Request-ID` with the request event. Inspect status and route template, not raw user input. For an unhandled 500, inspect the server traceback and request event timestamp (the outer error response has no ID header yet).
4. Read `/metrics` and check the exact lookup route/status series. A missing series before its first request is normal. Restarting resets process counters; Prometheus will need `rate`/`increase` later.
5. For startup failure, confirm the working directory, `CATALOG_PATH`, file permissions, JSON shape, allowed values, commit length and uniqueness. No partial records are accepted. Restore the last known valid artifact and restart; do not bypass validation.

| Symptom | Action |
|---|---|
| `Cannot load catalog` | Validate artifact schema and path; default resolves from current working directory |
| Python imports fail | Use the repository virtual environment and install the package editable |
| File edits do not change responses | Restart the Python process; rebuild the image for container data edits |
| Docker daemon pipe/socket missing | Start Docker Desktop in Linux-container mode; `docker version` must show a server |
| Docker config access denied | Inspect local Docker permissions/context; do not copy registry credentials into the repo |
| Port 8000 already used | Stop your old instance or choose another host port; do not terminate unrelated processes |
| Metrics differ across requests with multiple workers | Return to one worker; multi-process metrics are not configured |

For a native rollback, restore a known-good catalog/application version and restart the documented Uvicorn command. For a container rollback, use the previously verified image; immutable digests and GitOps rollback evidence arrive in Phase 2. Verify readiness, one successful lookup, one expected 404 and metrics after recovery. Stop native development with Ctrl+C or Compose with `docker compose down --volumes --remove-orphans`.

The later incident drill will record trigger, impact, detection, mitigation, UTC timestamps, observed recovery, and follow-up actions. Do not write a completed postmortem until those events actually occurred.
