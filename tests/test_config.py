"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from shepherd.config import (
    AIOBSConfig,
    CLIConfig,
    ProvidersConfig,
    ShepherdConfig,
    get_api_key,
    get_config_dir,
    get_config_path,
    get_endpoint,
    load_config,
    save_config,
)


class TestShepherdConfig:
    """Tests for config models."""

    def test_default_config(self):
        config = ShepherdConfig()
        assert config.default_provider == "aiobs"
        assert config.providers.aiobs.api_key == ""
        assert config.cli.output_format == "table"
        assert config.cli.color is True

    def test_config_with_values(self):
        config = ShepherdConfig(
            default_provider="aiobs",
            providers=ProvidersConfig(
                aiobs=AIOBSConfig(
                    api_key="test_key",
                    endpoint="https://custom.endpoint.com",
                )
            ),
            cli=CLIConfig(output_format="json", color=False),
        )
        assert config.providers.aiobs.api_key == "test_key"
        assert config.providers.aiobs.endpoint == "https://custom.endpoint.com"
        assert config.cli.output_format == "json"
        assert config.cli.color is False


class TestConfigPaths:
    """Tests for config path functions."""

    def test_get_config_dir_default(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove XDG_CONFIG_HOME if present
            os.environ.pop("XDG_CONFIG_HOME", None)
            config_dir = get_config_dir()
            assert config_dir == Path.home() / ".shepherd"

    def test_get_config_dir_xdg(self):
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/custom/config"}):
            config_dir = get_config_dir()
            assert config_dir == Path("/custom/config/shepherd")

    def test_get_config_path(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("XDG_CONFIG_HOME", None)
            config_path = get_config_path()
            assert config_path == Path.home() / ".shepherd" / "config.toml"


class TestConfigLoadSave:
    """Tests for loading and saving config."""

    def test_load_config_default_when_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("shepherd.config.get_config_path") as mock_path:
                mock_path.return_value = Path(tmpdir) / "nonexistent" / "config.toml"
                config = load_config()
                assert config.default_provider == "aiobs"
                assert config.providers.aiobs.api_key == ""

    def test_save_and_load_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"

            with patch("shepherd.config.get_config_dir") as mock_dir:
                with patch("shepherd.config.get_config_path") as mock_path:
                    mock_dir.return_value = Path(tmpdir)
                    mock_path.return_value = config_path

                    # Create and save config
                    config = ShepherdConfig(
                        providers=ProvidersConfig(
                            aiobs=AIOBSConfig(api_key="test_api_key_12345")
                        )
                    )
                    save_config(config)

                    # Load and verify
                    loaded = load_config()
                    assert loaded.providers.aiobs.api_key == "test_api_key_12345"


class TestGetApiKey:
    """Tests for get_api_key function."""

    def test_api_key_from_env(self):
        with patch.dict(os.environ, {"AIOBS_API_KEY": "env_key_123"}):
            assert get_api_key() == "env_key_123"

    def test_api_key_from_config(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("AIOBS_API_KEY", None)
            with patch("shepherd.config.load_config") as mock_load:
                mock_config = ShepherdConfig(
                    providers=ProvidersConfig(
                        aiobs=AIOBSConfig(api_key="config_key_456")
                    )
                )
                mock_load.return_value = mock_config
                assert get_api_key() == "config_key_456"

    def test_api_key_env_takes_precedence(self):
        """Environment variable should take precedence over config."""
        with patch.dict(os.environ, {"AIOBS_API_KEY": "env_key"}):
            with patch("shepherd.config.load_config") as mock_load:
                mock_config = ShepherdConfig(
                    providers=ProvidersConfig(
                        aiobs=AIOBSConfig(api_key="config_key")
                    )
                )
                mock_load.return_value = mock_config
                assert get_api_key() == "env_key"

    def test_api_key_none_when_not_set(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("AIOBS_API_KEY", None)
            with patch("shepherd.config.load_config") as mock_load:
                mock_config = ShepherdConfig()
                mock_load.return_value = mock_config
                assert get_api_key() is None


class TestGetEndpoint:
    """Tests for get_endpoint function."""

    def test_default_endpoint(self):
        with patch("shepherd.config.load_config") as mock_load:
            mock_load.return_value = ShepherdConfig()
            endpoint = get_endpoint()
            assert "shepherd-api" in endpoint

    def test_custom_endpoint(self):
        with patch("shepherd.config.load_config") as mock_load:
            mock_config = ShepherdConfig(
                providers=ProvidersConfig(
                    aiobs=AIOBSConfig(endpoint="https://custom.api.com")
                )
            )
            mock_load.return_value = mock_config
            assert get_endpoint() == "https://custom.api.com"

