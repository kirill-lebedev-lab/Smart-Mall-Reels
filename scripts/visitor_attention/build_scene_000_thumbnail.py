#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

try:
    from .paths import FITTING_ROOM_IMAGES_DIR, SCENES_DIR
    from .timeline import THUMBNAIL_DURATION
except ImportError:
    from paths import FITTING_ROOM_IMAGES_DIR, SCENES_DIR
    from timeline import THUMBNAIL_DURATION


DEFAULT_INPUT = FITTING_ROOM_IMAGES_DIR / "003-003-3.png"
DEFAULT_OUTPUT = SCENES_DIR / "scene_000_thumbnail.mp4"

FPS = 30
FRAME_COUNT = round(THUMBNAIL_DURATION * FPS)
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
VIDEO_CODEC = "libx264"
PRESET = "slow"
CRF = "18"
PIXEL_FORMAT = "yuv420p"

FONT_FAMILY = "Avenir Next Medium"
TEXT = "Smart Mirror\nGets Attention"
FONT_SIZE = 96
TEXT_COLOR = "0xFFF6DC"
SHADOW_COLOR = "0x000000"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the static Visitor Attention thumbnail scene."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to the final thumbnail image.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to the generated thumbnail scene.",
    )
    return parser.parse_args()


def build_filtergraph() -> str:
    return (
        f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:"
        f"force_original_aspect_ratio=increase,"
        f"crop={OUTPUT_WIDTH}:{OUTPUT_HEIGHT},"
        f"setsar=1,"
        f"drawtext="
        f"font='{FONT_FAMILY}':"
        f"text='{TEXT}':"
        f"fontsize={FONT_SIZE}:"
        f"fontcolor={TEXT_COLOR}:"
        f"x=(w-text_w)/2:"
        f"y=h*0.12:"
        f"bordercolor={SHADOW_COLOR}@0.22:"
        f"borderw=1:"
        f"shadowcolor={SHADOW_COLOR}@0.42:"
        f"shadowx=0:"
        f"shadowy=3,"
        f"format={PIXEL_FORMAT}"
    )


def main() -> int:
    args = parse_args()
    input_path = args.input
    output_path = args.output

    if not input_path.is_file():
        print(f"Input image not found: {input_path}", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-framerate",
        str(FPS),
        "-i",
        str(input_path),
        "-vf",
        build_filtergraph(),
        "-frames:v",
        str(FRAME_COUNT),
        "-an",
        "-c:v",
        VIDEO_CODEC,
        "-preset",
        PRESET,
        "-crf",
        CRF,
        "-pix_fmt",
        PIXEL_FORMAT,
        str(output_path),
    ]

    print("Rendering static thumbnail scene...")
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print("ffmpeg was not found. Please install ffmpeg and try again.", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as error:
        print(f"ffmpeg failed with exit code {error.returncode}.", file=sys.stderr)
        return error.returncode

    print(f"Thumbnail scene created: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
