#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

try:
    from .paths import OUTPUT_DIR, PROJECT_ROOT, SCENES_DIR
except ImportError:
    from paths import OUTPUT_DIR, PROJECT_ROOT, SCENES_DIR

from ffmpeg.assemble_reel_command import AssembleReelCommand
from video.frame_settings import FrameSettings
from video.video_settings import VideoSettings


SCENE_FILENAMES = [
    "scene_001.mp4",
    "scene_002.mp4",
    "scene_003.mp4",
]
DEFAULT_OUTPUT = OUTPUT_DIR / "visitor_attention_reel_v01_no_audio.mp4"

FPS = 30
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
VIDEO_CODEC = "libx264"
PRESET = "slow"
CRF = "18"
PIXEL_FORMAT = "yuv420p"


def resolve_project_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def build_filtergraph(scene_count: int) -> str:
    filters = []
    labels = []

    for index in range(scene_count):
        label = f"v{index}"
        labels.append(f"[{label}]")
        filters.append(
            f"[{index}:v]"
            f"fps={FPS},"
            f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:"
            f"force_original_aspect_ratio=increase,"
            f"crop={OUTPUT_WIDTH}:{OUTPUT_HEIGHT},"
            f"setsar=1,"
            f"format={PIXEL_FORMAT},"
            f"setpts=PTS-STARTPTS"
            f"[{label}]"
        )

    filters.append(
        f"{''.join(labels)}"
        f"concat=n={scene_count}:v=1:a=0"
        f"[vout]"
    )
    return ";".join(filters)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the silent Visitor Attention visual reel."
    )
    parser.add_argument(
        "--scenes-dir",
        type=Path,
        default=SCENES_DIR,
        help="Directory containing the generated scene videos.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to the assembled silent reel.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    scenes_dir = resolve_project_path(args.scenes_dir)
    output_path = resolve_project_path(args.output)
    scene_paths = [scenes_dir / name for name in SCENE_FILENAMES]

    scenes_dir.mkdir(parents=True, exist_ok=True)

    missing = [path for path in scene_paths if not path.exists()]
    if missing:
        missing_list = "\n".join(f"- {path}" for path in missing)
        print(f"Missing input scene(s):\n{missing_list}", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    video_settings = VideoSettings(
        frame=FrameSettings(width=OUTPUT_WIDTH, height=OUTPUT_HEIGHT),
        fps=FPS,
        codec=VIDEO_CODEC,
        preset=PRESET,
        crf=CRF,
        pixel_format=PIXEL_FORMAT,
    )
    command = AssembleReelCommand(
        scene_paths=scene_paths,
        output_path=output_path,
        filtergraph=build_filtergraph(len(scene_paths)),
        video_settings=video_settings,
    )

    print("Running ffmpeg...")
    try:
        subprocess.run(command.argv, check=True)
    except FileNotFoundError:
        print("ffmpeg was not found. Please install ffmpeg and try again.", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as error:
        print(f"ffmpeg failed with exit code {error.returncode}.", file=sys.stderr)
        return error.returncode

    print(f"Reel created: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
