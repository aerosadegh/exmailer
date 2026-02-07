"""Robust configuration loading with layered priority and validation."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)

# Standard config file locations (searched in order)
DEFAULT_CONFIG_PATHS = [
    Path.cwd() / "exmailer.json",
    Path.cwd() / "exmailer.yaml",
    Path.home() / ".config" / "exmailer" / "config.json",
    Path.home() / ".exmailer.json",
    Path.home() / ".exmailer.yaml",
]


def load_config(
    config_path: Optional[str] = None,
    config_dict: Optional[Dict[str, Any]] = None,
    use_env: bool = True,
) -> Dict[str, Any]:
    """
    Load configuration with layered priority:
    1. config_dict (programmatic - highest priority)
    2. config_path (explicit file path)
    3. DEFAULT_CONFIG_PATHS (implicit file discovery)
    4. Environment variables (if use_env=True)
    5. Safe defaults (non-sensitive values only)

    Args:
        config_path: Explicit path to config file (JSON/YAML)
        config_dict: Direct configuration dictionary
        use_env: Whether to fall back to environment variables

    Returns:
        Validated configuration dictionary

    Raises:
        ConfigurationError: If required fields are missing after all sources exhausted
    """
    config: Dict[str, Any] = {}

    # Layer 1: Programmatic config (highest priority)
    if config_dict:
        config.update(_normalize_config(config_dict))
        logger.debug("✓ Loaded configuration from programmatic dict")

    # Layer 2: Explicit config file
    if config_path:
        file_config = _load_config_file(config_path)
        config.update(_normalize_config(file_config))
        logger.info(f"✓ Loaded configuration from {config_path}")

    # Layer 3: Implicit config file discovery (only if no explicit sources yet)
    elif not config_dict and not config_path:
        for path in DEFAULT_CONFIG_PATHS:
            if path.exists():
                file_config = _load_config_file(str(path))
                config.update(_normalize_config(file_config))
                logger.info(f"✓ Loaded configuration from discovered file: {path}")
                break

    # Layer 4: Environment variables (optional fallback)
    if use_env:
        env_config = _load_env_config()
        # Only merge values not already set (lower priority)
        for key, value in env_config.items():
            if key not in config or config[key] is None:
                config[key] = value

    # Layer 5: Safe defaults (non-sensitive only)
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


def _load_config_file(path: str) -> Dict[str, Any]:
    """Load configuration from JSON or YAML file."""
    path_obj = Path(path).expanduser().resolve()

    if not path_obj.exists():
        raise ConfigurationError(f"Config file not found: {path}")

    try:
        if path_obj.suffix in (".yaml", ".yml"):
            try:
                import yaml

                with open(path_obj, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Handle empty files
                    if not content.strip():
                        return {}
                    return yaml.safe_load(content) or {}
            except ImportError:
                raise ConfigurationError(
                    "YAML support requires 'pyyaml' package. " "Install with: pip install pyyaml"
                )
            except Exception as e:
                raise ConfigurationError(f"Invalid YAML in {path}: {e}")
        else:  # JSON (default)
            with open(path_obj, "r", encoding="utf-8") as f:
                content = f.read()
                # Handle empty files
                if not content.strip():
                    return {}
                return json.loads(content)
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in {path}: {e}")
    except Exception as e:
        raise ConfigurationError(f"Failed to parse config file {path}: {e}")


def _load_env_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    # Optional: Load .env file if python-dotenv available
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass  # .env support is optional

    return {
        "domain": os.getenv("EXCHANGE_DOMAIN"),
        "username": os.getenv("EXCHANGE_USER"),
        "password": os.getenv("EXCHANGE_PASS"),
        "server": os.getenv("EXCHANGE_SERVER"),
        "email_domain": os.getenv("EXCHANGE_EMAIL_DOMAIN"),
        "auth_type": os.getenv("EXCHANGE_AUTH_TYPE"),
        "save_copy": _parse_bool_env("EXCHANGE_SAVE_COPY"),
    }


def _parse_bool_env(var_name: str) -> Optional[bool]:
    """Parse boolean environment variable."""
    value = os.getenv(var_name)
    if value is None:
        return None
    value_lower = value.lower()
    if value_lower in ("true", "1", "yes", "on", "y"):
        return True
    if value_lower in ("false", "0", "no", "off", "n"):
        return False
    return None  # Invalid value - will be handled by validation


def _normalize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize config keys to standard names and types."""
    if not isinstance(config, dict):
        raise ConfigurationError(f"Invalid configuration: expected dict, got {type(config)}")

    normalized = {}
    key_mapping = {
        # Support common aliases
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

    # Normalize boolean values
    if "save_copy" in normalized:
        val = normalized["save_copy"]
        if isinstance(val, str):
            normalized["save_copy"] = val.lower() in ("true", "1", "yes", "on")
        elif not isinstance(val, bool):
            normalized["save_copy"] = bool(val)

    return normalized


def _validate_required_fields(config: Dict[str, Any]) -> None:
    """Validate that all required fields are present and non-empty."""
    required_fields = ["domain", "username", "password", "server", "email_domain"]
    missing = [field for field in required_fields if not config.get(field)]

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

    # Validate auth_type
    valid_auth_types = ["NTLM", "BASIC"]
    if config["auth_type"] and config["auth_type"].upper() not in valid_auth_types:
        raise ConfigurationError(
            f"Invalid auth_type '{config['auth_type']}'. "
            f"Valid values: {', '.join(valid_auth_types)}"
        )
