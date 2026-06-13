#!/usr/bin/env python3
import argparse
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from .paths import OUTPUT_DIR, PROJECT_ROOT
except ImportError:
    from paths import OUTPUT_DIR, PROJECT_ROOT


DEFAULT_VIDEO = OUTPUT_DIR / "visitor_attention_reel_en_v01.mp4"
DEFAULT_MUSIC = PROJECT_ROOT / "audio" / "music" / "Atrium Glass.mp3"
DEFAULT_OUTPUT = OUTPUT_DIR / "visitor_attention_reel_en_music_v01.mp4"
ENGLISH_REEL_BUILDER = Path(__file__).with_name(
    "build_visitor_attention_reel_en.py"
)

VOICE_VOLUME = 0.60
MUSIC_VOLUME = 0.35
MUSIC_FADE_IN = 0.40
MUSIC_FADE_OUT = 0.70
AUDIO_SAMPLE_RATE = 48000
AUDIO_BITRATE = "192k"


def resolve_project_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def non_negative_volume(value: str) -> float:
    try:
        volume = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("volume must be a number") from error
    if not math.isfinite(volume) or volume < 0:
        raise argparse.ArgumentTypeError(
            "volume must be a finite, non-negative number"
        )
    return volume


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the English Visitor Attention reel with Josh voiceover "
            "and quiet background music."
        )
    )
    parser.add_argument(
        "--video",
        type=Path,
        default=DEFAULT_VIDEO,
        help="English voiceover reel used as the master video.",
    )
    parser.add_argument(
        "--music",
        type=Path,
        default=DEFAULT_MUSIC,
        help="Background music file.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path for the English reel with background music.",
    )
    parser.add_argument(
        "--voice-volume",
        type=non_negative_volume,
        default=VOICE_VOLUME,
        help="Linear voiceover volume multiplier.",
    )
    parser.add_argument(
        "--music-volume",
        type=non_negative_volume,
        default=MUSIC_VOLUME,
        help="Linear background music volume multiplier.",
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


def build_english_reel(video_path: Path) -> int:
    command = [sys.executable, str(ENGLISH_REEL_BUILDER)]
    if video_path != DEFAULT_VIDEO:
        command.extend(["--output", str(video_path)])

    print(f"Building English voiceover reel with {ENGLISH_REEL_BUILDER}...")
    try:
        result = subprocess.run(command)
    except OSError as error:
        print(f"Could not run the English reel builder: {error}", file=sys.stderr)
        return 1
    if result.returncode != 0:
        print(
            f"English reel builder failed with exit code {result.returncode}.",
            file=sys.stderr,
        )
    return result.returncode


def mix_music(
    video_path: Path,
    music_path: Path,
    output_path: Path,
    video_duration: float,
    voice_volume: float,
    music_volume: float,
) -> None:
    fade_out_duration = min(MUSIC_FADE_OUT, video_duration)
    fade_out_start = max(0.0, video_duration - fade_out_duration)
    fade_in_duration = min(MUSIC_FADE_IN, video_duration)

    filter_complex = (
        f"[0:a]aresample={AUDIO_SAMPLE_RATE},"
        f"pan=stereo|c0=c0|c1=c0,"
        f"volume={voice_volume:.6f}[voice];"
        f"[1:a]aresample={AUDIO_SAMPLE_RATE},"
        f"aformat=channel_layouts=stereo,"
        f"volume={music_volume:.6f},"
        f"afade=t=in:st=0:d={fade_in_duration:.6f},"
        f"afade=t=out:st={fade_out_start:.6f}:d={fade_out_duration:.6f},"
        f"atrim=duration={video_duration:.6f}[music];"
        f"[voice][music]"
        f"amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
        f"atrim=duration={video_duration:.6f}[mixed]"
    )
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-stream_loop",
        "-1",
        "-i",
        str(music_path),
        "-filter_complex",
        filter_complex,
        "-map",
        "0:v:0",
        "-map",
        "[mixed]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        AUDIO_BITRATE,
        "-ar",
        str(AUDIO_SAMPLE_RATE),
        "-t",
        f"{video_duration:.6f}",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    print("\nMixing voiceover and background music...")
    subprocess.run(command, check=True)


def main() -> int:
    args = parse_args()
    video_path = resolve_project_path(args.video)
    music_path = resolve_project_path(args.music)
    output_path = resolve_project_path(args.output)

    if not check_media_tools():
        return 2

    if not music_path.is_file():
        print(f"Music file not found: {music_path}", file=sys.stderr)
        return 1

    build_result = build_english_reel(video_path)
    if build_result != 0:
        return build_result

    if not video_path.is_file():
        print(
            f"English voiceover reel was not found after build: {video_path}",
            file=sys.stderr,
        )
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        video_duration = probe_duration(video_path)
        music_duration = probe_duration(music_path)

        print(f"\nInput video: {video_path}")
        print(f"Music file: {music_path}")
        print(f"Video duration: {video_duration:.3f}s")
        print(f"Music duration: {music_duration:.3f}s")
        print(f"Voice volume: {args.voice_volume:.3f}")
        print(f"Music volume: {args.music_volume:.3f}")

        with tempfile.TemporaryDirectory(
            prefix="visitor_attention_music_",
            dir=output_path.parent,
        ) as temp_dir:
            temp_output = Path(temp_dir) / output_path.name
            mix_music(
                video_path,
                music_path,
                temp_output,
                video_duration,
                args.voice_volume,
                args.music_volume,
            )
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

    print(f"\nEnglish music reel created: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
