"""Small HTTP boundary with bounded metrics and structured request logs."""

import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import RequestResponseEndpoint

from release_catalog.catalog import Catalog, Environment, Release, ServiceName, load_catalog

logger = logging.getLogger("uvicorn.error")


def create_app(catalog_path: Optional[Path] = None) -> FastAPI:
    path = (
        catalog_path
        if catalog_path is not None
        else Path(os.environ.get("CATALOG_PATH", "data/releases.json"))
    )
    catalog: Catalog = {}
    registry = CollectorRegistry()
    requests = Counter(
        "catalog_http_requests_total",
        "Completed HTTP requests",
        ["route", "method", "status"],
        registry=registry,
    )
    duration = Histogram(
        "catalog_http_request_duration_seconds",
        "HTTP handler duration in seconds",
        ["route", "method", "status"],
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
        registry=registry,
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        catalog.update(load_catalog(path))
        yield
        catalog.clear()

    application = FastAPI(title="Release Catalog", version="0.1.0", lifespan=lifespan)

    @application.middleware("http")
    async def observe(request: Request, call_next: RequestResponseEndpoint) -> Response:
        started = perf_counter()
        request_id = str(uuid4())
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            elapsed = perf_counter() - started
            route = getattr(request.scope.get("route"), "path", "unmatched")
            method = (
                request.method
                if request.method in {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}
                else "OTHER"
            )
            # Scraping should not change application request counters or flood logs.
            if route != "/metrics":
                labels = {"route": route, "method": method, "status": str(status)}
                requests.labels(**labels).inc()
                duration.labels(**labels).observe(elapsed)
                logger.info(
                    json.dumps(
                        {
                            "event": "http_request",
                            "request_id": request_id,
                            "route": route,
                            "method": method,
                            "status": status,
                            "duration_seconds": round(elapsed, 6),
                        }
                    )
                )

    @application.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "alive"}

    @application.get("/health/ready")
    async def ready() -> dict[str, str]:
        if not catalog:
            raise HTTPException(status_code=503, detail="Catalog not loaded")
        return {"status": "ready"}

    @application.get("/v1/releases/{service}", response_model=Release)
    async def release(service: ServiceName, environment: Environment) -> Release:
        result = catalog.get((service, environment))
        if result is None:
            raise HTTPException(status_code=404, detail="Release not found")
        return result

    @application.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(
            content=generate_latest(registry), headers={"Content-Type": CONTENT_TYPE_LATEST}
        )

    return application
