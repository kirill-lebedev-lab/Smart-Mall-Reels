from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceLine:
    scene: str
    text: str
    filename: str
    start_offset: float


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
        start_offset=0.60,
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
        start_offset=0.80,
    ),
    VoiceLine(
        scene="scene_005.mp4",
        text="Smart Mirror.",
        filename=(
            "ElevenLabs_2026-06-13T10_52_14_"
            "Josh - Teacher for Kids_pvc_sp100_s50_sb75_v3.mp3"
        ),
        start_offset=0.90,
    ),
    VoiceLine(
        scene="scene_005.mp4",
        text="Smart Mall.",
        filename=(
            "ElevenLabs_2026-06-13T10_52_38_"
            "Josh - Teacher for Kids_pvc_sp100_s50_sb75_v3.mp3"
        ),
        start_offset=2.05,
    ),
    VoiceLine(
        scene="scene_005.mp4",
        text="Designed around people.",
        filename=(
            "ElevenLabs_2026-06-13T10_53_08_"
            "Josh - Teacher for Kids_pvc_sp100_s50_sb75_v3.mp3"
        ),
        start_offset=3.15,
    ),
]
