"""Robust configuration loading with layered priority and validation."""

import json
import logging
import os
from pathlib import Path
from typing import Any

from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


def load_config(
    config_path: str | None = None,
    config_dict: dict[str, Any] | None = None,
    use_env: bool = True,
) -> dict[str, Any]:
    """
    Load configuration with layered priority.
    """
    config: dict[str, Any] = {}

    # Layer 3 & 2: Config Files
    if config_path:
        # Explicit file
        file_config = _load_config_file(config_path)
        config.update(_normalize_config(file_config))
        logger.info(f"✓ Loaded configuration from {config_path}")

    elif not config_dict:
        # Implicit discovery
        # MOVED HERE: Define paths dynamically to respect os.chdir()
        default_paths = [
            Path.cwd() / "exmailer.json",
            Path.cwd() / "exmailer.yaml",
            Path.home() / ".config" / "exmailer" / "config.json",
            Path.home() / ".exmailer.json",
            Path.home() / ".exmailer.yaml",
        ]

        for path in default_paths:
            if path.exists():
                file_config = _load_config_file(str(path))
                config.update(_normalize_config(file_config))
                logger.info(f"✓ Loaded configuration from discovered file: {path}")
                break

    # Layer 1: Programmatic config (Highest priority)
    if config_dict:
        config.update(_normalize_config(config_dict))
        logger.debug("✓ Loaded configuration from programmatic dict")

    # Layer 4: Environment variables
    if use_env:
        env_config = _load_env_config()
        for key, value in env_config.items():
            if key not in config or config[key] is None:
                config[key] = value

    # Layer 5: Safe defaults
    defaults = {
        "auth_type": "NTLM",
        "save_copy": True,
    }
    for key, value in defaults.items():
        if key not in config or config[key] is None:
            config[key] = value

    # Final validation
    _validate_required_fields(config)
    return config


def _load_config_file(path: str) -> dict[str, Any] | Any:
    """Load configuration from JSON or YAML file."""
    path_obj = Path(path).expanduser().resolve()

    if not path_obj.exists():
        raise ConfigurationError(f"Config file not found: {path}")

    try:
        if path_obj.suffix in (".yaml", ".yml"):
            try:
                import yaml

                with open(path_obj, encoding="utf-8") as f:
                    content = f.read()
                    if not content.strip():
                        return {}
                    return yaml.safe_load(content) or {}
            except ImportError:
                raise ConfigurationError(  # noqa: B904
                    "YAML support requires 'pyyaml' package. Install with: pip install pyyaml"
                )
            except Exception as e:
                raise ConfigurationError(f"Invalid YAML in {path}: {e}")  # noqa: B904
        else:  # JSON (default)
            with open(path_obj, encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    return {}
                return json.loads(content)
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in {path}: {e}")  # noqa: B904
    except Exception as e:
        raise ConfigurationError(f"Failed to parse config file {path}: {e}")  # noqa: B904


def _load_env_config() -> dict[str, Any]:
    """Load configuration from environment variables."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    return {
        "domain": os.getenv("EXCHANGE_DOMAIN"),
        "username": os.getenv("EXCHANGE_USER"),
        "password": os.getenv("EXCHANGE_PASS"),
        "server": os.getenv("EXCHANGE_SERVER"),
        "email_domain": os.getenv("EXCHANGE_EMAIL_DOMAIN"),
        "auth_type": os.getenv("EXCHANGE_AUTH_TYPE"),
        "save_copy": _parse_bool_env("EXCHANGE_SAVE_COPY"),
    }


def _parse_bool_env(var_name: str) -> bool | None:
    """Parse boolean environment variable."""
    value = os.getenv(var_name)
    if value is None:
        return None
    value_lower = value.lower()
    if value_lower in ("true", "1", "yes", "on", "y"):
        return True
    if value_lower in ("false", "0", "no", "off", "n"):
        return False
    return None


def _normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    """Normalize config keys to standard names and types."""
    if not isinstance(config, dict):
        raise ConfigurationError(f"Invalid configuration: expected dict, got {type(config)}")

    normalized = {}
    key_mapping = {
        "domain": ["domain", "exchange_domain", "ad_domain"],
        "username": ["username", "user", "exchange_user"],
        "password": ["password", "pass", "exchange_pass"],
        "server": ["server", "exchange_server", "host"],
        "email_domain": ["email_domain", "domain_name", "smtp_domain"],
        "auth_type": ["auth_type", "authentication", "auth"],
        "save_copy": ["save_copy", "save", "save_sent"],
    }

    for std_key, aliases in key_mapping.items():
        for alias in aliases:
            if alias in config:
                normalized[std_key] = config[alias]
                break

    if "save_copy" in normalized:
        val = normalized["save_copy"]
        if isinstance(val, str):
            normalized["save_copy"] = val.lower() in ("true", "1", "yes", "on")
        elif not isinstance(val, bool):
            normalized["save_copy"] = bool(val)

    return normalized


def _validate_required_fields(config: dict[str, Any]) -> None:
    """Validate that all required fields are present and non-empty."""
    required_fields = ["domain", "username", "password", "server", "email_domain"]
    missing = []

    for field in required_fields:
        val = config.get(field)
        # Check for None or empty string or whitespace-only string
        if not val or (isinstance(val, str) and not val.strip()):
            missing.append(field)

    if missing:
        example_config = {
            "domain": "your-domain",
            "username": "john.doe",
            "password": "your-password",
            "server": "mail.yourcompany.com",
            "email_domain": "yourcompany.com",
            "auth_type": "NTLM",
            "save_copy": True,
        }

        raise ConfigurationError(
            f"Missing required configuration fields: {', '.join(missing)}\n\n"
            "Provide configuration via one of these methods:\n"
            "1. Programmatic: ExchangeEmailer(config={...})\n"
            "2. Config file: ExchangeEmailer(config_path='path/to/config.json')\n"
            "3. Environment variables (see documentation)\n"
            "4. Place config.json in current directory or ~/.config/exmailer/\n\n"
            f"Example config.json:\n{json.dumps(example_config, indent=2, ensure_ascii=False)}"
        )

    valid_auth_types = ["NTLM", "BASIC"]
    if config["auth_type"] and config["auth_type"].upper() not in valid_auth_types:
        raise ConfigurationError(
            f"Invalid auth_type '{config['auth_type']}'. "
            f"Valid values: {', '.join(valid_auth_types)}"
        )
