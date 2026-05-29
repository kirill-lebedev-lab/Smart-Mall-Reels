#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


# Reel inputs and output.
SCENES = [
    "scenes/scene_001.mp4",
    "scenes/scene_002.mp4",
    "scenes/scene_003.mp4",
    "scenes/scene_004.mp4",
    "scenes/scene_005.mp4",
    "scenes/scene_006.mp4",
    "scenes/scene_007.mp4",
    "scenes/scene_008.mp4",
]
OUTPUT_PATH = "output/mall_navigation_reel_v01.mp4"

# Video and transition settings.
FPS = 30
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
TRANSITION_DURATION = 0.5
VIDEO_CODEC = "libx264"
PIXEL_FORMAT = "yuv420p"
CRF = "18"
PRESET = "slow"

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def project_path(path: str) -> Path:
    return PROJECT_ROOT / path


def check_input_scenes(scene_paths: list[Path]) -> None:
    missing = [path for path in scene_paths if not path.exists()]
    if missing:
        missing_list = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Missing input scene(s):\n{missing_list}")


def probe_duration(path: Path) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return float(result.stdout.strip())


def build_filtergraph(scene_count: int, durations: list[float]) -> str:
    # Normalize every scene so future additions still match the reel format.
    filters = []
    for index in range(scene_count):
        filters.append(
            f"[{index}:v]"
            f"fps={FPS},"
            f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={OUTPUT_WIDTH}:{OUTPUT_HEIGHT},"
            f"setsar=1,"
            f"format={PIXEL_FORMAT}"
            f"[v{index}]"
        )

    if scene_count == 1:
        filters.append("[v0]copy[vout]")
        return ";".join(filters)

    previous_label = "v0"
    elapsed = durations[0]

    for index in range(1, scene_count):
        output_label = "vout" if index == scene_count - 1 else f"xf{index}"
        offset = elapsed - TRANSITION_DURATION
        filters.append(
            f"[{previous_label}][v{index}]"
            f"xfade=transition=fade:"
            f"duration={TRANSITION_DURATION}:"
            f"offset={offset:.3f}"
            f"[{output_label}]"
        )
        previous_label = output_label
        elapsed += durations[index] - TRANSITION_DURATION

    return ";".join(filters)


def build_ffmpeg_command(scene_paths: list[Path], output_path: Path) -> list[str]:
    durations = [probe_duration(path) for path in scene_paths]

    command = ["ffmpeg", "-y"]
    for path in scene_paths:
        command.extend(["-i", str(path)])

    command.extend(
        [
            "-filter_complex",
            build_filtergraph(len(scene_paths), durations),
            "-map",
            "[vout]",
            "-r",
            str(FPS),
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
    )
    return command


def main() -> int:
    scene_paths = [project_path(path) for path in SCENES]
    output_path = project_path(OUTPUT_PATH)

    try:
        check_input_scenes(scene_paths)
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Running ffmpeg...")
    try:
        command = build_ffmpeg_command(scene_paths, output_path)
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print("ffmpeg or ffprobe was not found. Please install ffmpeg and try again.", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as error:
        print(f"ffmpeg failed with exit code {error.returncode}.", file=sys.stderr)
        return error.returncode

    print(f"Reel created: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
