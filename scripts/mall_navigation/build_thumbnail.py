#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

from PIL import Image

try:
    from .paths import OUTPUT_DIR
except ImportError:
    from paths import OUTPUT_DIR

from ffmpeg.encode_video_command import EncodeVideoCommand
from ffmpeg.ffmpeg_video_output import FfmpegVideoOutput
try:
    from .generate_thumbnails import generate_thumbnails
except ImportError:
    from generate_thumbnails import generate_thumbnails
from video.frame_settings import FrameSettings
from video.video_settings import VideoSettings


OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
FPS = 30
THUMBNAIL_DURATION = 1.5
VIDEO_CODEC = "libx264"
PIXEL_FORMAT = "yuv420p"
CRF = "18"
PRESET = "slow"

THUMBNAIL_VIDEOS = {
    "en": OUTPUT_DIR / "thumbnail_navigation_en.mp4",
    "ru": OUTPUT_DIR / "thumbnail_navigation_ru.mp4",
}


def render_thumbnail_frames(thumbnail_path: Path, total_frames: int):
    with Image.open(thumbnail_path) as source:
        frame = source.convert("RGB")

    if frame.size != (OUTPUT_WIDTH, OUTPUT_HEIGHT):
        scale = max(OUTPUT_WIDTH / frame.width, OUTPUT_HEIGHT / frame.height)
        scaled_width = round(frame.width * scale)
        scaled_height = round(frame.height * scale)
        frame = frame.resize(
            (scaled_width, scaled_height),
            Image.Resampling.LANCZOS,
        )
        left = (scaled_width - OUTPUT_WIDTH) // 2
        top = (scaled_height - OUTPUT_HEIGHT) // 2
        frame = frame.crop(
            (left, top, left + OUTPUT_WIDTH, top + OUTPUT_HEIGHT)
        )

    for _ in range(total_frames):
        yield frame


def build_thumbnail_video(thumbnail_path: Path, output_path: Path) -> None:
    if not thumbnail_path.exists():
        raise FileNotFoundError(f"Missing thumbnail file: {thumbnail_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_frames = round(THUMBNAIL_DURATION * FPS)
    video_settings = VideoSettings(
        frame=FrameSettings(width=OUTPUT_WIDTH, height=OUTPUT_HEIGHT),
        fps=FPS,
        codec=VIDEO_CODEC,
        preset=PRESET,
        crf=CRF,
        pixel_format=PIXEL_FORMAT,
    )
    command = EncodeVideoCommand(
        output_path=output_path,
        frame_count=total_frames,
        video_settings=video_settings,
    )

    with FfmpegVideoOutput(command) as output:
        for frame in render_thumbnail_frames(thumbnail_path, total_frames):
            output.write(frame)

    print(f"Thumbnail video created: {output_path.resolve()}")


def build_thumbnail_videos(thumbnail_paths: dict[str, Path]) -> dict[str, Path]:
    outputs = {}
    for language, thumbnail_path in thumbnail_paths.items():
        output_path = THUMBNAIL_VIDEOS[language]
        build_thumbnail_video(thumbnail_path, output_path)
        outputs[language] = output_path
    return outputs


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
