"""Configuration management for Shepherd CLI."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w


class AIOBSConfig(BaseModel):
    """AIOBS provider configuration."""

    api_key: str = ""
    endpoint: str = "https://shepherd-api-48963996968.us-central1.run.app"


class LangfuseConfig(BaseModel):
    """Langfuse provider configuration."""

    public_key: str = ""
    secret_key: str = ""
    host: str = "https://cloud.langfuse.com"


class ProvidersConfig(BaseModel):
    """All provider configurations."""

    aiobs: AIOBSConfig = Field(default_factory=AIOBSConfig)
    langfuse: LangfuseConfig = Field(default_factory=LangfuseConfig)


class CLIConfig(BaseModel):
    """CLI output configuration."""

    output_format: str = "table"  # table | json
    color: bool = True


class ShepherdConfig(BaseModel):
    """Root configuration model."""

    default_provider: str = "aiobs"
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)


def get_config_dir() -> Path:
    """Get the shepherd config directory path."""
    # Check XDG_CONFIG_HOME first, then fall back to ~/.shepherd
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "shepherd"
    return Path.home() / ".shepherd"


def get_config_path() -> Path:
    """Get the config file path."""
    return get_config_dir() / "config.toml"


def load_config() -> ShepherdConfig:
    """Load configuration from file or return defaults."""
    config_path = get_config_path()

    if not config_path.exists():
        return ShepherdConfig()

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    # Handle nested structure
    config_dict: dict[str, Any] = {}

    if "default" in data:
        config_dict["default_provider"] = data["default"].get("provider", "aiobs")

    if "providers" in data:
        config_dict["providers"] = data["providers"]

    if "cli" in data:
        config_dict["cli"] = data["cli"]

    return ShepherdConfig(**config_dict)


def save_config(config: ShepherdConfig) -> None:
    """Save configuration to file."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = get_config_path()

    # Convert to TOML-friendly structure
    data = {
        "default": {"provider": config.default_provider},
        "providers": config.providers.model_dump(),
        "cli": config.cli.model_dump(),
    }

    with open(config_path, "wb") as f:
        tomli_w.dump(data, f)


def get_api_key() -> str | None:
    """Get API key from config or environment."""
    # Environment variable takes precedence
    env_key = os.environ.get("AIOBS_API_KEY")
    if env_key:
        return env_key

    config = load_config()
    api_key = config.providers.aiobs.api_key
    return api_key if api_key else None


def get_endpoint() -> str:
    """Get the AIOBS API endpoint."""
    config = load_config()
    return config.providers.aiobs.endpoint


# Langfuse configuration helpers
def get_langfuse_public_key() -> str | None:
    """Get Langfuse public key from config or environment."""
    # Environment variable takes precedence
    env_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    if env_key:
        return env_key

    config = load_config()
    public_key = config.providers.langfuse.public_key
    return public_key if public_key else None


def get_langfuse_secret_key() -> str | None:
    """Get Langfuse secret key from config or environment."""
    # Environment variable takes precedence
    env_key = os.environ.get("LANGFUSE_SECRET_KEY")
    if env_key:
        return env_key

    config = load_config()
    secret_key = config.providers.langfuse.secret_key
    return secret_key if secret_key else None


def get_langfuse_host() -> str:
    """Get the Langfuse host URL."""
    # Environment variable takes precedence
    env_host = os.environ.get("LANGFUSE_HOST")
    if env_host:
        return env_host

    config = load_config()
    return config.providers.langfuse.host
