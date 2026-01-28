#!/usr/bin/env python3
"""Omarchy Theme Picker - Web interface for selecting themes."""

import subprocess
import re
import asyncio
import io
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
import httpx
from PIL import Image


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup: cache installed theme previews in background
    asyncio.create_task(auto_cache_installed())
    yield
    # Shutdown: nothing to clean up


app = FastAPI(title="Omarchy Theme Picker", lifespan=lifespan)

THEMES_DIR = Path.home() / ".config/omarchy/themes"
CURRENT_THEME_LINK = Path.home() / ".config/omarchy/current/theme"
OMARCHY_THEME_INSTALL = Path.home() / ".local/share/omarchy/bin/omarchy-theme-install"
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Sync state
sync_in_progress = False
installed_cache_in_progress = False

# Preview image settings
PREVIEW_MAX_WIDTH = 640
PREVIEW_QUALITY = 80

# Light themes (everything else is dark)
LIGHT_THEMES = {
    "catppuccin-latte",
    "flexoki-light",
    "milkmatcha-light",
    "snow",
    "snow_black",
    "solarized-light",
    "whitegold",
    "frost",
    "bliss",
}

# Official theme repos from https://learn.omacom.io/2/the-omarchy-manual/90/extra-themes
OFFICIAL_THEMES = {
    "amberbyte": "https://github.com/tahfizhabib/omarchy-amberbyte-theme",
    "arc-blueberry": "https://github.com/vale-c/omarchy-arc-blueberry",
    "archwave": "https://github.com/davidguttman/archwave",
    "ash": "https://github.com/bjarneo/omarchy-ash-theme",
    "artzen": "https://github.com/tahfizhabib/omarchy-artzen-theme",
    "aura": "https://github.com/bjarneo/omarchy-aura-theme",
    "all-hallows-eve": "https://github.com/guilhermetk/omarchy-all-hallows-eve-theme",
    "ayaka": "https://github.com/abhijeet-swami/omarchy-ayaka-theme",
    "azure-glow": "https://github.com/Hydradevx/omarchy-azure-glow-theme",
    "bauhaus": "https://github.com/somerocketeer/omarchy-bauhaus-theme",
    "black_arch": "https://github.com/ankur311sudo/black_arch",
    "blackgold": "https://github.com/HANCORE-linux/omarchy-blackgold-theme",
    "blackturq": "https://github.com/HANCORE-linux/omarchy-blackturq-theme",
    "bliss": "https://github.com/mishonki3/omarchy-bliss-theme",
    "bluedotrb": "https://github.com/dotsilva/omarchy-bluedotrb-theme",
    "blueridge-dark": "https://github.com/hipsterusername/omarchy-blueridge-dark-theme",
    "catppuccin-dark": "https://github.com/Luquatic/omarchy-catppuccin-dark",
    "citrus-cynapse": "https://github.com/Grey-007/citrus-cynapse",
    "cobalt2": "https://github.com/hoblin/omarchy-cobalt2-theme",
    "darcula": "https://github.com/noahljungberg/omarchy-darcula-theme",
    "demon": "https://github.com/HANCORE-linux/omarchy-demon-theme",
    "dotrb": "https://github.com/dotsilva/omarchy-dotrb-theme",
    "drac": "https://github.com/ShehabShaef/omarchy-drac-theme",
    "dracula": "https://github.com/catlee/omarchy-dracula-theme",
    "eldritch": "https://github.com/eldritch-theme/omarchy",
    "evergarden": "https://github.com/celsobenedetti/omarchy-evergarden",
    "felix": "https://github.com/TyRichards/omarchy-felix-theme",
    "fireside": "https://github.com/bjarneo/omarchy-fireside-theme",
    "flexoki-dark": "https://github.com/euandeas/omarchy-flexoki-dark-theme",
    "forest-green": "https://github.com/abhijeet-swami/omarchy-forest-green-theme",
    "frost": "https://github.com/bjarneo/omarchy-frost-theme",
    "futurism": "https://github.com/bjarneo/omarchy-futurism-theme",
    "gold-rush": "https://github.com/tahayvr/omarchy-gold-rush-theme",
    "thegreek": "https://github.com/HANCORE-linux/omarchy-thegreek-theme",
    "green-garden": "https://github.com/kalk-ak/omarchy-green-garden-theme",
    "gruvu": "https://github.com/ankur311sudo/gruvu",
    "infernium-dark": "https://github.com/RiO7MAKK3R/omarchy-infernium-dark-theme",
    "mapquest": "https://github.com/ItsABigIgloo/omarchy-mapquest-theme",
    "mars": "https://github.com/steve-lohmeyer/omarchy-mars-theme",
    "mechanoonna": "https://github.com/HANCORE-linux/omarchy-mechanoonna-theme",
    "miasma": "https://github.com/OldJobobo/omarchy-miasma-theme",
    "midnight": "https://github.com/JaxonWright/omarchy-midnight-theme",
    "milkmatcha-light": "https://github.com/hipsterusername/omarchy-milkmatcha-light-theme",
    "monochrome": "https://github.com/Swarnim114/omarchy-monochrome-theme",
    "monokai": "https://github.com/bjarneo/omarchy-monokai-theme",
    "nagai-poolside": "https://github.com/somerocketeer/omarchy-nagai-poolside-theme",
    "neo-sploosh": "https://github.com/monoooki/omarchy-neo-sploosh-theme",
    "neovoid": "https://github.com/RiO7MAKK3R/omarchy-neovoid-theme",
    "nes": "https://github.com/bjarneo/omarchy-nes-theme",
    "omacarchy": "https://github.com/RiO7MAKK3R/omarchy-omacarchy-theme",
    "one-dark-pro": "https://github.com/sc0ttman/omarchy-one-dark-pro-theme",
    "pandora": "https://github.com/imbypass/omarchy-pandora-theme",
    "pina": "https://github.com/bjarneo/omarchy-pina-theme",
    "pink-blood-omarchy": "https://github.com/ITSZXY/pink-blood-omarchy-theme",
    "pulsar": "https://github.com/bjarneo/omarchy-pulsar-theme",
    "purple-moon": "https://github.com/Grey-007/purple-moon",
    "purplewave": "https://github.com/dotsilva/omarchy-purplewave-theme",
    "rainynight": "https://github.com/atif-1402/omarchy-rainynight-theme",
    "retropc": "https://github.com/rondilley/omarchy-retropc-theme",
    "rose-pine-dark": "https://github.com/guilhermetk/omarchy-rose-pine-dark",
    "roseofdune": "https://github.com/HANCORE-linux/omarchy-roseofdune-theme",
    "sakura": "https://github.com/bjarneo/omarchy-sakura-theme",
    "sapphire": "https://github.com/HANCORE-linux/omarchy-sapphire-theme",
    "shadesofjade": "https://github.com/HANCORE-linux/omarchy-shadesofjade-theme",
    "space-monkey": "https://github.com/TyRichards/omarchy-space-monkey-theme",
    "snow": "https://github.com/bjarneo/omarchy-snow-theme",
    "solarized": "https://github.com/Gazler/omarchy-solarized-theme",
    "solarized-light": "https://github.com/dfrico/omarchy-solarized-light-theme",
    "solarizedosaka": "https://github.com/motorsss/omarchy-solarizedosaka-theme",
    "sunset": "https://github.com/rondilley/omarchy-sunset-theme",
    "sunset-drive": "https://github.com/tahayvr/omarchy-sunset-drive-theme",
    "super-game-bro": "https://github.com/TyRichards/omarchy-super-game-bro-theme",
    "synthwave84": "https://github.com/omacom-io/omarchy-synthwave84-theme",
    "temerald": "https://github.com/Ahmad-Mtr/omarchy-temerald-theme",
    "tokyoled": "https://github.com/Justin-De-Sio/omarchy-tokyoled-theme",
    "tycho": "https://github.com/leonardobetti/omarchy-tycho",
    "waveform-dark": "https://github.com/hipsterusername/omarchy-waveform-dark-theme",
    "whitegold": "https://github.com/HANCORE-linux/omarchy-whitegold-theme",
    "van-gogh": "https://github.com/Nirmal314/omarchy-van-gogh-theme",
    "vesper": "https://github.com/thmoee/omarchy-vesper-theme",
    "vhs80": "https://github.com/tahayvr/omarchy-vhs80-theme",
    "void": "https://github.com/vyrx-dev/omarchy-void-theme",
}

# Preview file names to check, in priority order
PREVIEW_NAMES = [
    "preview.png",
    "theme.png",
    "screenshot.png",
    "preview-1.png",
    "preview1.png",
    "preview_1.png",
]


class ThemeRequest(BaseModel):
    name: str


class InstallRequest(BaseModel):
    name: str
    url: str | None = None


def find_preview(theme_dir: Path) -> Path | None:
    """Find a preview image in the theme directory."""
    # Check known preview names first
    for name in PREVIEW_NAMES:
        preview = theme_dir / name
        if preview.exists():
            return preview

    # Fall back to any png/jpg in the root (not in subdirs like backgrounds)
    for ext in ["*.png", "*.jpg", "*.jpeg"]:
        matches = list(theme_dir.glob(ext))
        # Filter out common non-preview files
        for match in matches:
            if match.name not in ["logo.png", "icon.png"]:
                return match

    # Last resort: use first background image
    backgrounds_dir = theme_dir / "backgrounds"
    if backgrounds_dir.exists():
        for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
            matches = sorted(backgrounds_dir.glob(ext))
            if matches:
                return matches[0]

    return None


def get_current_theme() -> str:
    """Get the currently active theme name."""
    try:
        if CURRENT_THEME_LINK.is_symlink():
            return CURRENT_THEME_LINK.resolve().name
    except Exception:
        pass
    return ""


def get_theme_mode(name: str) -> str:
    """Determine if a theme is light or dark."""
    name_lower = name.lower()
    if name in LIGHT_THEMES or "light" in name_lower:
        return "light"
    return "dark"


def get_themes() -> list[dict]:
    """Get list of all available themes with metadata."""
    themes = []
    current = get_current_theme()

    for theme_dir in sorted(THEMES_DIR.iterdir()):
        if not theme_dir.is_dir():
            continue

        name = theme_dir.name
        preview = find_preview(theme_dir)
        cached = has_cached_preview(name, installed=True)

        themes.append({
            "name": name,
            "has_preview": preview is not None,
            "is_current": name == current,
            "mode": get_theme_mode(name),
            "cached": cached,
        })

    return themes


@app.get("/api/themes")
def list_themes():
    """List all available themes."""
    return {
        "themes": get_themes(),
        "current": get_current_theme(),
    }


def patch_hyprland_conf():
    """Patch deprecated Hyprland syntax in the current theme's hyprland.conf.

    Fixes compatibility with Hyprland 0.53+:
    - windowrulev2 -> windowrule
    - Comma-separated fields -> space-separated
    - Strip ^()$ regex anchors from class: and title: values
    """
    conf = Path.home() / ".config/omarchy/current/theme/hyprland.conf"
    if not conf.exists():
        return

    text = conf.read_text()
    lines = text.splitlines()
    new_lines = []
    changed = False

    for line in lines:
        stripped = line.strip()
        # Match windowrule or windowrulev2 lines
        m = re.match(r'^(windowrulev?2?)\s*=\s*(.+)$', stripped)
        if m:
            keyword, rest = m.groups()
            if keyword == 'windowrulev2':
                keyword = 'windowrule'
                changed = True
            # Split on commas, strip each field
            fields = [f.strip() for f in rest.split(',')]
            # Strip ^()$ anchors from class: and title: values
            cleaned = []
            for f in fields:
                new_f = re.sub(r'((?:class|title):)\^\((.+?)\)\$', r'\1\2', f)
                if new_f != f:
                    changed = True
                cleaned.append(new_f)
            new_line = f'{keyword} = {" ".join(cleaned)}'
            if new_line != stripped:
                changed = True
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    if changed:
        conf.write_text('\n'.join(new_lines) + '\n')


@app.post("/api/themes/apply")
def apply_theme(request: ThemeRequest):
    """Apply a theme by name."""
    theme_dir = THEMES_DIR / request.name

    if not theme_dir.exists():
        raise HTTPException(status_code=404, detail=f"Theme '{request.name}' not found")

    try:
        result = subprocess.run(
            [str(Path.home() / ".local/share/omarchy/bin/omarchy-theme-set"), request.name],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to apply theme: {result.stderr}"
            )

        patch_hyprland_conf()

        return {
            "success": True,
            "message": f"Theme '{request.name}' applied successfully",
            "current": request.name,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Theme application timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_github_preview_url(repo_url: str) -> str | None:
    """Convert GitHub repo URL to raw preview.png URL."""
    match = re.match(r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$', repo_url)
    if match:
        owner, repo = match.groups()
        return f"https://raw.githubusercontent.com/{owner}/{repo}/main/preview.png"
    return None


def get_cached_preview_path(theme_name: str, installed: bool = False) -> Path:
    """Get the path to a cached preview image."""
    prefix = "installed_" if installed else ""
    return CACHE_DIR / f"{prefix}{theme_name}.webp"


def has_cached_preview(theme_name: str, installed: bool = False) -> bool:
    """Check if a theme has a cached preview."""
    return get_cached_preview_path(theme_name, installed).exists()


def cache_installed_preview(theme_name: str) -> bool:
    """Cache an installed theme's preview as optimized WebP."""
    theme_dir = THEMES_DIR / theme_name
    if not theme_dir.exists():
        return False

    source = find_preview(theme_dir)
    if not source:
        return False

    cache_path = get_cached_preview_path(theme_name, installed=True)

    try:
        img = Image.open(source)

        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Resize if too large
        if img.width > PREVIEW_MAX_WIDTH:
            ratio = PREVIEW_MAX_WIDTH / img.width
            new_size = (PREVIEW_MAX_WIDTH, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Save as optimized WebP
        img.save(cache_path, 'WEBP', quality=PREVIEW_QUALITY, method=6)
        return True
    except Exception:
        return False


def cache_all_installed_previews() -> dict:
    """Cache all installed theme previews."""
    results = {"success": 0, "failed": 0, "skipped": 0}

    for theme_dir in THEMES_DIR.iterdir():
        if not theme_dir.is_dir():
            continue

        name = theme_dir.name

        # Skip if already cached
        if has_cached_preview(name, installed=True):
            results["skipped"] += 1
            continue

        if cache_installed_preview(name):
            results["success"] += 1
        else:
            results["failed"] += 1

    return results


async def auto_cache_installed():
    """Background task to cache installed themes on startup."""
    global installed_cache_in_progress
    if installed_cache_in_progress:
        return

    installed_cache_in_progress = True
    try:
        # Small delay to let server fully start
        await asyncio.sleep(1)
        cache_all_installed_previews()
    finally:
        installed_cache_in_progress = False


async def download_and_cache_preview(theme_name: str, repo_url: str) -> bool:
    """Download a preview image and cache it as optimized WebP."""
    cache_path = get_cached_preview_path(theme_name)

    # Extract owner/repo from URL
    match = re.match(r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$', repo_url)
    if not match:
        return False
    owner, repo = match.groups()
    base = f"https://raw.githubusercontent.com/{owner}/{repo}"

    # Try many possible preview filenames and branches
    filenames = [
        "preview.png", "preview.jpg", "preview.jpeg",
        "theme.png", "theme.jpg",
        "screenshot.png", "screenshot.jpg",
        "preview-1.png", "preview1.png",
    ]
    branches = ["main", "master"]

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        # First try standard preview files
        for branch in branches:
            for filename in filenames:
                try:
                    url = f"{base}/{branch}/{filename}"
                    response = await client.get(url)
                    if response.status_code == 200 and len(response.content) > 1000:
                        if await save_optimized_image(response.content, cache_path):
                            return True
                except Exception:
                    continue

        # If no preview found, try to get first image from backgrounds folder via API
        for branch in branches:
            try:
                api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/backgrounds?ref={branch}"
                response = await client.get(api_url)
                if response.status_code == 200:
                    files = response.json()
                    # Find first image file
                    for f in files:
                        name = f.get("name", "").lower()
                        if name.endswith((".png", ".jpg", ".jpeg", ".webp")):
                            img_url = f"{base}/{branch}/backgrounds/{f['name']}"
                            img_response = await client.get(img_url)
                            if img_response.status_code == 200 and len(img_response.content) > 1000:
                                if await save_optimized_image(img_response.content, cache_path):
                                    return True
                            break  # Only try first image
            except Exception:
                continue

    return False


async def save_optimized_image(content: bytes, cache_path: Path) -> bool:
    """Save image content as optimized WebP."""
    try:
        img = Image.open(io.BytesIO(content))

        # Convert to RGB if necessary (for WebP compatibility)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Resize if too large
        if img.width > PREVIEW_MAX_WIDTH:
            ratio = PREVIEW_MAX_WIDTH / img.width
            new_size = (PREVIEW_MAX_WIDTH, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Save as optimized WebP
        img.save(cache_path, 'WEBP', quality=PREVIEW_QUALITY, method=6)
        return True
    except Exception:
        return False


async def sync_all_previews(force: bool = False):
    """Sync all available theme previews to cache."""
    global sync_in_progress
    if sync_in_progress:
        return {"status": "already running"}

    sync_in_progress = True
    results = {"success": 0, "failed": 0, "skipped": 0}

    try:
        installed = {d.name for d in THEMES_DIR.iterdir() if d.is_dir()}

        for name, url in OFFICIAL_THEMES.items():
            if name in installed:
                results["skipped"] += 1
                continue

            if has_cached_preview(name) and not force:
                results["skipped"] += 1
                continue

            success = await download_and_cache_preview(name, url)
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
    finally:
        sync_in_progress = False

    return results


@app.get("/api/available")
def list_available():
    """List themes available to install from official sources."""
    installed = {d.name for d in THEMES_DIR.iterdir() if d.is_dir()}
    available = []

    for name, url in sorted(OFFICIAL_THEMES.items()):
        if name not in installed:
            # Use cached preview if available, otherwise GitHub URL
            if has_cached_preview(name):
                preview_url = f"/api/cache/{name}/preview"
            else:
                preview_url = get_github_preview_url(url)

            available.append({
                "name": name,
                "url": url,
                "mode": get_theme_mode(name),
                "preview_url": preview_url,
                "cached": has_cached_preview(name),
            })

    return {"available": available, "count": len(available)}


@app.get("/api/cache/{theme_name}/preview")
def get_cached_preview(theme_name: str):
    """Serve a cached preview image."""
    cache_path = get_cached_preview_path(theme_name)
    if not cache_path.exists():
        raise HTTPException(status_code=404, detail="Cached preview not found")
    return FileResponse(cache_path, media_type="image/webp")


@app.post("/api/cache-installed")
def trigger_installed_cache():
    """Cache all installed theme previews."""
    results = cache_all_installed_previews()
    return {"status": "complete", "results": results}


@app.post("/api/sync-previews")
async def trigger_sync(background_tasks: BackgroundTasks, force: bool = False):
    """Trigger a background sync of all theme previews (installed + available)."""
    if sync_in_progress:
        return {"status": "already running"}

    # First cache installed themes (fast, synchronous)
    installed_results = cache_all_installed_previews()

    # Then sync available themes in background
    background_tasks.add_task(sync_all_previews, force)
    return {
        "status": "started",
        "force": force,
        "installed_cached": installed_results,
    }


@app.post("/api/themes/install")
def install_theme(request: InstallRequest):
    """Install a theme from GitHub."""
    url = request.url or OFFICIAL_THEMES.get(request.name)

    if not url:
        raise HTTPException(status_code=400, detail=f"No URL for theme '{request.name}'")

    try:
        # Use omarchy-theme-install which clones and applies the theme
        result = subprocess.run(
            [str(OMARCHY_THEME_INSTALL), url],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to install theme: {result.stderr}"
            )

        return {
            "success": True,
            "message": f"Theme '{request.name}' installed and applied",
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Theme installation timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/themes/{theme_name}")
def delete_theme(theme_name: str):
    """Delete an installed theme."""
    theme_dir = THEMES_DIR / theme_name

    if not theme_dir.exists():
        raise HTTPException(status_code=404, detail=f"Theme '{theme_name}' not found")

    # Don't delete current theme
    if theme_name == get_current_theme():
        raise HTTPException(status_code=400, detail="Cannot delete the currently active theme")

    import shutil
    shutil.rmtree(theme_dir)

    return {"success": True, "message": f"Theme '{theme_name}' deleted"}


@app.get("/api/themes/{theme_name}/preview")
def get_theme_preview(theme_name: str):
    """Get the preview image for a theme (cached if available)."""
    # Serve cached version if available
    cache_path = get_cached_preview_path(theme_name, installed=True)
    if cache_path.exists():
        return FileResponse(cache_path, media_type="image/webp")

    # Fall back to original
    theme_dir = THEMES_DIR / theme_name
    if not theme_dir.exists():
        raise HTTPException(status_code=404, detail="Theme not found")

    preview_path = find_preview(theme_dir)
    if not preview_path:
        raise HTTPException(status_code=404, detail="Preview not found")

    # Determine media type
    suffix = preview_path.suffix.lower()
    media_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(suffix, "image/png")

    return FileResponse(preview_path, media_type=media_type)


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the main page."""
    return Path(__file__).parent.joinpath("index.html").read_text()


def find_free_port(start_port: int = 8420, max_attempts: int = 100) -> int:
    """Find a free port starting from start_port."""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No free port found in range {start_port}-{start_port + max_attempts}")


if __name__ == "__main__":
    import uvicorn

    port = find_free_port()
    port_file = Path(__file__).parent / ".port"
    port_file.write_text(str(port))

    print(f"Starting server on http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port)
