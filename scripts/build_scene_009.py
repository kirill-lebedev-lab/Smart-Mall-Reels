#!/usr/bin/env python3
import argparse
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

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


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "scenes" / "scene_009.mp4"

SCENE = Scene(
    source_path=PROJECT_ROOT / "images" / "navigation" / "001-014.png",
    shots=[
        Shot(
            duration=3.6,
            camera_path=BezierCameraPath(
                control_points=[
                    CameraControlPoint(
                        progress=0.0,
                        camera=CameraState(
                            zoom=1.0,
                            x=477,
                            y_focus=0.86,
                        ),
                    ),
                    CameraControlPoint(
                        progress=0.35,
                        camera=CameraState(
                            zoom=1.09,
                            x=505,
                            y_focus=0.5,
                        ),
                    ),
                    CameraControlPoint(
                        progress=0.7,
                        camera=CameraState(
                            zoom=1.17,
                            x=570,
                            y_focus=0.25,
                        ),
                    ),
                    CameraControlPoint(
                        progress=1.0,
                        camera=CameraState(
                            zoom=1.205,
                            x=650,
                            y_focus=0.2,
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
        description="Build cinematic scene 009 from a still mall image."
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
