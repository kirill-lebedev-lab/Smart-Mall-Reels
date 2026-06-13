#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

try:
    from .paths import OUTPUT_DIR, PROJECT_ROOT, SCENES_DIR
except ImportError:
    from paths import OUTPUT_DIR, PROJECT_ROOT, SCENES_DIR


SCENE_FILENAMES = [
    "scene_001.mp4",
    "scene_002.mp4",
    "scene_003.mp4",
    "scene_004.mp4",
    "scene_005.mp4",
]

DEFAULT_VIDEO = OUTPUT_DIR / "visitor_attention_reel_v01_no_audio.mp4"
DEFAULT_VOICE_DIR = (
    PROJECT_ROOT / "audio" / "voice" / "visitor_attention" / "Josh"
)
DEFAULT_OUTPUT = OUTPUT_DIR / "visitor_attention_reel_en_v01.mp4"
VISUAL_BUILDER = Path(__file__).with_name("build_visitor_attention_reel.py")

AUDIO_SAMPLE_RATE = 48000
AUDIO_BITRATE = "192k"
TIMING_TOLERANCE = 0.001
FINAL_FRAME_PADDING = 0.20


@dataclass(frozen=True)
class VoiceLine:
    scene: str
    text: str
    filename: str
    start_offset: float


@dataclass(frozen=True)
class SceneTiming:
    filename: str
    duration: float
    start: float

    @property
    def end(self) -> float:
        return self.start + self.duration


@dataclass(frozen=True)
class ScheduledLine:
    line: VoiceLine
    path: Path
    duration: float
    absolute_start: float

    @property
    def end(self) -> float:
        return self.absolute_start + self.duration


# These offsets are measured from the start of each scene and are intentionally
# explicit so they can be tuned after reviewing the rendered reel.
VOICE_SCRIPT = [
    VoiceLine(
        scene="scene_001.mp4",
        text="Advertising became the background.",
        filename=(
            "ElevenLabs_2026-06-13T10_49_09_"
            "Josh - Teacher for Kids_pvc_sp100_s50_sb75_v3.mp3"
        ),
        start_offset=0.50,
    ),
    VoiceLine(
        scene="scene_002.mp4",
        text="Pushy sales are annoying.",
        filename=(
            "ElevenLabs_2026-06-13T10_49_58_"
            "Josh - Teacher for Kids_pvc_sp100_s50_sb75_v3.mp3"
        ),
        start_offset=0.55,
    ),
    VoiceLine(
        scene="scene_003.mp4",
        text="People are tired of pressure.",
        filename=(
            "ElevenLabs_2026-06-13T10_50_33_"
            "Josh - Teacher for Kids_pvc_sp100_s50_sb75_v3.mp3"
        ),
        start_offset=0.45,
    ),
    VoiceLine(
        scene="scene_004.mp4",
        text="But they immediately notice themselves.",
        filename=(
            "ElevenLabs_2026-06-13T10_51_11_"
            "Josh - Teacher for Kids_pvc_sp100_s50_sb75_v3.mp3"
        ),
        start_offset=0.60,
    ),
    VoiceLine(
        scene="scene_005.mp4",
        text="A smart mirror helps people see themselves differently.",
        filename=(
            "ElevenLabs_2026-06-13T10_51_44_"
            "Josh - Teacher for Kids_pvc_sp100_s50_sb75_v3.mp3"
        ),
        start_offset=0.90,
    ),
    VoiceLine(
        scene="scene_005.mp4",
        text="Smart Mirror.",
        filename=(
            "ElevenLabs_2026-06-13T10_52_14_"
            "Josh - Teacher for Kids_pvc_sp100_s50_sb75_v3.mp3"
        ),
        start_offset=3.95,
    ),
    VoiceLine(
        scene="scene_005.mp4",
        text="Smart Mall.",
        filename=(
            "ElevenLabs_2026-06-13T10_52_38_"
            "Josh - Teacher for Kids_pvc_sp100_s50_sb75_v3.mp3"
        ),
        start_offset=5.20,
    ),
    VoiceLine(
        scene="scene_005.mp4",
        text="Designed around people.",
        filename=(
            "ElevenLabs_2026-06-13T10_53_08_"
            "Josh - Teacher for Kids_pvc_sp100_s50_sb75_v3.mp3"
        ),
        start_offset=6.35,
    ),
]


def resolve_project_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the English Visitor Attention reel with timed voiceover."
    )
    parser.add_argument(
        "--video",
        type=Path,
        default=DEFAULT_VIDEO,
        help="Silent visual reel used as the master video track.",
    )
    parser.add_argument(
        "--voice-dir",
        type=Path,
        default=DEFAULT_VOICE_DIR,
        help="Directory containing the eight English voice clips.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path for the English voiceover reel.",
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


def build_silent_reel() -> int:
    print(f"Building silent visual reel with {VISUAL_BUILDER}...")
    try:
        result = subprocess.run([sys.executable, str(VISUAL_BUILDER)])
    except OSError as error:
        print(f"Could not run the visual reel builder: {error}", file=sys.stderr)
        return 1
    if result.returncode != 0:
        print(
            f"Visual reel builder failed with exit code {result.returncode}.",
            file=sys.stderr,
        )
    return result.returncode


def calculate_scene_timings(scene_paths: List[Path]) -> Dict[str, SceneTiming]:
    timings = {}
    scene_start = 0.0

    print("\nScene timeline:")
    for path in scene_paths:
        duration = probe_duration(path)
        timing = SceneTiming(path.name, duration, scene_start)
        timings[path.name] = timing
        print(
            f"- {path.name}: duration={duration:.3f}s, "
            f"start={timing.start:.3f}s, end={timing.end:.3f}s"
        )
        scene_start = timing.end

    return timings


def schedule_voice_lines(
    voice_dir: Path,
    scene_timings: Dict[str, SceneTiming],
) -> List[ScheduledLine]:
    scheduled = []

    print("\nVoiceover timeline:")
    for line in VOICE_SCRIPT:
        path = voice_dir / line.filename
        duration = probe_duration(path)
        scene = scene_timings[line.scene]
        absolute_start = scene.start + line.start_offset
        scheduled_line = ScheduledLine(line, path, duration, absolute_start)
        scheduled.append(scheduled_line)
        print(f'- "{line.text}"')
        print(f"  file: {line.filename}")
        print(
            f"  duration={duration:.3f}s, offset={line.start_offset:.3f}s, "
            f"absolute_start={absolute_start:.3f}s, end={scheduled_line.end:.3f}s"
        )

    return scheduled


def collect_warnings(
    scheduled: List[ScheduledLine],
    scene_timings: Dict[str, SceneTiming],
    output_duration: float,
) -> List[str]:
    warnings = []

    for item in scheduled:
        scene = scene_timings[item.line.scene]
        scene_end = (
            output_duration
            if item.line.scene == SCENE_FILENAMES[-1]
            else scene.end
        )
        actual_offset = item.absolute_start - scene.start
        if actual_offset + TIMING_TOLERANCE < item.line.start_offset:
            warnings.append(
                f'"{item.line.text}" starts at offset {actual_offset:.3f}s, '
                f"before its semantic offset {item.line.start_offset:.3f}s."
            )
        if item.end > scene_end + TIMING_TOLERANCE:
            warnings.append(
                f'"{item.line.text}" ends at {item.end:.3f}s and does not fit '
                f"within {scene.filename}, which ends at {scene_end:.3f}s."
            )

    for current, following in zip(scheduled, scheduled[1:]):
        if current.end > following.absolute_start + TIMING_TOLERANCE:
            warnings.append(
                f'"{current.line.text}" overlaps "{following.line.text}" by '
                f"{current.end - following.absolute_start:.3f}s."
            )

    final_line = scheduled[-1]
    if final_line.end > output_duration + TIMING_TOLERANCE:
        warnings.append(
            f'Final slogan line "{final_line.line.text}" ends at '
            f"{final_line.end:.3f}s, after the video ends at "
            f"{output_duration:.3f}s."
        )

    voice_timeline_end = max(item.end for item in scheduled)
    if voice_timeline_end > output_duration + TIMING_TOLERANCE:
        warnings.append(
            f"Voice timeline ends at {voice_timeline_end:.3f}s, after the "
            f"video ends at {output_duration:.3f}s."
        )

    return warnings


def render_voice_timeline(
    scheduled: List[ScheduledLine],
    video_duration: float,
    timeline_path: Path,
) -> None:
    command = ["ffmpeg", "-y"]
    for item in scheduled:
        command.extend(["-i", str(item.path)])

    filters = []
    delayed_labels = []
    for index, item in enumerate(scheduled):
        delay_ms = round(item.absolute_start * 1000)
        label = f"voice{index}"
        delayed_labels.append(f"[{label}]")
        filters.append(
            f"[{index}:a]"
            f"aresample={AUDIO_SAMPLE_RATE},"
            f"adelay={delay_ms}:all=1"
            f"[{label}]"
        )

    filters.append(
        f"{''.join(delayed_labels)}"
        f"amix=inputs={len(scheduled)}:duration=longest:normalize=0,"
        f"apad,"
        f"atrim=duration={video_duration:.6f}"
        f"[voiceout]"
    )
    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[voiceout]",
            "-c:a",
            "aac",
            "-b:a",
            AUDIO_BITRATE,
            "-ar",
            str(AUDIO_SAMPLE_RATE),
            str(timeline_path),
        ]
    )

    print("\nRendering voiceover timeline...")
    subprocess.run(command, check=True)


def extend_final_frame(
    video_path: Path,
    extension_duration: float,
    extended_video_path: Path,
) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        f"tpad=stop_mode=clone:stop_duration={extension_duration:.6f}",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        str(extended_video_path),
    ]
    print(
        f"Extending the final frame by {extension_duration:.3f}s "
        "for the closing voiceover..."
    )
    subprocess.run(command, check=True)


def mux_voiceover(video_path: Path, timeline_path: Path, output_path: Path) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(timeline_path),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-shortest",
        str(output_path),
    ]
    print("Muxing voiceover with the master video...")
    subprocess.run(command, check=True)


def main() -> int:
    args = parse_args()
    video_path = resolve_project_path(args.video)
    voice_dir = resolve_project_path(args.voice_dir)
    output_path = resolve_project_path(args.output)
    scene_paths = [SCENES_DIR / filename for filename in SCENE_FILENAMES]
    voice_paths = [voice_dir / line.filename for line in VOICE_SCRIPT]

    try:
        displayed_voice_dir = voice_dir.relative_to(PROJECT_ROOT)
    except ValueError:
        displayed_voice_dir = voice_dir
    print(f"Voice pack: {voice_dir.name}")
    print(f"Voice directory: {displayed_voice_dir}")

    if not check_media_tools():
        return 2

    missing_scenes = [path for path in scene_paths if not path.is_file()]
    if missing_scenes:
        print("Missing input scene file(s):", file=sys.stderr)
        for path in missing_scenes:
            print(f"- {path}", file=sys.stderr)
        return 1

    missing_voice = [path for path in voice_paths if not path.is_file()]
    if missing_voice:
        print("Missing voice clip file(s):", file=sys.stderr)
        for path in missing_voice:
            print(f"- {path.name}", file=sys.stderr)
        return 1

    visual_result = build_silent_reel()
    if visual_result != 0:
        return visual_result

    if not video_path.is_file():
        print(
            f"Silent master video was not found after visual build: {video_path}",
            file=sys.stderr,
        )
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        scene_timings = calculate_scene_timings(scene_paths)
        scheduled = schedule_voice_lines(voice_dir, scene_timings)
        video_duration = probe_duration(video_path)
        print(f"\nMaster video duration: {video_duration:.3f}s")
        voice_timeline_end = max(item.end for item in scheduled)
        output_duration = max(
            video_duration,
            voice_timeline_end + FINAL_FRAME_PADDING,
        )
        extension_duration = output_duration - video_duration
        print(f"English reel duration: {output_duration:.3f}s")

        warnings = collect_warnings(scheduled, scene_timings, output_duration)
        if warnings:
            print("\nWarnings:", file=sys.stderr)
            for warning in warnings:
                print(f"WARNING: {warning}", file=sys.stderr)

        with tempfile.TemporaryDirectory(
            prefix="visitor_attention_voiceover_"
        ) as temp_dir:
            timeline_path = Path(temp_dir) / "voiceover_timeline.m4a"
            extended_video_path = Path(temp_dir) / "extended_video.mp4"
            render_voice_timeline(scheduled, output_duration, timeline_path)
            if extension_duration > TIMING_TOLERANCE:
                extend_final_frame(
                    video_path,
                    extension_duration,
                    extended_video_path,
                )
                mux_video_path = extended_video_path
            else:
                mux_video_path = video_path
            mux_voiceover(mux_video_path, timeline_path, output_path)
    except subprocess.CalledProcessError as error:
        print(
            f"Media command failed with exit code {error.returncode}.",
            file=sys.stderr,
        )
        return error.returncode

    print(f"\nEnglish reel created: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
