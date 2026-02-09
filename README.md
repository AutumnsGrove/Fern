# Fern 🌿

A voice training feedback companion that hooks into your existing dictation workflow. Fern listens when you speak, shows you what your voice is doing, and helps you grow toward the voice you want. No dedicated practice sessions required.

## Overview

Fern integrates seamlessly with your existing dictation setup. When you trigger dictation with your hotkey, Fern captures your voice, analyzes pitch and resonance in real-time, and provides immediate visual feedback through a Hammerspoon overlay. Over time, it tracks your progress and helps you build a voice that feels like you.

### Key Features

- 🎙️ **Passive Listening** - Captures audio during normal dictation, no extra effort needed
- 📊 **Real-time Feedback** - Live pitch and resonance visualization via Hammerspoon overlay
- 📈 **Progress Tracking** - Long-term trends stored in SQLite with rolling audio archives
- 🎯 **Interactive Charts** - Historical trend visualization with keyboard navigation
- 🔒 **Privacy-First** - All data stays local on your machine
- ⌨️ **Keyboard Control** - Full keyboard navigation for chart views

## Quick Start

### Prerequisites

- macOS (for Hammerspoon integration)
- Python 3.11+
- [UV package manager](https://docs.astral.sh/uv/)
- [Hammerspoon](https://www.hammerspoon.org/go/)

### Installation

#### Option 1: Automated Install

```bash
# Clone the repository
git clone https://github.com/autumnsgrove/fern.git
cd fern

# Run installation script
./install.sh
```

#### Option 2: Manual Install

```bash
# Clone the repository
git clone https://github.com/autumnsgrove/fern.git
cd fern

# Install Python dependencies
uv sync

# Install Fern CLI
uv pip install -e .

# Install Hammerspoon config
mkdir -p ~/.hammerspoon
cp hammerspoon/init.lua ~/.hammerspoon/fern.lua
cp hammerspoon/overlay.lua ~/.hammerspoon/
cp hammerspoon/charts.lua ~/.hammerspoon/
cp hammerspoon/chart_view.lua ~/.hammerspoon/

# Add to Hammerspoon init
echo 'require("fern")' >> ~/.hammerspoon/init.lua

# Reload Hammerspoon (Ctrl+Cmd+R)
```

### Setup After Installation

1. **Reload Hammerspoon**: Click the Hammerspoon icon in your menu bar and select "Reload Config"
2. **Verify installation**: Run `fern status` in Terminal
3. **Configure targets**: Set your target pitch range with `fern config:set-target 100 200`

## Usage

### CLI Commands

```bash
# Show current status
fern status

# Test pitch detection with microphone
fern test

# View pitch trends (last 7 days with sparklines)
fern trend

# List recent training sessions
fern sessions

# Review a specific session
fern review <session-id>

# Export training data
fern export --format csv --days 30

# Send chart data to Hammerspoon
fern chart --send --days 7

# Show current configuration
fern config:show

# Set target pitch range
fern config:set-target 100 200

# Show Fern version
fern version
```

### Keyboard Shortcuts

When Hammerspoon is running, use these hotkeys:

| Hotkey | Action |
|--------|--------|
| `Ctrl+Alt+Shift+F` | Start voice capture |
| `Ctrl+Alt+Shift+S` | Stop voice capture |
| `Ctrl+Alt+Shift+O` | Toggle overlay display |
| `Ctrl+Alt+Shift+C` | Toggle chart view |

#### Chart View Navigation

| Key | Action |
|-----|--------|
| `1` | Pitch Trend view |
| `2` | Resonance Profile view |
| `3` | Session Summary view |
| `←` / `→` | Previous/Next view |
| `7` | 7-day time range |
| `8` | 30-day time range |
| `9` | 90-day time range |
| `H` | Show help |
| `ESC` / `Q` | Close chart view |

## Architecture

Fern uses a two-layer architecture:

```
┌─────────────────────────────────────────────────────────┐
│  GUI Layer (Hammerspoon - Lua)                         │
│  ├── Global hotkey detection (same key as Hex)          │
│  ├── Live overlay display (pitch bar, resonance arc)    │
│  ├── Chart view (historical trends)                     │
│  └── Keyboard navigation                                │
├─────────────────────────────────────────────────────────┤
│  Backend Layer (Python 3.11+)                           │
│  ├── Audio capture (sounddevice)                        │
│  ├── Pitch analysis (praat-parselmouth)                 │
│  ├── Resonance analysis (librosa)                       │
│  ├── Data persistence (SQLite)                          │
│  ├── WebSocket server (IPC with Hammerspoon)            │
│  └── CLI interface (Typer + Rich)                       │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
Fern/
├── src/fern/                  # Python source
│   ├── __init__.py            # Package init, version
│   ├── cli.py                 # Typer CLI entry point
│   ├── capture.py             # Audio capture module
│   ├── analysis.py            # Pitch/resonance analysis
│   ├── db.py                  # SQLite interface
│   ├── models.py              # Dataclasses (Session, Reading, etc.)
│   ├── config.py              # Configuration management
│   └── websocket_server.py    # IPC between Python & Hammerspoon
├── hammerspoon/               # Lua GUI layer
│   ├── init.lua               # Main entry point, hotkeys
│   ├── overlay.lua            # Live display overlay
│   ├── charts.lua             # Historical chart rendering
│   └── chart_view.lua         # Full-screen chart with navigation
├── tests/                     # Test suite
│   ├── test_analysis.py       # Pitch/resonance tests
│   ├── test_cli.py            # CLI command tests
│   └── test_config.py         # Configuration tests
├── scripts/                   # Utility scripts
├── tools/                     # Development tools
├── install.sh                 # Installation script
├── pyproject.toml             # UV package configuration
├── README.md                  # This file
└── LICENSE                    # MIT License
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| CLI Framework | [Typer](https://typer.tiangolo.com/) + [Rich](https://rich.readthedocs.io/) |
| Audio Capture | [sounddevice](https://python-sounddevice.readthedocs.io/) |
| Pitch Analysis | [praat-parselmouth](https://parselmouth.readthedocs.io/) |
| Resonance Analysis | [librosa](https://librosa.org/) |
| Database | SQLite |
| GUI Layer | [Hammerspoon](https://www.hammerspoon.org/) (Lua) |
| Package Manager | [UV](https://docs.astral.sh/uv/) |

## Data Storage

Fern stores all data locally in `~/.fern/`:

```
~/.fern/
├── fern.db                    # SQLite database
│   ├── sessions               # Training sessions
│   ├── readings               # Individual pitch readings
│   └── targets                # Target pitch ranges
├── clips/                     # Rolling audio archive (30 most recent)
│   ├── clip_001.wav
│   ├── clip_002.wav
│   └── ...
└── archive/                   # Quarterly archives
    ├── clips-2025-Q1.zip
    └── clips-2025-Q2.zip
```

## Development

### Setup

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src

# Format code
uv run ruff format .

# Type check
uv run mypy src/
```

### Project Phases

See [Fern-Spec.md](Fern-Spec.md) for the complete technical specification and implementation roadmap.

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | Foundation - Project structure, basic pitch detection |
| Phase 2 | ✅ Complete | Data Layer - SQLite schema, models, audio storage |
| Phase 3 | ✅ Complete | Core Analysis - Audio capture, pitch/resonance analysis |
| Phase 4 | ✅ Complete | Hammerspoon Integration - WebSocket IPC, live overlay |
| Phase 5 | ✅ Complete | CLI Polish - Rich formatting, new commands, sparklines |
| Phase 6 | ✅ Complete | Charts - Historical trend visualization, keyboard navigation |
| Phase 7 | 🔨 In Progress | Installation & Packaging - Install script, documentation |
| Phase 8 | ⏳ Pending | v1.0 Polish - Error handling, logging, type hints |
| Phase 9 | ⏳ Pending | Guided Exercises - Structured practice sessions |

## Troubleshooting

### Fern CLI not found after installation

```bash
# Add to PATH (add to ~/.zshrc or ~/.bashrc)
export PATH="$HOME/.local/bin:$PATH"

# Or reinstall
cd fern
uv pip install -e .
```

### Hammerspoon overlay not showing

1. Reload Hammerspoon: `Ctrl+Cmd+R` or click menu bar icon → "Reload Config"
2. Check Console.app for Hammerspoon errors
3. Verify all Lua files are in `~/.hammerspoon/`

### No audio captured

1. Check microphone permissions in System Settings → Privacy & Security
2. Ensure no other app is using the microphone
3. Try a different audio device: `fern test --device 0`

### Charts show no data

```bash
# Send data to Hammerspoon
fern chart --send --days 30

# Then toggle chart view in Hammerspoon: Ctrl+Alt+Shift+C
```

## License

[MIT License](LICENSE)

## Repository

**GitHub**: [github.com/autumnsgrove/fern](https://github.com/autumnsgrove/fern)

**Related**: Works alongside [Hex](https://github.com/autumnsgrove/hex) dictation system
