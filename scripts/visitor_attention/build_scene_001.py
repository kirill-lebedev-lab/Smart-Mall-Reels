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

from camera.bezier_camera_path import BezierCameraPath
from camera.camera_control_point import CameraControlPoint
from camera.camera_state import CameraState
from ffmpeg.encode_video_command import EncodeVideoCommand
from ffmpeg.ffmpeg_video_output import FfmpegVideoOutput
from scene.scene import Scene
from scene.scene_frame_renderer import SceneFrameRenderer
from scene.shot import Shot
from video.frame_settings import FrameSettings
from video.video_settings import VideoSettings


DEFAULT_OUTPUT = SCENES_DIR / "scene_001.mp4"

SCENE = Scene(
    source_path=FITTING_ROOM_IMAGES_DIR / "003-001-1.png",
    shots=[
        Shot(
            duration=2.3,
            camera_path=BezierCameraPath(
                control_points=[
                    CameraControlPoint(
                        progress=0.0,
                        camera=CameraState(
                            zoom=1.26,
                            x=630,
                            y_focus=0.82,
                        ),
                    ),
                    CameraControlPoint(
                        progress=0.55,
                        camera=CameraState(
                            zoom=1.1,
                            x=550,
                            y_focus=0.62,
                        ),
                    ),
                    CameraControlPoint(
                        progress=1.0,
                        camera=CameraState(
                            zoom=1.0,
                            x=405,
                            y_focus=0.5,
                        ),
                    ),
                ]
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
        description="Build the Visitor Attention opening scene."
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
