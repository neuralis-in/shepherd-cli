"""Config CLI commands."""

from __future__ import annotations

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from shepherd.config import (
    AIOBSConfig,
    LangfuseConfig,
    ProvidersConfig,
    ShepherdConfig,
    get_config_path,
    load_config,
    save_config,
)

app = typer.Typer(help="Manage Shepherd configuration")
console = Console()


@app.command("init")
def init_config(
    provider: str = typer.Option(
        None,
        "--provider",
        "-p",
        help="Provider to configure: aiobs or langfuse (if not specified, configures both)",
    ),
):
    """Initialize Shepherd configuration interactively."""
    console.print("\n[bold]🐑 Shepherd Configuration Setup[/bold]\n")

    # Check if config already exists
    config_path = get_config_path()
    existing_config = None
    if config_path.exists():
        overwrite = Prompt.ask(
            f"Config already exists at {config_path}. Update?",
            choices=["y", "n"],
            default="y",
        )
        if overwrite.lower() != "y":
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit()
        existing_config = load_config()

    # Start with existing config or defaults
    aiobs_config = existing_config.providers.aiobs if existing_config else AIOBSConfig()
    langfuse_config = existing_config.providers.langfuse if existing_config else LangfuseConfig()
    default_provider = existing_config.default_provider if existing_config else "aiobs"

    # Configure AIOBS if requested or no specific provider
    if provider is None or provider == "aiobs":
        console.print("[bold cyan]AIOBS Configuration[/bold cyan]")
        api_key = Prompt.ask(
            "Enter your AIOBS API key (leave empty to skip)",
            password=True,
            default="",
        )
        if api_key:
            aiobs_config.api_key = api_key
            endpoint = Prompt.ask(
                "Enter AIOBS API endpoint",
                default=aiobs_config.endpoint,
            )
            aiobs_config.endpoint = endpoint
            default_provider = "aiobs"
        console.print()

    # Configure Langfuse if requested or no specific provider
    if provider is None or provider == "langfuse":
        console.print("[bold cyan]Langfuse Configuration[/bold cyan]")
        public_key = Prompt.ask(
            "Enter your Langfuse public key (leave empty to skip)",
            default="",
        )
        if public_key:
            langfuse_config.public_key = public_key
            secret_key = Prompt.ask(
                "Enter your Langfuse secret key",
                password=True,
            )
            if not secret_key:
                console.print(
                    "[red]Langfuse secret key is required when public key is provided.[/red]"
                )
                raise typer.Exit(1)
            langfuse_config.secret_key = secret_key
            host = Prompt.ask(
                "Enter Langfuse host",
                default=langfuse_config.host,
            )
            langfuse_config.host = host
            if provider == "langfuse":
                default_provider = "langfuse"
        console.print()

    # Create and save config
    config = ShepherdConfig(
        default_provider=default_provider,
        providers=ProvidersConfig(
            aiobs=aiobs_config,
            langfuse=langfuse_config,
        ),
    )
    save_config(config)

    console.print(f"[green]✓[/green] Config saved to [cyan]{config_path}[/cyan]")

    # Show next steps based on what was configured
    console.print(f"\n[bold]Default provider:[/bold] {default_provider}")
    if aiobs_config.api_key:
        console.print("\nAIOBS commands: [bold]shepherd sessions list[/bold]")
    if langfuse_config.public_key:
        console.print("Langfuse commands: [bold]shepherd traces list[/bold]")
    console.print("\nSwitch provider: [bold]shepherd config set provider <aiobs|langfuse>[/bold]")
    console.print()


@app.command("show")
def show_config():
    """Show current configuration."""
    config = load_config()
    config_path = get_config_path()

    # Mask AIOBS API key
    masked_aiobs_key = ""
    if config.providers.aiobs.api_key:
        key = config.providers.aiobs.api_key
        masked_aiobs_key = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else "***"

    # Mask Langfuse keys
    masked_lf_public = ""
    if config.providers.langfuse.public_key:
        key = config.providers.langfuse.public_key
        masked_lf_public = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"

    masked_lf_secret = ""
    if config.providers.langfuse.secret_key:
        key = config.providers.langfuse.secret_key
        masked_lf_secret = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"

    content = f"""[bold]Default Provider:[/bold] {config.default_provider}

[bold]AIOBS:[/bold]
  API Key:  {masked_aiobs_key or "[dim]not set[/dim]"}
  Endpoint: {config.providers.aiobs.endpoint}

[bold]Langfuse:[/bold]
  Public Key: {masked_lf_public or "[dim]not set[/dim]"}
  Secret Key: {masked_lf_secret or "[dim]not set[/dim]"}
  Host:       {config.providers.langfuse.host}

[bold]CLI:[/bold]
  Output Format: {config.cli.output_format}
  Color:         {config.cli.color}"""

    rprint(Panel(content, title=f"[bold]Config[/bold] ({config_path})", expand=False))


@app.command("set")
def set_config(
    key: str = typer.Argument(..., help="Config key (e.g., aiobs.api_key, langfuse.public_key)"),
    value: str = typer.Argument(..., help="Value to set"),
):
    """Set a configuration value."""
    config = load_config()

    # Parse the key
    parts = key.lower().split(".")

    if parts[0] == "aiobs":
        if len(parts) != 2:
            console.print(f"[red]Invalid key: {key}[/red]")
            raise typer.Exit(1)

        if parts[1] == "api_key":
            config.providers.aiobs.api_key = value
        elif parts[1] == "endpoint":
            config.providers.aiobs.endpoint = value
        else:
            console.print(f"[red]Unknown key: {key}[/red]")
            raise typer.Exit(1)
    elif parts[0] == "langfuse":
        if len(parts) != 2:
            console.print(f"[red]Invalid key: {key}[/red]")
            raise typer.Exit(1)

        if parts[1] == "public_key":
            config.providers.langfuse.public_key = value
        elif parts[1] == "secret_key":
            config.providers.langfuse.secret_key = value
        elif parts[1] == "host":
            config.providers.langfuse.host = value
        else:
            console.print(f"[red]Unknown key: {key}[/red]")
            raise typer.Exit(1)
    elif parts[0] == "cli":
        if len(parts) != 2:
            console.print(f"[red]Invalid key: {key}[/red]")
            raise typer.Exit(1)

        if parts[1] == "output_format":
            if value not in ("table", "json"):
                console.print("[red]output_format must be 'table' or 'json'[/red]")
                raise typer.Exit(1)
            config.cli.output_format = value
        elif parts[1] == "color":
            config.cli.color = value.lower() in ("true", "1", "yes")
        else:
            console.print(f"[red]Unknown key: {key}[/red]")
            raise typer.Exit(1)
    elif parts[0] in ("default_provider", "provider"):
        if value not in ("aiobs", "langfuse"):
            console.print("[red]provider must be 'aiobs' or 'langfuse'[/red]")
            raise typer.Exit(1)
        config.default_provider = value
    else:
        console.print(f"[red]Unknown key: {key}[/red]")
        console.print(
            "[dim]Available keys: provider, aiobs.api_key, aiobs.endpoint, "
            "langfuse.public_key, langfuse.secret_key, langfuse.host, cli.output_format, cli.color[/dim]"
        )
        raise typer.Exit(1)

    save_config(config)
    console.print(f"[green]✓[/green] Set [cyan]{key}[/cyan]")


@app.command("get")
def get_config(
    key: str = typer.Argument(..., help="Config key to get"),
):
    """Get a configuration value."""
    config = load_config()
    parts = key.lower().split(".")

    value = None

    if parts[0] in ("default_provider", "provider"):
        value = config.default_provider
    elif parts[0] == "aiobs":
        if len(parts) == 2:
            if parts[1] == "api_key":
                raw = config.providers.aiobs.api_key
                value = f"{raw[:10]}...{raw[-4:]}" if raw and len(raw) > 14 else raw or ""
            elif parts[1] == "endpoint":
                value = config.providers.aiobs.endpoint
    elif parts[0] == "langfuse":
        if len(parts) == 2:
            if parts[1] == "public_key":
                raw = config.providers.langfuse.public_key
                value = f"{raw[:8]}...{raw[-4:]}" if raw and len(raw) > 12 else raw or ""
            elif parts[1] == "secret_key":
                raw = config.providers.langfuse.secret_key
                value = f"{raw[:8]}...{raw[-4:]}" if raw and len(raw) > 12 else raw or ""
            elif parts[1] == "host":
                value = config.providers.langfuse.host
    elif parts[0] == "cli":
        if len(parts) == 2:
            if parts[1] == "output_format":
                value = config.cli.output_format
            elif parts[1] == "color":
                value = str(config.cli.color)

    if value is None:
        console.print(f"[red]Unknown key: {key}[/red]")
        raise typer.Exit(1)

    console.print(value)
