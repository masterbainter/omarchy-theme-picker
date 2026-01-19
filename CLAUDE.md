# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Omarchy Theme Picker is a web-based theme manager for [Omarchy](https://github.com/omacom-io/omarchy). It provides a visual interface to browse, preview, install, and apply themes.

## Tech Stack

- **Backend**: Python 3.10+ with FastAPI and Uvicorn
- **Frontend**: Single-file HTML/CSS/JS (no framework)
- **Image Processing**: Pillow for WebP optimization
- **HTTP Client**: httpx for async GitHub API calls
- **Testing**: Playwright for screenshot generation

## Commands

```bash
# Full installation (venv, deps, desktop entry, Hyprland keybinding)
./install.sh

# Run the development server
./run.sh

# Or manually:
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py

# Generate screenshots (requires npm install first)
npm install
node screenshots.js
```

The server automatically finds a free port starting from 8420 and writes it to `.port`.

## Architecture

### Backend (server.py)

Single-file FastAPI application with these key components:

- **Lifespan handler** (lines 18-24): Caches installed theme previews on startup via background task
- **Theme detection** (lines 162-186): Searches for preview images in priority order (preview.png, theme.png, etc.)
- **Image caching** (lines 293-438): Converts previews to optimized WebP (640px max width, quality 80)
- **GitHub integration** (lines 363-416): Downloads preview images from official theme repos, trying multiple filename patterns and branches

### Key Data Structures

- `OFFICIAL_THEMES` (lines 57-140): Dict mapping theme names to GitHub repo URLs (~90 themes)
- `LIGHT_THEMES` (lines 44-54): Set of theme names classified as light mode
- `PREVIEW_NAMES` (lines 143-150): Priority list of preview filename patterns

### File Paths

- Themes directory: `~/.config/omarchy/themes`
- Current theme symlink: `~/.config/omarchy/current/theme`
- Theme installer: `~/.local/share/omarchy/bin/omarchy-theme-install`
- Preview cache: `./cache/` (WebP files, prefixed with `installed_` for local themes)

### Frontend (index.html)

Self-contained SPA with inline CSS and JavaScript. Key features:
- Grid-based theme card layout
- Tab switching between installed/available themes
- Mode filtering (all/light/dark)
- Search functionality
- Installation progress modal with step-by-step status

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/themes` | GET | List installed themes |
| `/api/available` | GET | List available themes from official sources |
| `/api/themes/apply` | POST | Apply an installed theme |
| `/api/themes/install` | POST | Install a theme from GitHub |
| `/api/themes/{name}/preview` | GET | Get theme preview image |
| `/api/sync-previews` | POST | Cache all preview images locally |

## External Dependencies

The app relies on Omarchy being installed:
- `omarchy-theme-set` - CLI command to apply themes
- `omarchy-theme-install` - CLI command to install themes from GitHub
