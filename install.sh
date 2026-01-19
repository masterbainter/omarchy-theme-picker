#!/bin/bash
# Omarchy Theme Picker - Install Script

set -e

REPO_URL="https://github.com/masterbainter/omarchy-theme-picker.git"
DEFAULT_INSTALL_DIR="$HOME/.local/share/omarchy-theme-picker"
DESKTOP_ENTRY_DIR="$HOME/.local/share/applications"
HYPRLAND_BINDINGS="$HOME/.config/hypr/bindings.conf"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo ""
echo "=========================================="
echo "  Omarchy Theme Picker - Installer"
echo "=========================================="
echo ""

# Check dependencies
command -v python3 >/dev/null 2>&1 || error "Python 3 is required but not installed"
command -v git >/dev/null 2>&1 || error "Git is required but not installed"

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    error "Python 3.10+ is required (found $PYTHON_VERSION)"
fi
success "Python $PYTHON_VERSION detected"

# Check if Omarchy is installed
if [ ! -d "$HOME/.config/omarchy" ]; then
    warn "Omarchy not found at ~/.config/omarchy"
    warn "The theme picker requires Omarchy to be installed"
    echo ""
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo ""
    [[ $REPLY =~ ^[Yy]$ ]] || exit 1
fi

# Determine install location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if we're running from an existing clone
if [ -f "$SCRIPT_DIR/server.py" ] && [ -f "$SCRIPT_DIR/index.html" ]; then
    info "Running from existing installation at $SCRIPT_DIR"
    INSTALL_DIR="$SCRIPT_DIR"
else
    echo ""
    echo "Where would you like to install Omarchy Theme Picker?"
    echo "  Default: $DEFAULT_INSTALL_DIR"
    echo ""
    read -p "Install directory (press Enter for default): " USER_DIR
    INSTALL_DIR="${USER_DIR:-$DEFAULT_INSTALL_DIR}"

    # Expand ~ if used
    INSTALL_DIR="${INSTALL_DIR/#\~/$HOME}"

    if [ -d "$INSTALL_DIR" ] && [ -f "$INSTALL_DIR/server.py" ]; then
        info "Existing installation found at $INSTALL_DIR"
        read -p "Update existing installation? [Y/n] " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            exit 0
        fi
        cd "$INSTALL_DIR"
        git pull
    else
        info "Cloning repository to $INSTALL_DIR"
        git clone "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
fi

cd "$INSTALL_DIR"

# Create virtual environment
info "Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    success "Virtual environment created"
else
    success "Virtual environment already exists"
fi

# Install dependencies
info "Installing Python dependencies..."
source .venv/bin/activate
pip install -q -r requirements.txt
success "Dependencies installed"

# Setup desktop entry
info "Installing desktop entry..."
mkdir -p "$DESKTOP_ENTRY_DIR"

# Create desktop entry with correct path
cat > "$DESKTOP_ENTRY_DIR/omarchy-themes.desktop" << EOF
[Desktop Entry]
Name=Omarchy Themes
Comment=Browse and apply Omarchy themes
Exec=$INSTALL_DIR/launch.sh
Icon=preferences-desktop-theme
Terminal=false
Type=Application
Categories=Settings;DesktopSettings;
Keywords=theme;omarchy;appearance;
EOF

success "Desktop entry installed to $DESKTOP_ENTRY_DIR"

# Setup Hyprland keybinding
if [ -f "$HYPRLAND_BINDINGS" ]; then
    BINDING_LINE="bindd = SUPER, T, Theme Picker, exec, $INSTALL_DIR/launch.sh"

    if grep -q "omarchy-theme-picker\|omarchy-themes\|Theme Picker" "$HYPRLAND_BINDINGS" 2>/dev/null; then
        warn "Hyprland binding for theme picker already exists in $HYPRLAND_BINDINGS"
        echo "  You may want to update it manually to:"
        echo "  $BINDING_LINE"
    else
        echo ""
        read -p "Add SUPER+T keybinding to Hyprland? [Y/n] " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            # Backup existing config
            cp "$HYPRLAND_BINDINGS" "$HYPRLAND_BINDINGS.bak"

            # Add binding
            echo "" >> "$HYPRLAND_BINDINGS"
            echo "# Omarchy Theme Picker" >> "$HYPRLAND_BINDINGS"
            echo "$BINDING_LINE" >> "$HYPRLAND_BINDINGS"

            success "Hyprland keybinding added (backup: $HYPRLAND_BINDINGS.bak)"
            warn "Reload Hyprland config or press SUPER+SHIFT+C to apply"
        fi
    fi
elif [ -d "$HOME/.config/hypr" ]; then
    warn "Hyprland config directory exists but bindings.conf not found"
    echo "  To add the keybinding manually, add this line to your Hyprland config:"
    echo "  bindd = SUPER, T, Theme Picker, exec, $INSTALL_DIR/launch.sh"
else
    info "Hyprland not detected, skipping keybinding setup"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}  Installation Complete!${NC}"
echo "=========================================="
echo ""
echo "To run the theme picker:"
echo "  $INSTALL_DIR/run.sh"
echo ""
if [ -f "$HYPRLAND_BINDINGS" ]; then
    echo "Or press SUPER+T (after reloading Hyprland config)"
    echo ""
fi
echo "The server will start at http://127.0.0.1:8420"
echo ""
