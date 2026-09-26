import json
from pathlib import Path

import pytest

from release_catalog.catalog import load_catalog

RELEASE: dict[str, str] = {
    "service": "matchmaking",
    "environment": "production",
    "version": "1.0.0",
    "commit": "a" * 40,
}


def test_catalog_lookup(tmp_path: Path) -> None:
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps([RELEASE]), encoding="utf-8")
    assert load_catalog(path)[("matchmaking", "production")].version == "1.0.0"


@pytest.mark.parametrize(
    "payload",
    [
        "{",
        "null",
        "{}",
        "[]",
        "[null]",
        "[{}]",
        json.dumps([RELEASE, RELEASE]),
        *[
            json.dumps([{**RELEASE, "version": value}])
            for value in [None, "", " ", 1, "bad version"]
        ],
        json.dumps([{**RELEASE, "environment": "dev"}]),
        json.dumps([{**RELEASE, "commit": "nope"}]),
        json.dumps([{**RELEASE, "extra": "unexpected"}]),
    ],
)
def test_invalid_catalog_fails_as_a_unit(tmp_path: Path, payload: str) -> None:
    path = tmp_path / "catalog.json"
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(ValueError):
        load_catalog(path)


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Cannot load catalog"):
        load_catalog(tmp_path / "missing.json")
