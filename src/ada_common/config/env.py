"""Environment variable injection from ADA dotenv files."""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class EnvVarInjector:  # pylint: disable=too-few-public-methods
    """Load env vars with precedence: process env > env-specific > local > default.

    Each known environment declares exactly which files it loads. An unrecognised
    environment falls back to loading whatever exists, failing only if nothing does.
    """

    def __init__(
        self,
        service_name: str,
        *,
        default_environment: str = "manual",
    ) -> None:
        self.service_name = service_name
        self.default_environment = default_environment

        self.env = self._determine_config_environment()
        self.config_dir = self._determine_config_dir()

    def inject_all(self) -> None:
        """Load the configuration files for the active environment."""
        match self.env:
            case "prod":
                # Ansible renders a complete config.env.prod only
                self._load_required(f"config.env.{self.env}")

            case "stack":
                # Vars come from the compose stack; files supply local creds + baseline.
                self._load_required("config.local")
                self._load_required("config.default")

            case "manual":
                self._load_required(f"config.env.{self.env}")
                self._load_required("config.local")
                self._load_required("config.default")

            case "k8s":
                # Secrets arrive via envFrom at runtime; only the baked baseline is on
                # disk. config.env.k8s is optional (ada-ui ships one; the API services
                # have no k8s delta to override).
                self._load_optional(f"config.env.{self.env}")
                self._load_required("config.default")

            case _:
                self._inject_unknown_env()

    def _inject_unknown_env(self) -> None:
        """Best-effort load for an unrecognised environment: take whatever exists."""
        loaded = [
            self._load_optional(f"config.env.{self.env}"),
            self._load_optional("config.local"),
            self._load_optional("config.default"),
        ]
        if not any(loaded):
            msg = f'No config files found for environment "{self.env}", exiting'
            print(msg, file=sys.stderr)
            logger.error(msg)
            self._exit()

    def _determine_config_environment(self) -> str:
        """Return ADA_CONFIG_ENVIRONMENT or default to 'manual'."""
        env = os.getenv("ADA_CONFIG_ENVIRONMENT")
        if not env:
            msg = (
                '"ADA_CONFIG_ENVIRONMENT" not set, '
                f'defaulting to "{self.default_environment}"'
            )
            print(msg, file=sys.stderr)
            logger.warning(msg)
            env = self.default_environment

        env = env.lower()
        print(f'Using environment: "{env}"')
        logger.info('Using environment: "%s"', env)
        return env

    def _determine_config_dir(self) -> Path:
        """Find the directory holding this environment's config files."""
        candidates = (
            f"config.env.{self.env}",
            "config.local",
            "config.default",
        )

        for location in self._config_locations():
            if any((location / candidate).is_file() for candidate in candidates):
                print(f"Using config dir: {location}")
                logger.info("Using config dir: %s", location)
                return location

        msg = "No config files found, exiting"
        print(msg, file=sys.stderr)
        logger.error(msg)
        self._exit()

    def _config_locations(self) -> Sequence[Path]:
        return [Path(f"/etc/{self.service_name}"), Path(".env")]

    def _load_optional(self, filename: str) -> bool:
        """Load a config file if present (no override). Return whether it was loaded."""
        path = self.config_dir / filename
        if not path.is_file():
            return False

        load_dotenv(path, override=False)
        print(f"Loaded {path}")
        logger.info("Loaded %s", path)
        return True

    def _load_required(self, filename: str) -> None:
        """Load a config file that must exist; exit if it is missing."""
        if self._load_optional(filename):
            return

        path = self.config_dir / filename
        print(f"ERROR: {path} not found, exiting...", file=sys.stderr)
        logger.error("%s not found, exiting...", path)
        self._exit()

    @staticmethod
    def _exit() -> NoReturn:
        sys.exit(1)
