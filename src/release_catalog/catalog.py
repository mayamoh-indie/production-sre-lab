"""Validate a deployment artifact before accepting traffic."""

from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, TypeAdapter, ValidationError

ServiceName = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]{0,39}$")]
Environment = Literal["staging", "production"]


class Release(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    service: ServiceName
    environment: Environment
    version: Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")]
    commit: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]


Catalog = dict[tuple[str, Environment], Release]


def load_catalog(path: Path) -> Catalog:
    """Reject malformed, empty or ambiguous catalogs; never silently skip releases."""
    try:
        releases = TypeAdapter(list[Release]).validate_json(path.read_bytes())
    except (OSError, ValidationError):
        # Do not echo arbitrary catalog values into startup logs.
        raise ValueError(f"Cannot load catalog at {path}: check file access and schema") from None
    if not releases:
        raise ValueError("Catalog must contain at least one release")
    catalog: Catalog = {}
    for release in releases:
        key = (release.service, release.environment)
        if key in catalog:
            raise ValueError(f"Duplicate catalog key: {key}")
        catalog[key] = release
    return catalog
