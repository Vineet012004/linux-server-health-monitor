import json
import logging
import os

logger = logging.getLogger(__name__)

REQUIRED_KEYS = ("cpu_percent", "memory_percent", "disk_percent")


class ConfigError(Exception):
    pass


def load_config(path: str) -> dict:
    """Load and validate config JSON. Returns {'thresholds': {...}}."""
    if not os.path.exists(path):
        raise ConfigError(f"Config file not found: '{path}'. Pass a valid path with --config.")
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in '{path}': {e}") from e
    except OSError as e:
        raise ConfigError(f"Cannot read '{path}': {e}") from e

    if not isinstance(raw, dict):
        raise ConfigError(f"'{path}' must contain a JSON object at the top level.")
    if "thresholds" not in raw:
        raise ConfigError(f"'{path}' is missing the required 'thresholds' key.")

    t = raw["thresholds"]
    if not isinstance(t, dict):
        raise ConfigError(f"'thresholds' must be a JSON object, got {type(t).__name__}.")

    validated = {}
    for key in REQUIRED_KEYS:
        if key not in t:
            raise ConfigError(f"Missing threshold key: '{key}'.")
        val = t[key]
        if not isinstance(val, (int, float)):
            raise ConfigError(f"Threshold '{key}' must be a number, got {type(val).__name__}.")
        if not (0 <= val <= 100):
            raise ConfigError(f"Threshold '{key}' must be 0–100, got {val}.")
        validated[key] = float(val)

    logger.debug("Config loaded from '%s': %s", path, validated)
    return {"thresholds": validated}
