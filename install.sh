#!/bin/bash
set -e

# Fern Installation Script
# Installs Fern CLI and Hammerspoon configuration

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Banner
echo ""
echo "🌿 Fern Installation Script"
echo "=========================="
echo ""

# Check prerequisites
log_info "Checking prerequisites..."

# Check macOS
if [[ "$(uname)" != "Darwin" ]]; then
    log_warn "Fern is designed for macOS (Hammerspoon integration)."
    log_warn "The Python CLI will work, but the GUI layer requires macOS."
fi

# Check Python version
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PY_MAJOR=$(echo $PY_VERSION | cut -d. -f1)
    PY_MINOR=$(echo $PY_VERSION | cut -d. -f2)
    if [[ "$PY_MAJOR" -lt 3 ]] || [[ "$PY_MAJOR" -eq 3 && "$PY_MINOR" -lt 11 ]]; then
        log_error "Python 3.11+ required. Found: $PY_VERSION"
        exit 1
    fi
    log_success "Python $PY_VERSION found"
else
    log_error "Python 3.11+ not found. Please install Python first."
    exit 1
fi

# Check UV
if ! command -v uv &> /dev/null; then
    log_info "Installing UV package manager..."
    curl -Ls https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v uv &> /dev/null; then
        log_error "Failed to install UV. Please install manually: https://docs.astral.sh/uv/"
        exit 1
    fi
fi
log_success "UV package manager found"

# Check Hammerspoon
if ! command -v hs &> /dev/null; then
    log_info "Hammerspoon not found. Installing via Homebrew..."
    if ! command -v brew &> /dev/null; then
        log_error "Homebrew not found. Please install Homebrew first: https://brew.sh"
        exit 1
    fi
    brew install hammerspoon
    log_success "Hammerspoon installed"
else
    log_success "Hammerspoon found"
fi

# Determine Fern directory
if [[ -z "${FERN_DIR:-}" ]]; then
    FERN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi
log_info "Fern directory: $FERN_DIR"

# Create Python virtual environment
log_info "Setting up Python environment..."
cd "$FERN_DIR"
uv sync

# Install Fern in editable mode
log_info "Installing Fern CLI..."
uv pip install -e .

# Verify installation
if ! command -v fern &> /dev/null; then
    log_error "Fern CLI installation failed"
    exit 1
fi
log_success "Fern CLI installed ($(fern --version 2>&1 || echo 'unknown version')"

# Setup Hammerspoon configuration
log_info "Setting up Hammerspoon configuration..."
HOMESPOON_DIR="$HOME/.hammerspoon"
mkdir -p "$HOMESPOON_DIR"

# Create main Fern module
FERN_LUA="$HOMESPOON_DIR/fern.lua"
if [[ -f "$FERN_LUA" ]]; then
    log_warn "Existing fern.lua found. Backing up to fern.lua.backup"
    cp "$FERN_LUA" "$FERN_LUA.backup"
fi

# Copy Fern Lua modules
cp "$FERN_DIR/hammerspoon/init.lua" "$HOMESPOON_DIR/fern.lua"
if [[ -f "$FERN_DIR/hammerspoon/overlay.lua" ]]; then
    cp "$FERN_DIR/hammerspoon/overlay.lua" "$HOMESPOON_DIR/"
fi
if [[ -f "$FERN_DIR/hammerspoon/charts.lua" ]]; then
    cp "$FERN_DIR/hammerspoon/charts.lua" "$HOMESPOON_DIR/"
fi
if [[ -f "$FERN_DIR/hammerspoon/chart_view.lua" ]]; then
    cp "$FERN_DIR/hammerspoon/chart_view.lua" "$HOMESPOON_DIR/"
fi

log_success "Hammerspoon modules copied to $HOMESPOON_DIR"

# Update init.lua to load Fern
INIT_LUA="$HOMESPOON_DIR/init.lua"
if [[ ! -f "$INIT_LUA" ]]; then
    touch "$INIT_LUA"
fi

# Check if Fern is already loaded
if grep -q 'require.*"fern"' "$INIT_LUA" 2>/dev/null; then
    log_info "Fern already loaded in init.lua"
else
    echo '' >> "$INIT_LUA"
    echo '-- Fern voice training feedback companion' >> "$INIT_LUA"
    echo 'require("fern")' >> "$INIT_LUA"
    log_success "Added Fern to init.lua"
fi

# Create data directory
DATA_DIR="$HOME/.fern"
mkdir -p "$DATA_DIR/clips"
mkdir -p "$DATA_DIR/archive"
log_success "Data directory created at $DATA_DIR"

# Summary
echo ""
echo "=========================="
echo "🌿 Installation Complete!"
echo "=========================="
echo ""
echo "Next steps:"
echo ""
echo "1. Reload Hammerspoon configuration:"
echo "   - Click the Hammerspoon icon in your menu bar"
echo "   - Select 'Reload Config' (or press Ctrl+Cmd+R)"
echo ""
echo "2. Verify Fern is working:"
echo "   - Open Terminal and run: fern status"
echo ""
echo "3. Test the overlay:"
echo "   - Press Ctrl+Alt+Shift+F to start capture"
echo "   - Speak into your microphone"
echo "   - Press Ctrl+Alt+Shift+S to stop"
echo ""
echo "4. View charts:"
echo "   - Press Ctrl+Alt+Shift+C to toggle chart view"
echo "   - Press H for keyboard shortcuts"
echo ""
echo "Useful commands:"
echo "   fern status      - Show current status"
echo "   fern trend       - View pitch trends"
echo "   fern sessions    - List recent sessions"
echo "   fern chart --send  - Send data to Hammerspoon charts"
echo ""
echo "For more information, see README.md"
echo ""
