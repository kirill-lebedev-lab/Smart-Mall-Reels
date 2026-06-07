#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image

from ffmpeg.encode_video_command import EncodeVideoCommand
from ffmpeg.ffmpeg_video_output import FfmpegVideoOutput
from video.frame_settings import FrameSettings
from video.video_settings import VideoSettings


# Scene timing and output format.
DURATION = 4.0
FPS = 30
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920

# Motion tuning.
# Do not stretch the source image. Scale to cover the vertical frame, then crop.
ZOOM_START = 1.055
ZOOM_END = 1.0
BASE_SCALE_HEIGHT = OUTPUT_HEIGHT
VIEWPORT_X_START = 730
VIEWPORT_X_END = 705
VIEWPORT_Y_FOCUS = 0.5

# Encoding settings.
VIDEO_CODEC = "libx264"
PIXEL_FORMAT = "yuv420p"
CRF = "18"
PRESET = "slow"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "images" / "navigation" / "001-009.png"
DEFAULT_OUTPUT = PROJECT_ROOT / "scenes" / "scene_004.mp4"


def smoothstep(progress: float) -> float:
    """Return a calm 0..1 easing value for premium camera motion."""
    return progress * progress * (3 - 2 * progress)


def frame_count() -> int:
    return int(round(DURATION * FPS))


def render_frame(source: Image.Image, index: int, total_frames: int) -> Image.Image:
    """Render one undistorted 9:16 frame showing the visitor's choice moment."""
    progress = 0 if total_frames == 1 else index / (total_frames - 1)
    eased = smoothstep(progress)
    zoom = ZOOM_START + (ZOOM_END - ZOOM_START) * eased

    scaled_height = round(BASE_SCALE_HEIGHT * zoom)
    scaled_width = round(source.width * scaled_height / source.height)
    scaled = source.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

    # Keep the visitor-screen relationship central while the camera gently pulls back.
    x = round(VIEWPORT_X_START + (VIEWPORT_X_END - VIEWPORT_X_START) * eased)
    y = round((scaled_height - OUTPUT_HEIGHT) * VIEWPORT_Y_FOCUS)
    x = max(0, min(x, scaled_width - OUTPUT_WIDTH))
    y = max(0, min(y, scaled_height - OUTPUT_HEIGHT))

    return scaled.crop((x, y, x + OUTPUT_WIDTH, y + OUTPUT_HEIGHT))


def render_frames(source: Image.Image, total_frames: int):
    for index in range(total_frames):
        yield render_frame(source, index, total_frames)


def render_video(input_path: Path, output_path: Path) -> None:
    total_frames = frame_count()
    source = Image.open(input_path).convert("RGB")
    video_settings = VideoSettings(
        frame=FrameSettings(width=OUTPUT_WIDTH, height=OUTPUT_HEIGHT),
        fps=FPS,
        codec=VIDEO_CODEC,
        preset=PRESET,
        crf=CRF,
        pixel_format=PIXEL_FORMAT,
    )
    command = EncodeVideoCommand(
        output_path=output_path,
        frame_count=total_frames,
        video_settings=video_settings,
    )

    with FfmpegVideoOutput(command) as output:
        for frame in render_frames(source, total_frames):
            output.write(frame)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build cinematic scene 004 from a still mall image."
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
