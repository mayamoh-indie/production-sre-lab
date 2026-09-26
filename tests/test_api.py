import json
import logging
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from release_catalog.app import create_app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app(Path("data/releases.json"))) as session:
        yield session


def test_lookup_and_health(client: TestClient) -> None:
    for path in ("/health/live", "/health/ready"):
        assert client.get(path).status_code == 200
    response = client.get("/v1/releases/matchmaking", params={"environment": "production"})
    assert response.status_code == 200
    assert response.json()["version"] == "2026.09.25"
    assert response.headers["x-request-id"]


@pytest.mark.parametrize(
    ("path", "status"),
    [
        ("/v1/releases/unknown?environment=production", 404),
        ("/v1/releases/matchmaking?environment=dev", 422),
        ("/v1/releases/matchmaking", 422),
        ("/v1/releases/INVALID?environment=production", 422),
    ],
)
def test_lookup_errors(client: TestClient, path: str, status: int) -> None:
    assert client.get(path).status_code == status


def test_metrics_are_bounded_and_scrapes_excluded(client: TestClient) -> None:
    client.get("/v1/releases/matchmaking?environment=production")
    client.get("/v1/releases/secret-customer?environment=production")
    client.get("/arbitrary-secret-path")
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert 'route="/v1/releases/{service}",status="200"} 1.0' in metrics.text
    assert 'route="/v1/releases/{service}",status="404"} 1.0' in metrics.text
    assert 'route="unmatched"' in metrics.text
    assert "secret" not in metrics.text
    assert 'route="/metrics"' not in metrics.text
    assert 'le="0.25"' in metrics.text
    assert client.get("/metrics").text == metrics.text


def test_logs_omit_raw_input(client: TestClient, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        response = client.get("/v1/releases/private-name?environment=production&token=secret")
    event = json.loads(caplog.records[-1].message)
    assert event["request_id"] == response.headers["x-request-id"]
    assert event["status"] == 404
    assert "private-name" not in caplog.text
    assert "secret" not in caplog.text


def test_invalid_catalog_prevents_startup(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="at least one"):
        with TestClient(create_app(path)):
            pytest.fail("Invalid catalog accepted")


def test_unhandled_failure_is_counted() -> None:
    app = create_app(Path("data/releases.json"))

    @app.get("/test-failure")
    async def fail() -> None:
        raise RuntimeError("test-only fault")

    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.get("/test-failure").status_code == 500
        assert 'route="/test-failure",status="500"} 1.0' in client.get("/metrics").text
