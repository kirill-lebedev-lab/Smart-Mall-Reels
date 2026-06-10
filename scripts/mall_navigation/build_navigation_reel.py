#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

try:
    from .paths import AUDIO_DIR, OUTPUT_DIR, SCENES_DIR
except ImportError:
    from paths import AUDIO_DIR, OUTPUT_DIR, SCENES_DIR

from ffmpeg.assemble_reel_command import AssembleReelCommand
from ffmpeg.compose_final_reel_command import ComposeFinalReelCommand
try:
    from .generate_thumbnails import generate_thumbnails
except ImportError:
    from generate_thumbnails import generate_thumbnails
from video.frame_settings import FrameSettings
from video.video_settings import VideoSettings


# Reel inputs and output.
SCENES = [
    SCENES_DIR / "scene_001.mp4",
    SCENES_DIR / "scene_002.mp4",
    SCENES_DIR / "scene_003.mp4",
    SCENES_DIR / "scene_004.mp4",
    SCENES_DIR / "scene_005.mp4",
    SCENES_DIR / "scene_006.mp4",
    SCENES_DIR / "scene_007.mp4",
    SCENES_DIR / "scene_008.mp4",
    SCENES_DIR / "scene_009.mp4",
]
OUTPUT_PATH = OUTPUT_DIR / "mall_navigation_reel_v01.mp4"
RUSSIAN_OUTPUT_PATH = OUTPUT_DIR / "mall_navigation_reel_rus_v01.mp4"
NO_TEXT_OUTPUT_PATH = OUTPUT_DIR / "mall_navigation_reel_v01_no_text.mp4"
MUSIC_PATH = AUDIO_DIR / "Glass Atrium Drift.mp3"

# Video and transition settings.
FPS = 30
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920
TRANSITION_DURATION = 0.5
THUMBNAIL_DURATION = 1.5
DISSOLVE_DURATION = 0.65
VIDEO_CODEC = "libx264"
PIXEL_FORMAT = "yuv420p"
CRF = "18"
PRESET = "slow"

# Background music settings.
MUSIC_VOLUME = 0.52
MUSIC_FADE_IN = 1.0
MUSIC_FADE_OUT = 1.75
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "192k"

# Caption settings.
FONT_FAMILY = "Avenir Next Medium"
TEXT_COLOR = "0xFFF6DC"
SHADOW_COLOR = "0x000000"
CAPTION_FADE = 0.65
CAPTIONS = [
    {
        "text": "The mall notices you",
        "start": 1.2,
        "end": 5.0,
        "font_size": 74,
        "x": "(w-text_w)/2",
        "y": "h*0.815",
    },
    {
        "text": "Space begins to respond",
        "start": 9.0,
        "end": 12.0,
        "font_size": 70,
        "x": "(w-text_w)/2",
        "y": "h*0.815",
    },
    {
        "text": "Smart Mall",
        "start": 32.1,
        "end": 36.2,
        "font_size": 122,
        "x": "(w-text_w)/2",
        "y": "h*0.382",
        "border_width": 2,
        "fade_out": False,
    },
    {
        "text": "Space that responds to people",
        "start": 32.45,
        "end": 36.2,
        "font_size": 66,
        "x": "(w-text_w)/2",
        "y": "h*0.462",
        "border_width": 2,
        "fade_out": False,
    },
]
RUSSIAN_CAPTIONS = [
    {**CAPTIONS[0], "text": "Молл замечает вас"},
    {**CAPTIONS[1], "text": "Пространство начинает", "y": "h*0.775"},
    {**CAPTIONS[1], "text": "реагировать", "y": "h*0.825"},
    {**CAPTIONS[2], "text": "Умный молл"},
    {**CAPTIONS[3], "text": "Пространство, которое", "y": "h*0.455"},
    {**CAPTIONS[3], "text": "реагирует на людей", "y": "h*0.500"},
]

def check_input_scenes(scene_paths: list[Path]) -> None:
    missing = [path for path in scene_paths if not path.exists()]
    if missing:
        missing_list = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Missing input scene(s):\n{missing_list}")


def check_music_file(music_path: Path) -> None:
    if not music_path.exists():
        raise FileNotFoundError(f"Missing background music file: {music_path}")


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


def escape_drawtext_text(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace(",", "\\,")
    )


def escape_drawtext_expression(expression: str) -> str:
    return expression.replace(",", "\\,")


def caption_alpha_expression(start: float, end: float, fade_out: bool = True) -> str:
    fade = CAPTION_FADE
    if fade_out:
        expression = (
            f"if(lt(t,{start:.3f}),0,"
            f"if(lt(t,{start + fade:.3f}),(t-{start:.3f})/{fade:.3f},"
            f"if(lt(t,{end - fade:.3f}),0.92,"
            f"if(lt(t,{end:.3f}),0.92*(1-(t-{end - fade:.3f})/{fade:.3f}),0))))"
        )
    else:
        expression = (
            f"if(lt(t,{start:.3f}),0,"
            f"if(lt(t,{start + fade:.3f}),(t-{start:.3f})/{fade:.3f},0.92))"
        )
    return escape_drawtext_expression(expression)


def build_caption_filter(captions: list[dict]) -> str:
    if not captions:
        return "[reel]null[captioned_reel]"

    filters = ["[reel]null[cap0]"]

    for index, caption in enumerate(captions):
        input_label = f"cap{index}"
        output_label = (
            "captioned_reel"
            if index == len(captions) - 1
            else f"cap{index + 1}"
        )
        text = escape_drawtext_text(caption["text"])
        alpha = caption_alpha_expression(
            caption["start"], caption["end"], caption.get("fade_out", True)
        )
        border_width = caption.get("border_width", 1)
        border_opacity = caption.get("border_opacity", 0.22)
        shadow_opacity = caption.get("shadow_opacity", 0.42)
        enable = escape_drawtext_expression(
            f"between(t,{caption['start']:.3f},{caption['end']:.3f})"
        )
        filters.append(
            f"[{input_label}]"
            f"drawtext="
            f"font='{FONT_FAMILY}':"
            f"text='{text}':"
            f"fontsize={caption['font_size']}:"
            f"fontcolor={TEXT_COLOR}:"
            f"alpha='{alpha}':"
            f"x={caption['x']}:"
            f"y={caption['y']}:"
            f"bordercolor={SHADOW_COLOR}@{border_opacity}:"
            f"borderw={border_width}:"
            f"shadowcolor={SHADOW_COLOR}@{shadow_opacity}:"
            f"shadowx=0:"
            f"shadowy=3:"
            f"enable='{enable}'"
            f"[{output_label}]"
        )

    return ";".join(filters)


def build_final_reel_filtergraph(
    assembled_reel_duration: float,
    captions: list[dict],
) -> str:
    total_duration = (
        THUMBNAIL_DURATION + assembled_reel_duration - DISSOLVE_DURATION
    )
    dissolve_offset = THUMBNAIL_DURATION - DISSOLVE_DURATION
    fade_out_duration = min(MUSIC_FADE_OUT, total_duration)
    fade_out_start = max(0.0, total_duration - fade_out_duration)

    video_filters = (
        f"[0:v]fps={FPS},scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT},"
        f"setsar=1,trim=duration={THUMBNAIL_DURATION:.3f},"
        f"setpts=PTS-STARTPTS[cover];"
        f"[1:v]fps={FPS},scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT},"
        f"setsar=1,setpts=PTS-STARTPTS[reel];"
        f"{build_caption_filter(captions)};"
        f"[cover][captioned_reel]xfade=transition=fade:"
        f"duration={DISSOLVE_DURATION:.3f}:"
        f"offset={dissolve_offset:.3f}[vout]"
    )
    audio_filter = (
        f"[2:a]atrim=duration={total_duration:.3f},"
        f"asetpts=PTS-STARTPTS,"
        f"volume={MUSIC_VOLUME:.2f},"
        f"afade=t=in:st=0:d={MUSIC_FADE_IN:.3f},"
        f"afade=t=out:st={fade_out_start:.3f}:d={fade_out_duration:.3f}"
        f"[aout]"
    )
    return f"{video_filters};{audio_filter}"


def main() -> int:
    scene_paths = SCENES
    output_path = OUTPUT_PATH
    russian_output_path = RUSSIAN_OUTPUT_PATH
    no_text_output_path = NO_TEXT_OUTPUT_PATH
    music_path = MUSIC_PATH

    try:
        check_input_scenes(scene_paths)
        check_music_file(music_path)
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
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

    print("Running ffmpeg...")
    try:
        scene_durations = [probe_duration(path) for path in scene_paths]
        filtergraph = build_filtergraph(len(scene_paths), scene_durations)
        assemble_command = AssembleReelCommand(
            scene_paths=scene_paths,
            output_path=no_text_output_path,
            filtergraph=filtergraph,
            video_settings=video_settings,
        )
        subprocess.run(assemble_command.argv, check=True)

        assembled_reel_duration = probe_duration(no_text_output_path)
        thumbnail_paths = generate_thumbnails()
        final_filtergraph = build_final_reel_filtergraph(
            assembled_reel_duration,
            CAPTIONS,
        )
        compose_command = ComposeFinalReelCommand(
            thumbnail_path=thumbnail_paths["en"],
            assembled_reel_path=no_text_output_path,
            music_path=music_path,
            output_path=output_path,
            filtergraph=final_filtergraph,
            thumbnail_duration=THUMBNAIL_DURATION,
            video_settings=video_settings,
            audio_codec=AUDIO_CODEC,
            audio_bitrate=AUDIO_BITRATE,
        )
        subprocess.run(compose_command.argv, check=True)

        russian_final_filtergraph = build_final_reel_filtergraph(
            assembled_reel_duration,
            RUSSIAN_CAPTIONS,
        )
        russian_compose_command = ComposeFinalReelCommand(
            thumbnail_path=thumbnail_paths["ru"],
            assembled_reel_path=no_text_output_path,
            music_path=music_path,
            output_path=russian_output_path,
            filtergraph=russian_final_filtergraph,
            thumbnail_duration=THUMBNAIL_DURATION,
            video_settings=video_settings,
            audio_codec=AUDIO_CODEC,
            audio_bitrate=AUDIO_BITRATE,
        )
        subprocess.run(russian_compose_command.argv, check=True)
    except FileNotFoundError as error:
        if error.filename in {"ffmpeg", "ffprobe"}:
            print(
                "ffmpeg or ffprobe was not found. Please install ffmpeg and try again.",
                file=sys.stderr,
            )
            return 2
        print(error, file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as error:
        print(f"ffmpeg failed with exit code {error.returncode}.", file=sys.stderr)
        return error.returncode

    print(f"Reel created: {output_path.resolve()}")
    print(f"Russian reel created: {russian_output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
