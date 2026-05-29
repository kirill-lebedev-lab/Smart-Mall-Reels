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
    "scenes/scene_009.mp4",
]
OUTPUT_PATH = "output/mall_navigation_reel_v01.mp4"
NO_TEXT_OUTPUT_PATH = "output/mall_navigation_reel_v01_no_text.mp4"

# Video and transition settings.
FPS = 30
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
TRANSITION_DURATION = 0.5
VIDEO_CODEC = "libx264"
PIXEL_FORMAT = "yuv420p"
CRF = "18"
PRESET = "slow"

# Caption settings.
FONT_FILE = "/System/Library/Fonts/Avenir.ttc"
TEXT_COLOR = "0xFFF6DC"
SHADOW_COLOR = "0x000000"
CAPTION_FADE = 0.65
CAPTIONS = [
    {
        "text": "The mall notices you",
        "start": 1.2,
        "end": 4.2,
        "font_size": 62,
        "x": "(w-text_w)/2",
        "y": "h*0.815",
    },
    {
        "text": "Space begins to respond",
        "start": 11.2,
        "end": 14.2,
        "font_size": 58,
        "x": "(w-text_w)/2",
        "y": "h*0.815",
    },
    {
        "text": "Smart Mall",
        "start": 41.4,
        "end": 45.1,
        "font_size": 104,
        "x": "(w-text_w)/2",
        "y": "h*0.382",
        "border_width": 3,
        "shadow_opacity": 0.56,
    },
    {
        "text": "Space that responds to people",
        "start": 41.75,
        "end": 45.1,
        "font_size": 56,
        "x": "(w-text_w)/2",
        "y": "h*0.462",
        "border_width": 3,
        "shadow_opacity": 0.56,
    },
]

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


def escape_drawtext_text(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace(",", "\\,")
    )


def escape_drawtext_expression(expression: str) -> str:
    return expression.replace(",", "\\,")


def caption_alpha_expression(start: float, end: float) -> str:
    fade = CAPTION_FADE
    expression = (
        f"if(lt(t,{start:.3f}),0,"
        f"if(lt(t,{start + fade:.3f}),(t-{start:.3f})/{fade:.3f},"
        f"if(lt(t,{end - fade:.3f}),0.92,"
        f"if(lt(t,{end:.3f}),0.92*(1-(t-{end - fade:.3f})/{fade:.3f}),0))))"
    )
    return escape_drawtext_expression(expression)


def build_caption_filter() -> str:
    filters = ["[0:v]null[cap0]"]

    for index, caption in enumerate(CAPTIONS):
        input_label = f"cap{index}"
        output_label = "vout" if index == len(CAPTIONS) - 1 else f"cap{index + 1}"
        text = escape_drawtext_text(caption["text"])
        alpha = caption_alpha_expression(caption["start"], caption["end"])
        border_width = caption.get("border_width", 2)
        shadow_opacity = caption.get("shadow_opacity", 0.48)
        enable = escape_drawtext_expression(
            f"between(t,{caption['start']:.3f},{caption['end']:.3f})"
        )
        filters.append(
            f"[{input_label}]"
            f"drawtext="
            f"fontfile='{FONT_FILE}':"
            f"text='{text}':"
            f"fontsize={caption['font_size']}:"
            f"fontcolor={TEXT_COLOR}:"
            f"alpha='{alpha}':"
            f"x={caption['x']}:"
            f"y={caption['y']}:"
            f"bordercolor={SHADOW_COLOR}@0.32:"
            f"borderw={border_width}:"
            f"shadowcolor={SHADOW_COLOR}@{shadow_opacity}:"
            f"shadowx=0:"
            f"shadowy=3:"
            f"enable='{enable}'"
            f"[{output_label}]"
        )

    return ";".join(filters)


def build_caption_command(input_path: Path, output_path: Path) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-filter_complex",
        build_caption_filter(),
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


def main() -> int:
    scene_paths = [project_path(path) for path in SCENES]
    output_path = project_path(OUTPUT_PATH)
    no_text_output_path = project_path(NO_TEXT_OUTPUT_PATH)

    try:
        check_input_scenes(scene_paths)
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Running ffmpeg...")
    try:
        reel_command = build_ffmpeg_command(scene_paths, no_text_output_path)
        subprocess.run(reel_command, check=True)
        caption_command = build_caption_command(no_text_output_path, output_path)
        subprocess.run(caption_command, check=True)
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
