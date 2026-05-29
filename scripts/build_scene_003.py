#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image


# Scene timing and output format.
DURATION = 4.0
FPS = 30
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920

# Motion tuning.
# Do not stretch the source image. Scale to cover the vertical frame, then crop.
ZOOM_START = 1.12
ZOOM_END = 1.0
BASE_SCALE_HEIGHT = OUTPUT_HEIGHT
VIEWPORT_X_START = 725
VIEWPORT_X_END = 775
VIEWPORT_Y_FOCUS = 0.5

# Encoding settings.
VIDEO_CODEC = "libx264"
PIXEL_FORMAT = "yuv420p"
CRF = "18"
PRESET = "slow"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "images" / "navigation" / "001-008.png"
DEFAULT_OUTPUT = PROJECT_ROOT / "scenes" / "scene_003.mp4"


def smoothstep(progress: float) -> float:
    """Return a calm 0..1 easing value for premium camera motion."""
    return progress * progress * (3 - 2 * progress)


def frame_count() -> int:
    return int(round(DURATION * FPS))


def build_ffmpeg_command(output_path: Path) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{OUTPUT_WIDTH}x{OUTPUT_HEIGHT}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-frames:v",
        str(frame_count()),
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


def render_frame(source: Image.Image, index: int, total_frames: int) -> Image.Image:
    """Render one undistorted 9:16 frame showing screen-to-visitor adaptation."""
    progress = 0 if total_frames == 1 else index / (total_frames - 1)
    eased = smoothstep(progress)
    zoom = ZOOM_START + (ZOOM_END - ZOOM_START) * eased

    scaled_height = round(BASE_SCALE_HEIGHT * zoom)
    scaled_width = round(source.width * scaled_height / source.height)
    scaled = source.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

    # The camera starts on the responsive screen, then pulls back to reveal the visitor.
    x = round(VIEWPORT_X_START + (VIEWPORT_X_END - VIEWPORT_X_START) * eased)
    y = round((scaled_height - OUTPUT_HEIGHT) * VIEWPORT_Y_FOCUS)
    x = max(0, min(x, scaled_width - OUTPUT_WIDTH))
    y = max(0, min(y, scaled_height - OUTPUT_HEIGHT))

    return scaled.crop((x, y, x + OUTPUT_WIDTH, y + OUTPUT_HEIGHT))


def write_video(input_path: Path, output_path: Path) -> None:
    total_frames = frame_count()
    source = Image.open(input_path).convert("RGB")
    command = build_ffmpeg_command(output_path)

    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None

    try:
        for index in range(total_frames):
            frame = render_frame(source, index, total_frames)
            process.stdin.write(frame.tobytes())
        process.stdin.close()
        return_code = process.wait()
    except BrokenPipeError:
        return_code = process.wait()

    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, command)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build cinematic scene 003 from a still mall image."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to the source image.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to the generated video.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = args.input
    output_path = args.output

    if not input_path.exists():
        print(f"Input image not found: {input_path}", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Running ffmpeg...")
    try:
        write_video(input_path, output_path)
    except FileNotFoundError:
        print("ffmpeg was not found. Please install ffmpeg and try again.", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as error:
        print(f"ffmpeg failed with exit code {error.returncode}.", file=sys.stderr)
        return error.returncode

    print(f"Scene created: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
