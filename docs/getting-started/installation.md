# Installation

## Requirements

- Python 3.10 or higher
- An AIOBS API key

## Install via pip

```bash
pip install shepherd-cli
```

## Install via pipx (Recommended)

[pipx](https://pipx.pypa.io/) installs the CLI in an isolated environment:

```bash
pipx install shepherd-cli
```

## Install from source

```bash
git clone https://github.com/neuralis/shepherd-cli
cd shepherd-cli
pip install -e .
```

## Verify Installation

```bash
shepherd --help
```

You should see:

```
 Usage: shepherd [OPTIONS] COMMAND [ARGS]...

 🐑 Debug your AI agents like you debug your code

╭─ Options ────────────────────────────────────────────────────────╮
│ --install-completion    Install completion for the current shell │
│ --show-completion       Show completion for the current shell    │
│ --help                  Show this message and exit               │
╰──────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────╮
│ version    Show version information                              │
│ config     Manage configuration                                  │
│ sessions   List and inspect sessions                             │
╰──────────────────────────────────────────────────────────────────╯
```

## Shell Completion

Enable tab completion:

````{tab-set}

```{tab-item} Bash
shepherd --install-completion bash
```

```{tab-item} Zsh
shepherd --install-completion zsh
```

```{tab-item} Fish
shepherd --install-completion fish
```

````

