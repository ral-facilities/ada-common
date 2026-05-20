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
    """Load env vars with precedence: process env > env-specific > local > default."""

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
        """Load the selected configuration files."""
        if self.env == "prod":
            self._load_if_exists(self.config_dir / "config.env.prod")
            return

        self._inject_env_specific_vars()
        self._load_if_exists(self.config_dir / "config.local")
        self._load_if_exists(self.config_dir / "config.default")

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
        """Find directory containing the required config file."""
        required_config = "config.env.prod" if self.env == "prod" else "config.default"

        for location in self._config_locations():
            if (location / required_config).is_file():
                print(f"Using config dir: {location}")
                logger.info("Using config dir: %s", location)
                return location

        msg = f"No {required_config} found, exiting"
        print(msg, file=sys.stderr)
        logger.error(msg)
        self._exit()

    def _config_locations(self) -> Sequence[Path]:
        return [Path(f"/etc/{self.service_name}"), Path(".env")]

    @staticmethod
    def _load_if_exists(path: Path) -> None:
        """Load .env file if present (no override)."""
        if path.is_file():
            load_dotenv(path, override=False)
            print(f"Loaded {path}")
            logger.info("Loaded %s", path)
            return

        print(f"ERROR: {path} not found, exiting...", file=sys.stderr)
        logger.error("%s not found, exiting...", path)
        EnvVarInjector._exit()

    def _inject_env_specific_vars(self) -> None:
        """Load config.env.<env> unless using stack-provided vars."""
        if self.env == "stack":
            msg = "Using vars from Ada stack"
            print(msg)
            logger.info(msg)
            return

        env_file = self.config_dir / f"config.env.{self.env}"
        self._load_if_exists(env_file)

    @staticmethod
    def _exit() -> NoReturn:
        sys.exit(1)
