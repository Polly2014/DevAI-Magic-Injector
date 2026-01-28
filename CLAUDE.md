# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/claude-code) when working with code in this repository.

## Project Overview

DevAI-Magic-Injector is a Python-based research and testing project for injecting and modifying AI code statistics in Microsoft developer tools. It targets two systems:

1. **CodeBlend** - Microsoft's code tracking extension that monitors AI vs human code contributions
2. **MAI AI Telemetry** - Microsoft's AI telemetry system that tracks AI-assisted coding sessions

## Project Structure

```
DevAI-Magic-Injector/
├── src/
│   ├── codeblend_injector.py     # CodeBlend statistics injector
│   └── ai_telemetry_injector.py  # AI Telemetry injector
├── docs/
│   └── ARCHITECTURE.md           # Architecture documentation
├── tests/                        # Test files (empty)
└── examples/                     # Example files (empty)
```

## Technology Stack

- **Language**: Python 3 (standard library only, no external dependencies)
- **Key Modules**: argparse, json, subprocess, pathlib, datetime, glob

## Common Commands

### CodeBlend Injector

```bash
# View current status
python src/codeblend_injector.py status

# Inject AI statistics (default 95% ratio)
python src/codeblend_injector.py inject --ratio 0.95

# Install git hook
python src/codeblend_injector.py install --repo /path/to/repo --type pre

# Uninstall git hook
python src/codeblend_injector.py uninstall --repo /path/to/repo --type pre
```

### AI Telemetry Injector

```bash
# View telemetry cache status
python src/ai_telemetry_injector.py status

# Inject session statistics
python src/ai_telemetry_injector.py session --lines 2000 --ratio 0.95

# Inject specific commit
python src/ai_telemetry_injector.py commit <hash> --repo <repo_name>

# Batch inject all commits
python src/ai_telemetry_injector.py all --repo <repo_name>
```

## Key Data Paths

- **CodeBlend data**: `~/.codeblend/vscode/`
  - `document-state.json` - Current document tracking state
  - `commits/*.json` - Per-commit statistics

- **AI Telemetry data**: `~/.vscode-server/data/User/globalStorage/mai-engineeringsystems.mai-ai-telemetry/`
  - `metrics_cache.json` - Session and commit metrics cache

## Code Architecture

### codeblend_injector.py

Main functions:
- `cmd_status()` - Display current tracking status
- `cmd_inject()` - Inject AI states into document-state.json (pre-commit)
- `cmd_patch()` - Modify existing commit JSON files (post-commit)
- `cmd_precommit()` / `cmd_postcommit()` - Git hook integration
- `cmd_install_hook()` / `cmd_uninstall_hook()` - Git hook management

Line state values: `0=unchanged`, `1=Human`, `2=AI`

### ai_telemetry_injector.py

Main functions:
- `cmd_status()` - Display telemetry cache status
- `cmd_inject_session()` - Modify Claude Code session statistics
- `cmd_inject_commit()` - Add AI markers to specific commits
- `cmd_inject_all()` - Batch inject all commits

## Development Notes

- No build step required - pure Python scripts
- All scripts use argparse for CLI interface
- Git subprocess calls used for repository operations
- JSON files are read/modified/written for data manipulation

## Testing

Run from project root:
```bash
python -m pytest tests/
```

Note: Test directory is currently empty and needs test implementations.
