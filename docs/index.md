# Shepherd CLI

**Debug your AI agents like you debug your code**

```{button-ref} getting-started/installation
:color: primary
:expand:

Get Started →
```

---

## What is Shepherd?

Shepherd is a command-line tool for inspecting and debugging AI agent sessions. Think of it as **gdb for AI agents**.

::::{grid} 2
:gutter: 3

:::{grid-item-card} 📋 Session Tracking
List, filter, and inspect all your agent sessions from the terminal.
:::

:::{grid-item-card} 🌳 Trace Trees
Visualize execution flows with hierarchical trace trees.
:::

:::{grid-item-card} 📄 JSON Export
Export traces for analysis or integration with other tools.
:::

:::{grid-item-card} 🔌 Provider Agnostic
Works with any LLM provider. Currently supports AIOBS.
:::

::::

---

## Quick Preview

```bash
$ pip install shepherd-cli
$ shepherd config init
$ shepherd sessions list

                              Sessions                              
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┓
┃ ID          ┃ Name         ┃ Started      ┃ Duration ┃ Events ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━┩
│ be393d0d... │ pipeline-ex… │ 2025-12-03   │     9.6s │      4 │
│ 6dfe36bb... │ pipeline-ex… │ 2025-12-03   │     9.8s │      4 │
└─────────────┴──────────────┴──────────────┴──────────┴────────┘
```

---

## Coming Soon

::::{grid} 2
:gutter: 3

:::{grid-item-card} 💻 Interactive Shell
A REPL for exploring sessions with natural language queries.
:::

:::{grid-item-card} 🔄 Deterministic Replay
Replay agent runs with exact inputs and random seeds.
:::

:::{grid-item-card} 🔴 Breakpoints
Set breakpoints on tool calls, LLM invocations, or conditions.
:::

:::{grid-item-card} 🧠 Trace Agent
AI that analyzes your execution traces.
:::

::::

---

```{toctree}
:maxdepth: 2
:caption: Contents
:hidden:

getting-started/installation
getting-started/configuration
getting-started/quickstart
cli/overview
cli/config
cli/sessions
concepts/sessions
concepts/providers
development/contributing
development/testing
```

