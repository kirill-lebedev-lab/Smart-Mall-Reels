#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

try:
    from .paths import OUTPUT_DIR, PROJECT_ROOT, SCENES_DIR
    from .timeline import SCENE_FILENAMES
    from .voice_script import VOICE_SCRIPT, VoiceLine
except ImportError:
    from paths import OUTPUT_DIR, PROJECT_ROOT, SCENES_DIR
    from timeline import SCENE_FILENAMES
    from voice_script import VOICE_SCRIPT, VoiceLine

from ffmpeg.cinematic_captions import build_cinematic_caption_filter


DEFAULT_INPUT = OUTPUT_DIR / "visitor_attention_reel_en_music_v01.mp4"
DEFAULT_OUTPUT = (
    OUTPUT_DIR / "visitor_attention_reel_en_music_captions_v01.mp4"
)
DEFAULT_VOICE_DIR = (
    PROJECT_ROOT / "audio" / "voice" / "visitor_attention" / "Josh"
)
MUSIC_REEL_BUILDER = Path(__file__).with_name(
    "build_visitor_attention_reel_en_with_music.py"
)

FONT_FAMILY = "Avenir Next Medium"
TEXT_COLOR = "0xFFF6DC"
SHADOW_COLOR = "0x000000"
CAPTION_FADE = 0.65
REGULAR_CAPTION_LEAD = 0.25
REGULAR_CAPTION_TAIL = 0.375
VIDEO_CODEC = "libx264"
PIXEL_FORMAT = "yuv420p"
CRF = "18"
PRESET = "slow"

REGULAR_CAPTION_STYLES = [
    {
        "display_text": "Advertising became\nthe background.",
        "font_size": 68,
        "x": "(w-text_w)/2",
        "y": "h*0.785",
    },
    {"font_size": 68, "x": "(w-text_w)/2", "y": "h*0.815"},
    {"font_size": 68, "x": "(w-text_w)/2", "y": "h*0.815"},
    {
        "display_text": "But they immediately\nnotice themselves.",
        "font_size": 64,
        "x": "(w-text_w)/2",
        "y": "h*0.785",
    },
]
FINAL_CAPTION_STYLES = [
    {
        "text": "Smart Mirror",
        "font_size": 108,
        "x": "(w-text_w)/2",
        "y": "h*0.360",
        "border_width": 2,
    },
    {
        "text": "Smart Mall",
        "font_size": 108,
        "x": "(w-text_w)/2",
        "y": "h*0.445",
        "border_width": 2,
    },
    {
        "text": "Designed around people",
        "font_size": 62,
        "x": "(w-text_w)/2",
        "y": "h*0.585",
        "border_width": 2,
    },
]


@dataclass(frozen=True)
class ScheduledLine:
    line: VoiceLine
    start: float
    end: float


def resolve_project_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the English Visitor Attention music reel with cinematic "
            "captions synchronized to the voiceover."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="English music reel used as the caption master.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path for the captioned English music reel.",
    )
    return parser.parse_args()


def check_media_tools() -> bool:
    missing = [tool for tool in ("ffmpeg", "ffprobe") if shutil.which(tool) is None]
    if missing:
        print(
            f"Required media tool(s) not found: {', '.join(missing)}. "
            "Please install ffmpeg and try again.",
            file=sys.stderr,
        )
        return False
    return True


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
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        if error.stderr:
            print(error.stderr.strip(), file=sys.stderr)
        print(
            f"ffprobe failed for {path} with exit code {error.returncode}.",
            file=sys.stderr,
        )
        raise

    try:
        return float(result.stdout.strip())
    except ValueError:
        print(f"ffprobe returned an invalid duration for {path}.", file=sys.stderr)
        raise subprocess.CalledProcessError(1, command)


def build_music_reel(input_path: Path) -> int:
    command = [sys.executable, str(MUSIC_REEL_BUILDER)]
    if input_path != DEFAULT_INPUT:
        command.extend(["--output", str(input_path)])

    print(f"Building English music reel with {MUSIC_REEL_BUILDER}...")
    try:
        result = subprocess.run(command)
    except OSError as error:
        print(f"Could not run the English music reel builder: {error}", file=sys.stderr)
        return 1
    if result.returncode != 0:
        print(
            f"English music reel builder failed with exit code "
            f"{result.returncode}.",
            file=sys.stderr,
        )
    return result.returncode


def schedule_lines(voice_dir: Path) -> list[ScheduledLine]:
    scene_starts = {}
    elapsed = 0.0
    for scene_name in SCENE_FILENAMES:
        scene_path = SCENES_DIR / scene_name
        scene_starts[scene_name] = elapsed
        elapsed += probe_duration(scene_path)

    scheduled = []
    for line in VOICE_SCRIPT:
        start = scene_starts[line.scene] + line.start_offset
        duration = probe_duration(voice_dir / line.filename)
        scheduled.append(ScheduledLine(line=line, start=start, end=start + duration))
    return scheduled


def build_captions(
    scheduled: list[ScheduledLine],
    video_duration: float,
) -> list[dict]:
    captions = []
    for item, style in zip(scheduled[:4], REGULAR_CAPTION_STYLES):
        captions.append(
            {
                "text": item.line.text,
                "start": max(0.0, item.start - REGULAR_CAPTION_LEAD),
                "end": min(
                    video_duration,
                    item.end + REGULAR_CAPTION_TAIL,
                ),
                **style,
            }
        )

    for item, style in zip(scheduled[4:], FINAL_CAPTION_STYLES):
        captions.append(
            {
                **style,
                "start": item.start,
                "end": video_duration,
                "fade_out": False,
            }
        )
    return captions


def build_caption_filter(captions: list[dict]) -> str:
    return build_cinematic_caption_filter(
        captions,
        input_label="0:v",
        output_label="captioned",
        font_family=FONT_FAMILY,
        text_color=TEXT_COLOR,
        shadow_color=SHADOW_COLOR,
        fade=CAPTION_FADE,
    )


def render_captions(
    input_path: Path,
    output_path: Path,
    captions: list[dict],
    video_duration: float,
) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-filter_complex",
        build_caption_filter(captions),
        "-map",
        "[captioned]",
        "-map",
        "0:a:0",
        "-c:v",
        VIDEO_CODEC,
        "-preset",
        PRESET,
        "-crf",
        CRF,
        "-pix_fmt",
        PIXEL_FORMAT,
        "-c:a",
        "copy",
        "-t",
        f"{video_duration:.6f}",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    print("\nRendering cinematic captions...")
    subprocess.run(command, check=True)


def main() -> int:
    args = parse_args()
    input_path = resolve_project_path(args.input)
    output_path = resolve_project_path(args.output)
    voice_dir = DEFAULT_VOICE_DIR

    if not check_media_tools():
        return 2

    build_result = build_music_reel(input_path)
    if build_result != 0:
        return build_result

    if not input_path.is_file():
        print(
            f"English music reel was not found after build: {input_path}",
            file=sys.stderr,
        )
        return 1

    missing_scenes = [
        SCENES_DIR / scene
        for scene in SCENE_FILENAMES
        if not (SCENES_DIR / scene).is_file()
    ]
    missing_voice = [
        voice_dir / line.filename
        for line in VOICE_SCRIPT
        if not (voice_dir / line.filename).is_file()
    ]
    if missing_scenes or missing_voice:
        print("Missing timing source file(s):", file=sys.stderr)
        for path in [*missing_scenes, *missing_voice]:
            print(f"- {path}", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        video_duration = probe_duration(input_path)
        scheduled = schedule_lines(voice_dir)
        captions = build_captions(scheduled, video_duration)

        print(f"Input video: {input_path}")
        print(f"Video duration: {video_duration:.3f}s")
        print("\nCaption timeline:")
        for caption in captions:
            print(
                f'- "{caption["text"]}": '
                f'{caption["start"]:.3f}s-{caption["end"]:.3f}s'
            )

        with tempfile.TemporaryDirectory(
            prefix="visitor_attention_captions_",
            dir=output_path.parent,
        ) as temp_dir:
            temp_output = Path(temp_dir) / output_path.name
            render_captions(input_path, temp_output, captions, video_duration)
            temp_output.replace(output_path)
    except subprocess.CalledProcessError as error:
        print(
            f"Media command failed with exit code {error.returncode}.",
            file=sys.stderr,
        )
        return error.returncode
    except OSError as error:
        print(f"Could not write output file: {error}", file=sys.stderr)
        return 1

    print(f"\nCaptioned reel created: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
