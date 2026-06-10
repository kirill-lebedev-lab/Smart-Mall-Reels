import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = SCRIPTS_DIR.parent
FITTING_ROOM_IMAGES_DIR = PROJECT_ROOT / "images" / "fitting-room"
SCENES_DIR = PROJECT_ROOT / "scenes" / "visitor_attention"
OUTPUT_DIR = PROJECT_ROOT / "output" / "visitor_attention"

scripts_path = str(SCRIPTS_DIR)
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)
