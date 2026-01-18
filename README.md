# Omarchy Theme Picker

A web-based theme picker for [Omarchy](https://github.com/omacom-io/omarchy) - browse, preview, and install themes with a single click.

## Screenshots

### Installed Themes
![Installed Themes](screenshots/01-installed-themes.png)

### Available Themes (One-Click Install)
![Available Themes](screenshots/02-available-themes.png)

### Installation Progress Modal
![Install Modal](screenshots/06-install-modal.png)

### Search & Filter
![Search](screenshots/05-search.png)

### Light Theme Filter
![Light Themes](screenshots/04-light-themes.png)

## Features

- **Visual Theme Browser** - Grid view of all installed and available themes with preview images
- **One-Click Install** - Install themes directly from the official Omarchy theme gallery
- **One-Click Apply** - Switch between installed themes instantly
- **Dark/Light Filter** - Filter themes by mode
- **Search** - Find themes by name
- **Optimized Previews** - Preview images are cached locally as WebP for fast loading (~98% size reduction)
- **Installation Progress** - Modal showing step-by-step installation status
- **Back to Top** - Slick progress-ring button with glassmorphism design

## Installation

```bash
# Clone the repository
git clone https://github.com/masterbainter/omarchy-theme-picker.git
cd omarchy-theme-picker

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py
```

Then open http://127.0.0.1:8420 in your browser.

## Desktop Integration (Hyprland)

To launch as a borderless webapp with a keyboard shortcut:

1. Copy the desktop entry:
```bash
cp omarchy-themes.desktop ~/.local/share/applications/
# Edit the Exec path to point to your installation
```

2. Add to your Hyprland config (`~/.config/hypr/bindings.conf`):
```
bindd = SUPER, T, Theme Picker, exec, /path/to/omarchy-theme-picker/launch.sh
```

## Requirements

- Python 3.10+
- Omarchy installed at `~/.config/omarchy`
- `omarchy-theme-set` and `omarchy-theme-install` in PATH

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/themes` | GET | List installed themes |
| `/api/available` | GET | List available themes from official sources |
| `/api/themes/apply` | POST | Apply an installed theme |
| `/api/themes/install` | POST | Install a theme from GitHub |
| `/api/themes/{name}/preview` | GET | Get theme preview image |
| `/api/sync-previews` | POST | Cache all preview images locally |

## Port Handling

The server automatically finds a free port starting from 8420. If that port is in use, it increments until it finds an available one. The active port is written to `.port` for the launch script to read.

## License

MIT
