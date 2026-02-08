"""Tests for configuration loading with layered priority and validation."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from exmailer.config import load_config
from exmailer.exceptions import ConfigurationError


class TestConfigValidation:
    """Test configuration validation logic."""

    def test_missing_required_fields_raises_error(self, clean_environment):
        """Test that missing required fields raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_config()

        error_msg = str(exc_info.value).lower()
        assert "missing required configuration" in error_msg
        assert any(
            field in error_msg
            for field in ["domain", "username", "password", "server", "email_domain"]
        )

    def test_partial_config_raises_error(self, clean_environment):
        """Test that partial config (missing critical fields) raises error."""
        os.environ["EXCHANGE_DOMAIN"] = "company"
        os.environ["EXCHANGE_USER"] = "john.doe"

        with pytest.raises(ConfigurationError) as exc_info:
            load_config()

        assert "missing required configuration" in str(exc_info.value).lower()

    def test_invalid_auth_type_raises_error(self, minimal_config_env):
        """Test that invalid auth_type values raise ConfigurationError."""
        os.environ["EXCHANGE_AUTH_TYPE"] = "INVALID"

        with pytest.raises(ConfigurationError) as exc_info:
            load_config()

        assert "invalid auth_type" in str(exc_info.value).lower()
        assert "ntlm" in str(exc_info.value).lower()
        assert "basic" in str(exc_info.value).lower()


class TestConfigSourcesPriority:
    """Test layered configuration loading with proper priority."""

    def test_programmatic_config_highest_priority(self, minimal_config_env, tmp_path):
        """Test that programmatic config overrides all other sources."""
        os.environ["EXCHANGE_DOMAIN"] = "env-domain"
        os.environ["EXCHANGE_SERVER"] = "env-server.com"

        config_file = tmp_path / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "domain": "file-domain",
                    "server": "file-server.com",
                    "username": "file-user",
                    "password": "file-pass",
                    "email_domain": "file.com",
                }
            )
        )

        config = load_config(
            config_path=str(config_file),
            config_dict={
                "domain": "prog-domain",
                "server": "prog-server.com",
                "username": "prog-user",
                "password": "prog-pass",
                "email_domain": "prog.com",
            },
        )

        assert config["domain"] == "prog-domain"
        assert config["server"] == "prog-server.com"
        assert config["username"] == "prog-user"

    def test_config_file_overrides_env(self, minimal_config_env, tmp_path):
        """Test that explicit config file overrides environment variables."""
        os.environ["EXCHANGE_DOMAIN"] = "wrong-domain"
        os.environ["EXCHANGE_SERVER"] = "wrong-server.com"

        config_file = tmp_path / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "domain": "correct-domain",
                    "server": "correct-server.com",
                    "username": "john.doe",
                    "password": "secure_password",
                    "email_domain": "company.com",
                }
            )
        )

        config = load_config(str(config_file))

        assert config["domain"] == "correct-domain"
        assert config["server"] == "correct-server.com"

    def test_env_fallback_when_no_file_provided(self, minimal_config_env):
        """Test that env vars are used when no config file is provided."""
        config = load_config()

        assert config["domain"] == "company"
        assert config["username"] == "john.doe"
        assert config["server"] == "mail.company.com"

    def test_safe_defaults_applied_last(self, minimal_config_env):
        """Test that safe defaults (non-sensitive) are applied only when missing."""
        os.environ.pop("EXCHANGE_AUTH_TYPE", None)
        os.environ.pop("EXCHANGE_SAVE_COPY", None)

        config = load_config()

        assert config["auth_type"] == "NTLM"
        assert config["save_copy"] is True


class TestConfigFileHandling:
    """Test config file loading and error handling."""

    def test_missing_config_file_with_no_fallback_raises_error(self, clean_environment):
        """Test that missing config file with no env vars raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_config("/nonexistent/path.json")

        error_msg = str(exc_info.value).lower()
        assert "config file not found:" in error_msg

    def test_invalid_json_raises_error(self, tmp_path):
        """Test that invalid JSON in config file raises ConfigurationError."""
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("{invalid json}")

        with pytest.raises(ConfigurationError) as exc_info:
            load_config(str(bad_json))

        assert "invalid json" in str(exc_info.value).lower()

    def test_empty_json_file_uses_fallback_sources(self, tmp_path, minimal_config_env):
        """Test that empty JSON file doesn't break loading (falls back to env)."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("{}")

        config = load_config(str(empty_file))

        assert config["domain"] == "company"
        assert config["username"] == "john.doe"

    @pytest.mark.parametrize("content", ["", "   ", "\n"])
    def test_whitespace_only_file_uses_fallback(self, tmp_path, minimal_config_env, content):
        """Test that whitespace-only files are treated as empty."""
        whitespace_file = tmp_path / "whitespace.json"
        whitespace_file.write_text(content)

        config = load_config(str(whitespace_file))
        assert config["domain"] == "company"

    def test_yaml_config_file_support(self, tmp_path, clean_environment):
        """Test loading configuration from YAML file."""
        yaml_file = tmp_path / "config.yaml"
        yaml_content = """
domain: yaml-domain
username: yaml-user
password: yaml-pass
server: yaml-server.com
email_domain: yaml.com
auth_type: BASIC
save_copy: false
"""
        yaml_file.write_text(yaml_content)

        mock_yaml = MagicMock()
        mock_yaml.safe_load.return_value = {
            "domain": "yaml-domain",
            "username": "yaml-user",
            "password": "yaml-pass",
            "server": "yaml-server.com",
            "email_domain": "yaml.com",
            "auth_type": "BASIC",
            "save_copy": False,
        }

        with patch.dict(sys.modules, {"yaml": mock_yaml}):
            config = load_config(str(yaml_file))
            assert config["domain"] == "yaml-domain"
            assert config["auth_type"] == "BASIC"
            assert config["save_copy"] is False

    def test_yaml_not_installed_raises_helpful_error(self, tmp_path):
        """Test that missing pyyaml gives helpful error message."""
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text("domain: test")

        with patch.dict(sys.modules, {"yaml": None}):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config(str(yaml_file))

        assert "pyyaml" in str(exc_info.value).lower()
        assert "pip install pyyaml" in str(exc_info.value).lower()


class TestConfigNormalization:
    """Test config key normalization and alias support."""

    def test_config_aliases_normalized(self, tmp_path):
        """Test that common config aliases are normalized to standard keys."""
        alias_config = tmp_path / "aliases.json"
        alias_config.write_text(
            json.dumps(
                {
                    "exchange_domain": "alias-domain",
                    "user": "alias-user",
                    "pass": "alias-pass",
                    "host": "alias-host.com",
                    "domain_name": "alias.com",
                    "authentication": "BASIC",
                    "save": False,
                }
            )
        )

        config = load_config(str(alias_config))

        assert config["domain"] == "alias-domain"
        assert config["username"] == "alias-user"
        assert config["password"] == "alias-pass"
        assert config["server"] == "alias-host.com"
        assert config["email_domain"] == "alias.com"
        assert config["auth_type"] == "BASIC"
        assert config["save_copy"] is False

    def test_boolean_normalization(self, tmp_path):
        """Test that various boolean representations are normalized correctly."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
            ("off", False),
            (True, True),
            (False, False),
        ]

        for input_val, expected in test_cases:
            config_file = tmp_path / f"bool_{input_val!s}.json"
            config_file.write_text(
                json.dumps(
                    {
                        "domain": "test",
                        "username": "user",
                        "password": "pass",
                        "server": "srv.com",
                        "email_domain": "test.com",
                        "save_copy": input_val,
                    }
                )
            )

            config = load_config(str(config_file))
            assert config["save_copy"] == expected, f"Failed for input: {input_val}"


class TestAutoDiscovery:
    """Test automatic config file discovery in standard locations."""

    def test_auto_discovery_in_cwd(self, tmp_path, clean_environment):
        """Test that config file in current working directory is auto-discovered."""
        config_file = tmp_path / "exmailer.json"
        config_file.write_text(
            json.dumps(
                {
                    "domain": "cwd-domain",
                    "username": "cwd-user",
                    "password": "cwd-pass",
                    "server": "cwd-server.com",
                    "email_domain": "cwd.com",
                }
            )
        )

        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            config = load_config()
            assert config["domain"] == "cwd-domain"
            assert config["username"] == "cwd-user"
        finally:
            os.chdir(original_cwd)

    def test_auto_discovery_priority_order(self, tmp_path, clean_environment, monkeypatch):
        """Test that auto-discovery follows correct priority order."""
        mock_home = tmp_path / "fake_home"
        mock_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: mock_home)

        # Lower priority
        (mock_home / ".exmailer.json").write_text(
            json.dumps(
                {
                    "domain": "home-domain",
                    "username": "home",
                    "password": "p",
                    "server": "s",
                    "email_domain": "e",
                }
            )
        )

        # Higher priority
        cwd_config = tmp_path / "exmailer.json"
        cwd_config.write_text(
            json.dumps(
                {
                    "domain": "cwd-domain",
                    "username": "cwd",
                    "password": "p",
                    "server": "s",
                    "email_domain": "e",
                }
            )
        )

        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            config = load_config()
            # CWD > Home
            assert config["domain"] == "cwd-domain"
        finally:
            os.chdir(original_cwd)

    def test_explicit_path_skips_auto_discovery(self, tmp_path, clean_environment):
        """Test that explicit config_path skips auto-discovery."""
        (tmp_path / "exmailer.json").write_text(
            json.dumps(
                {
                    "domain": "wrong-domain",
                    "username": "u",
                    "password": "p",
                    "server": "s",
                    "email_domain": "e",
                }
            )
        )

        explicit_config = tmp_path / "explicit.json"
        explicit_config.write_text(
            json.dumps(
                {
                    "domain": "correct-domain",
                    "username": "u",
                    "password": "p",
                    "server": "s",
                    "email_domain": "e",
                }
            )
        )

        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            config = load_config(str(explicit_config))
            assert config["domain"] == "correct-domain"
        finally:
            os.chdir(original_cwd)


class TestSecurityAndEdgeCases:
    """Test security-sensitive scenarios and edge cases."""

    def test_empty_password_rejected(self, clean_environment):
        os.environ["EXCHANGE_DOMAIN"] = "company"
        os.environ["EXCHANGE_USER"] = "user"
        os.environ["EXCHANGE_PASS"] = ""
        os.environ["EXCHANGE_SERVER"] = "srv.com"
        os.environ["EXCHANGE_EMAIL_DOMAIN"] = "company.com"

        with pytest.raises(ConfigurationError) as exc_info:
            load_config()

        assert "password" in str(exc_info.value).lower()

    def test_whitespace_password_rejected(self, clean_environment):
        os.environ["EXCHANGE_DOMAIN"] = "company"
        os.environ["EXCHANGE_USER"] = "user"
        os.environ["EXCHANGE_PASS"] = "   "
        os.environ["EXCHANGE_SERVER"] = "srv.com"
        os.environ["EXCHANGE_EMAIL_DOMAIN"] = "company.com"

        with pytest.raises(ConfigurationError) as exc_info:
            load_config()

        assert "password" in str(exc_info.value).lower()

    def test_dotenv_file_support(self, tmp_path, clean_environment):
        """Test that .env file is loaded if python-dotenv available."""
        # Setup specific valid config for this test
        env_vars = {
            "EXCHANGE_DOMAIN": "dotenv-domain",
            "EXCHANGE_USER": "dotenv-user",
            "EXCHANGE_PASS": "dotenv-pass",
            "EXCHANGE_SERVER": "dotenv-server.com",
            "EXCHANGE_EMAIL_DOMAIN": "dotenv.com",
        }

        mock_dotenv = MagicMock()

        # Side effect: when load_dotenv() is called, populate os.environ
        def load_dotenv_side_effect(**kwargs):
            os.environ.update(env_vars)
            return True

        mock_dotenv.load_dotenv.side_effect = load_dotenv_side_effect

        with patch.dict(sys.modules, {"dotenv": mock_dotenv}):
            original_cwd = Path.cwd()
            try:
                os.chdir(tmp_path)
                config = load_config()

                assert mock_dotenv.load_dotenv.called
                assert config["domain"] == "dotenv-domain"
                assert config["username"] == "dotenv-user"
            finally:
                os.chdir(original_cwd)

    def test_config_with_extra_fields_ignored(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "domain": "test",
                    "username": "user",
                    "password": "pass",
                    "server": "srv.com",
                    "email_domain": "test.com",
                    "extra": "ignore me",
                }
            )
        )
        config = load_config(str(config_file))
        assert config["domain"] == "test"
        assert "extra" not in config
