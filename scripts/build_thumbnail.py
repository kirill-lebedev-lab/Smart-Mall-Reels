#!/usr/bin/env python3
import subprocess
import sys
import tempfile
from pathlib import Path

from generate_thumbnails import generate_thumbnails


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
FPS = 30
THUMBNAIL_DURATION = 1.5
DISSOLVE_DURATION = 0.65
VIDEO_CODEC = "libx264"
PIXEL_FORMAT = "yuv420p"
CRF = "18"
PRESET = "slow"
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "192k"

THUMBNAIL_VIDEOS = {
    "en": PROJECT_ROOT / "output/thumbnail_navigation_en.mp4",
    "ru": PROJECT_ROOT / "output/thumbnail_navigation_ru.mp4",
}


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


def build_thumbnail_video_command(thumbnail_path: Path, output_path: Path) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-t",
        f"{THUMBNAIL_DURATION:.3f}",
        "-i",
        str(thumbnail_path),
        "-vf",
        (
            f"fps={FPS},"
            f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={OUTPUT_WIDTH}:{OUTPUT_HEIGHT},"
            f"setsar=1,"
            f"format={PIXEL_FORMAT}"
        ),
        "-r",
        str(FPS),
        "-frames:v",
        str(round(THUMBNAIL_DURATION * FPS)),
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


def build_thumbnail_video(thumbnail_path: Path, output_path: Path) -> None:
    if not thumbnail_path.exists():
        raise FileNotFoundError(f"Missing thumbnail file: {thumbnail_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(build_thumbnail_video_command(thumbnail_path, output_path), check=True)
    print(f"Thumbnail video created: {output_path.resolve()}")


def build_thumbnail_videos(thumbnail_paths: dict[str, Path]) -> dict[str, Path]:
    outputs = {}
    for language, thumbnail_path in thumbnail_paths.items():
        output_path = THUMBNAIL_VIDEOS[language]
        build_thumbnail_video(thumbnail_path, output_path)
        outputs[language] = output_path
    return outputs


def prepend_thumbnail(
    video_path: Path,
    thumbnail_path: Path,
    music_path: Path,
    music_volume: float,
    music_fade_in: float,
    music_fade_out: float,
) -> None:
    if not video_path.exists():
        raise FileNotFoundError(f"Missing video file: {video_path}")
    if not thumbnail_path.exists():
        raise FileNotFoundError(f"Missing thumbnail file: {thumbnail_path}")
    if not music_path.exists():
        raise FileNotFoundError(f"Missing background music file: {music_path}")

    total_duration = THUMBNAIL_DURATION + probe_duration(video_path) - DISSOLVE_DURATION
    dissolve_offset = THUMBNAIL_DURATION - DISSOLVE_DURATION
    fade_out_duration = min(music_fade_out, total_duration)
    fade_out_start = max(0.0, total_duration - fade_out_duration)
    filtergraph = (
        f"[0:v]fps={FPS},scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT},"
        f"setsar=1,trim=duration={THUMBNAIL_DURATION:.3f},"
        f"setpts=PTS-STARTPTS[cover];"
        f"[1:v]fps={FPS},scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT},"
        f"setsar=1,setpts=PTS-STARTPTS[reel];"
        f"[cover][reel]xfade=transition=fade:"
        f"duration={DISSOLVE_DURATION:.3f}:"
        f"offset={dissolve_offset:.3f}[vout];"
        f"[2:a]atrim=duration={total_duration:.3f},"
        f"asetpts=PTS-STARTPTS,"
        f"volume={music_volume:.2f},"
        f"afade=t=in:st=0:d={music_fade_in:.3f},"
        f"afade=t=out:st={fade_out_start:.3f}:d={fade_out_duration:.3f}"
        f"[aout]"
    )

    with tempfile.NamedTemporaryFile(
        prefix=f".{video_path.stem}_", suffix=".mp4", dir=video_path.parent, delete=False
    ) as temp_file:
        temp_path = Path(temp_file.name)

    command = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-t",
        f"{THUMBNAIL_DURATION:.3f}",
        "-i",
        str(thumbnail_path),
        "-i",
        str(video_path),
        "-stream_loop",
        "-1",
        "-i",
        str(music_path),
        "-filter_complex",
        filtergraph,
        "-map",
        "[vout]",
        "-map",
        "[aout]",
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
        "-c:a",
        AUDIO_CODEC,
        "-b:a",
        AUDIO_BITRATE,
        str(temp_path),
    ]

    try:
        subprocess.run(command, check=True)
        temp_path.chmod(0o644)
        temp_path.replace(video_path)
    finally:
        temp_path.unlink(missing_ok=True)


def main() -> int:
    try:
        thumbnail_paths = generate_thumbnails()
        build_thumbnail_videos(thumbnail_paths)
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as error:
        print(f"ffmpeg failed with exit code {error.returncode}.", file=sys.stderr)
        return error.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
