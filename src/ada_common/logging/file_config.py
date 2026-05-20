"""Logging configuration helpers."""

from __future__ import annotations

import logging.config
import sys
from pathlib import Path

from ada_common.config.paths import fetch_system_then_local_path


def initialise_file_config_logging(
    service_name: str,
    *,
    file_name: str = "log.ini",
    system_location: str | Path = "/etc",
    local_location: str | Path = "",
    logs_root: str | Path = "/var/log",
) -> None:
    """Initialise logging from a service log.ini found in /etc/<service> or locally."""
    logs_dir_path = (Path(logs_root) / service_name).resolve()
    logs_dir_path.mkdir(parents=True, exist_ok=True)

    log_ini_path = fetch_system_then_local_path(
        file_name,
        service_name,
        system_location=system_location,
        local_location=local_location,
    )
    if not log_ini_path:
        print(f"{file_name} not found in {Path(system_location) / service_name}/ or locally")
        sys.exit(1)

    logging.config.fileConfig(log_ini_path)

