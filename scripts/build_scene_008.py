#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image


# Scene timing and output format.
DURATION = 12.0
FPS = 30
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920

# Motion tuning.
# Do not stretch the source image. Scale to cover the vertical frame, then crop.
FOCUS_END = 2.5
PAUSE_END = 3.0

ZOOM_START = 1.0
ZOOM_AFTER_FOCUS = 1.035
APPROACH_ZOOM_AMOUNT = 0.44
ASCENT_ZOOM_AMOUNT = 0.04

SOURCE_X_START = 705.0
SOURCE_X_AFTER_FOCUS = 730.0
APPROACH_X_DRIFT = -270.0
ASCENT_X_DRIFT = 250.0

VIEWPORT_Y_FOCUS_START = 0.82
VIEWPORT_Y_FOCUS_AFTER_FOCUS = 0.76
APPROACH_Y_DRIFT = -0.02
ASCENT_Y_DRIFT = -0.66

# Encoding settings.
VIDEO_CODEC = "libx264"
PIXEL_FORMAT = "yuv420p"
CRF = "18"
PRESET = "slow"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "images" / "navigation" / "001-013.png"
DEFAULT_OUTPUT = PROJECT_ROOT / "scenes" / "scene_008.mp4"


def smoothstep(progress: float) -> float:
    """Return a calm 0..1 easing value for premium camera motion."""
    return progress * progress * (3 - 2 * progress)


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp a value to the 0..1 range used by camera phase curves."""
    return max(low, min(value, high))


def phase_value(time: float, start: float, end: float) -> float:
    """Return a smooth 0..1 phase value between two scene times."""
    if time <= start:
        return 0.0
    if time >= end:
        return 1.0
    return smoothstep((time - start) / (end - start))


def interpolate_camera(progress: float) -> tuple[float, float, float]:
    """Return orientation, pause, then one continuous route into the escalator."""
    time = progress * DURATION
    focus = phase_value(time, 0.0, FOCUS_END)
    route_progress = clamp((time - PAUSE_END) / (DURATION - PAUSE_END))

    # The ascent starts before the approach is finished, so the camera enters the
    # escalator trajectory as one continuous spatial movement.
    escalator_approach = smoothstep(route_progress)
    escalator_ascent = smoothstep(clamp((route_progress - 0.42) / 0.58))

    zoom = (
        ZOOM_START
        + (ZOOM_AFTER_FOCUS - ZOOM_START) * focus
        + APPROACH_ZOOM_AMOUNT * escalator_approach
        + ASCENT_ZOOM_AMOUNT * escalator_ascent
    )
    source_x = (
        SOURCE_X_START
        + (SOURCE_X_AFTER_FOCUS - SOURCE_X_START) * focus
        + APPROACH_X_DRIFT * escalator_approach
        + ASCENT_X_DRIFT * escalator_ascent
    )
    y_focus = (
        VIEWPORT_Y_FOCUS_START
        + (VIEWPORT_Y_FOCUS_AFTER_FOCUS - VIEWPORT_Y_FOCUS_START) * focus
        + APPROACH_Y_DRIFT * escalator_approach
        + ASCENT_Y_DRIFT * escalator_ascent
    )
    return zoom, source_x, y_focus


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
    """Render one undistorted 9:16 frame following the distributed route system."""
    progress = 0 if total_frames == 1 else index / (total_frames - 1)
    zoom, source_x, y_focus = interpolate_camera(progress)

    scale = (OUTPUT_HEIGHT / source.height) * zoom
    scaled_width = source.width * scale
    scaled_height = source.height * scale

    # Follow the architectural route upward while the display remains secondary context.
    x = source_x * scale
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
        description="Build cinematic scene 008 from a still mall image."
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
