"""Central path resolution. All file access goes through these so the app
never depends on the machine-specific working directory."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
APP_DATA_DIR = ROOT / "app_data"
ASSETS_DIR = ROOT / "assets"

USER_STATE_FILE = APP_DATA_DIR / "user_state.json"
