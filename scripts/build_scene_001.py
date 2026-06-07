#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image

from camera.camera_state import CameraState
from camera.linear_camera_path import LinearCameraPath
from ffmpeg.encode_video_command import EncodeVideoCommand
from ffmpeg.ffmpeg_video_output import FfmpegVideoOutput
from scene.scene import Scene
from video.frame_settings import FrameSettings
from video.video_settings import VideoSettings


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "scenes" / "scene_001.mp4"

SCENE = Scene(
    source_path=PROJECT_ROOT / "images" / "navigation" / "001-001.png",
    duration=4.0,
    camera_path=LinearCameraPath(
        start=CameraState(
            zoom=1.0,
            x=760.0,
            y_focus=0.48,
        ),
        end=CameraState(
            zoom=1.13,
            x=1100.0,
            y_focus=0.48,
        ),
    ),
    video_settings=VideoSettings(
        frame=FrameSettings(
            width=1080,
            height=1920,
        ),
        fps=30,
        codec="libx264",
        preset="slow",
        crf="18",
        pixel_format="yuv420p",
    ),
)


def frame_count() -> int:
    return int(round(SCENE.duration * SCENE.video_settings.fps))


def render_frame(source: Image.Image, index: int, total_frames: int) -> Image.Image:
    """Render one undistorted 9:16 frame from the horizontal source image."""
    frame_settings = SCENE.video_settings.frame
    camera = SCENE.camera_path.state_at(index, total_frames)

    scaled_height = round(frame_settings.height * camera.zoom)
    scaled_width = round(source.width * scaled_height / source.height)
    scaled = source.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

    x = round(camera.x)
    y = round((scaled_height - frame_settings.height) * camera.y_focus)
    x = max(0, min(x, scaled_width - frame_settings.width))
    y = max(0, min(y, scaled_height - frame_settings.height))

    return scaled.crop(
        (
            x,
            y,
            x + frame_settings.width,
            y + frame_settings.height,
        )
    )


def render_frames(source: Image.Image, total_frames: int):
    for index in range(total_frames):
        yield render_frame(source, index, total_frames)


def render_video(input_path: Path, output_path: Path) -> None:
    total_frames = frame_count()
    source = Image.open(input_path).convert("RGB")
    command = EncodeVideoCommand(
        output_path=output_path,
        frame_count=total_frames,
        video_settings=SCENE.video_settings,
    )

    with FfmpegVideoOutput(command) as output:
        for frame in render_frames(source, total_frames):
            output.write(frame)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build cinematic scene 001 from a still mall image."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=SCENE.source_path,
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
