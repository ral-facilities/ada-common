"""Path lookup helpers."""

from __future__ import annotations

from pathlib import Path


def fetch_system_then_local_path(
    file_name: str,
    service_name: str,
    *,
    system_location: str | Path = "/etc",
    local_location: str | Path = "",
) -> Path | None:
    """Attempt loading a file from a system service directory then local directory."""
    system_path = Path(system_location) / service_name / file_name
    local_path = Path(local_location) / file_name

    if system_path.resolve().is_file():
        return system_path.resolve()
    if local_path.resolve().is_file():
        return local_path.resolve()
    return None
