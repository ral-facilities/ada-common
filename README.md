# ada-common

Shared Python helpers for ADA services.

## Install

```bash
pip install "ada-common @ git+https://github.com/ral-facilities/ada-common.git@v0.1.0"
```

## Env injection

```python
from ada_common.config import EnvVarInjector

EnvVarInjector(service_name="ada-api").inject_all()
```

## Logging helpers

```python
from ada_common.logging import initialise_file_config_logging

initialise_file_config_logging(service_name="ada-api")
```

