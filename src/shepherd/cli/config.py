"""Config CLI commands."""

from __future__ import annotations

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from shepherd.config import (
    AIOBSConfig,
    ProvidersConfig,
    ShepherdConfig,
    get_config_path,
    load_config,
    save_config,
)

app = typer.Typer(help="Manage Shepherd configuration")
console = Console()


@app.command("init")
def init_config():
    """Initialize Shepherd configuration interactively."""
    console.print("\n[bold]🐑 Shepherd Configuration Setup[/bold]\n")

    # Check if config already exists
    config_path = get_config_path()
    if config_path.exists():
        overwrite = Prompt.ask(
            f"Config already exists at {config_path}. Overwrite?",
            choices=["y", "n"],
            default="n",
        )
        if overwrite.lower() != "y":
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit()

    # Get API key
    api_key = Prompt.ask(
        "Enter your AIOBS API key",
        password=True,
    )

    if not api_key:
        console.print("[red]API key is required.[/red]")
        raise typer.Exit(1)

    # Get endpoint (with default)
    endpoint = Prompt.ask(
        "Enter AIOBS API endpoint",
        default="https://shepherd-api-48963996968.us-central1.run.app",
    )

    # Create and save config
    config = ShepherdConfig(
        default_provider="aiobs",
        providers=ProvidersConfig(
            aiobs=AIOBSConfig(api_key=api_key, endpoint=endpoint)
        ),
    )
    save_config(config)

    console.print(f"\n[green]✓[/green] Config saved to [cyan]{config_path}[/cyan]")
    console.print("\nYou can now use [bold]shepherd sessions list[/bold] to see your sessions.\n")


@app.command("show")
def show_config():
    """Show current configuration."""
    config = load_config()
    config_path = get_config_path()

    # Mask API key
    masked_key = ""
    if config.providers.aiobs.api_key:
        key = config.providers.aiobs.api_key
        masked_key = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else "***"

    content = f"""[bold]Provider:[/bold] {config.default_provider}

[bold]AIOBS:[/bold]
  API Key:  {masked_key or "[dim]not set[/dim]"}
  Endpoint: {config.providers.aiobs.endpoint}

[bold]CLI:[/bold]
  Output Format: {config.cli.output_format}
  Color:         {config.cli.color}"""

    rprint(Panel(content, title=f"[bold]Config[/bold] ({config_path})", expand=False))


@app.command("set")
def set_config(
    key: str = typer.Argument(..., help="Config key (e.g., aiobs.api_key, aiobs.endpoint)"),
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
    else:
        console.print(f"[red]Unknown key: {key}[/red]")
        console.print("[dim]Available keys: aiobs.api_key, aiobs.endpoint, cli.output_format, cli.color[/dim]")
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

    if parts[0] == "aiobs":
        if len(parts) == 2:
            if parts[1] == "api_key":
                raw = config.providers.aiobs.api_key
                value = f"{raw[:10]}...{raw[-4:]}" if raw and len(raw) > 14 else raw or ""
            elif parts[1] == "endpoint":
                value = config.providers.aiobs.endpoint
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

