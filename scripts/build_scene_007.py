#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image

from ffmpeg.encode_video_command import EncodeVideoCommand
from ffmpeg.ffmpeg_video_output import FfmpegVideoOutput


# Scene timing and output format.
DURATION = 5.5
FPS = 30
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920

# Motion tuning.
# Do not stretch the source image. Scale to cover the vertical frame, then crop.
# Match the final camera of scene 006 exactly, then move into the route reveal.
ZOOM_START = 1.02
ROUTE_PUSH_AMOUNT = 0.018
VIEWPORT_X_START = 735.0
ATTENTION_DRIFT = 210.0
ROUTE_FOLLOW_DRIFT = 335.0
VIEWPORT_Y_FOCUS_START = 0.5
VIEWPORT_Y_FOCUS_END = 0.95

# Encoding settings.
VIDEO_CODEC = "libx264"
PIXEL_FORMAT = "yuv420p"
CRF = "18"
PRESET = "slow"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "images" / "navigation" / "001-012.png"
DEFAULT_OUTPUT = PROJECT_ROOT / "scenes" / "scene_007.mp4"


def smoothstep(progress: float) -> float:
    """Return a calm 0..1 easing value for premium camera motion."""
    return progress * progress * (3 - 2 * progress)


def phase_value(progress: float, start: float, end: float) -> float:
    """Return a smooth 0..1 activation value for an overlapping motion layer."""
    if progress <= start:
        return 0.0
    if progress >= end:
        return 1.0
    return smoothstep((progress - start) / (end - start))


def interpolate_camera(progress: float) -> tuple[float, float, float]:
    """Return a continuous camera path without internal stops."""
    attention = phase_value(progress, 0.22, 0.72)
    route_follow = phase_value(progress, 0.52, 1.0)

    zoom = ZOOM_START + ROUTE_PUSH_AMOUNT * route_follow
    x = VIEWPORT_X_START + ATTENTION_DRIFT * attention + ROUTE_FOLLOW_DRIFT * route_follow
    y_focus = VIEWPORT_Y_FOCUS_START + (
        VIEWPORT_Y_FOCUS_END - VIEWPORT_Y_FOCUS_START
    ) * attention
    return zoom, x, y_focus


def frame_count() -> int:
    return int(round(DURATION * FPS))


def render_frame(source: Image.Image, index: int, total_frames: int) -> Image.Image:
    """Render one undistorted 9:16 frame as the mall route activates."""
    progress = 0 if total_frames == 1 else index / (total_frames - 1)
    zoom, x, y_focus = interpolate_camera(progress)

    scale = (OUTPUT_HEIGHT / source.height) * zoom
    scaled_width = source.width * scale
    scaled_height = source.height * scale

    # Reframe in phases: completed interaction, environment response, route activation.
    y = (scaled_height - OUTPUT_HEIGHT) * y_focus
    x = max(0.0, min(x, scaled_width - OUTPUT_WIDTH))
    y = max(0.0, min(y, scaled_height - OUTPUT_HEIGHT))

    crop_box = (
        x / scale,
        y / scale,
        (x + OUTPUT_WIDTH) / scale,
        (y + OUTPUT_HEIGHT) / scale,
    )
    return source.transform(
        (OUTPUT_WIDTH, OUTPUT_HEIGHT),
        Image.Transform.EXTENT,
        crop_box,
        Image.Resampling.BICUBIC,
    )


def render_frames(source: Image.Image, total_frames: int):
    for index in range(total_frames):
        yield render_frame(source, index, total_frames)


def render_video(input_path: Path, output_path: Path) -> None:
    total_frames = frame_count()
    source = Image.open(input_path).convert("RGB")
    command = EncodeVideoCommand(
        output_path=output_path,
        width=OUTPUT_WIDTH,
        height=OUTPUT_HEIGHT,
        fps=FPS,
        frame_count=total_frames,
        codec=VIDEO_CODEC,
        preset=PRESET,
        crf=CRF,
        output_pixel_format=PIXEL_FORMAT,
    )

    with FfmpegVideoOutput(command) as output:
        for frame in render_frames(source, total_frames):
            output.write(frame)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build cinematic scene 007 from a still mall image."
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
        render_video(input_path, output_path)
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
