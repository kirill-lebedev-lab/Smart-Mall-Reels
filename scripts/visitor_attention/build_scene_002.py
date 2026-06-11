#!/usr/bin/env python3
import argparse
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

try:
    from .paths import FITTING_ROOM_IMAGES_DIR, SCENES_DIR
except ImportError:
    from paths import FITTING_ROOM_IMAGES_DIR, SCENES_DIR

from camera.camera_state import CameraState
from camera.linear_camera_path import LinearCameraPath
from ffmpeg.encode_video_command import EncodeVideoCommand
from ffmpeg.ffmpeg_video_output import FfmpegVideoOutput
from scene.scene import Scene
from scene.scene_frame_renderer import SceneFrameRenderer
from scene.shot import Shot
from video.frame_settings import FrameSettings
from video.video_settings import VideoSettings


DEFAULT_OUTPUT = SCENES_DIR / "scene_002.mp4"

SCENE = Scene(
    source_path=FITTING_ROOM_IMAGES_DIR / "003-002.png",
    shots=[
        Shot(
            duration=1.9,
            camera_path=LinearCameraPath(
                start=CameraState(
                    zoom=1.0,
                    x=790,
                    y_focus=0.48,
                ),
                end=CameraState(
                    zoom=1.07,
                    x=815,
                    y_focus=0.48,
                ),
            ),
        ),
    ],
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


def render_video(scene: Scene, output_path: Path) -> None:
    command = EncodeVideoCommand(
        output_path=output_path,
        frame_count=scene.frame_count,
        video_settings=scene.video_settings,
    )

    with SceneFrameRenderer(scene) as renderer:
        with FfmpegVideoOutput(command) as output:
            for frame in renderer.frames():
                output.write(frame)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the Visitor Attention promo refusal scene."
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
        scene = replace(SCENE, source_path=input_path)
        render_video(scene, output_path)
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
