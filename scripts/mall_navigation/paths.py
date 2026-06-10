import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SCRIPTS_DIR.parent
NAVIGATION_IMAGES_DIR = PROJECT_ROOT / "images" / "navigation"
SCENES_DIR = PROJECT_ROOT / "scenes" / "mall_navigation"
OUTPUT_DIR = PROJECT_ROOT / "output" / "mall_navigation"
AUDIO_DIR = PROJECT_ROOT / "audio"

scripts_path = str(SCRIPTS_DIR)
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)
