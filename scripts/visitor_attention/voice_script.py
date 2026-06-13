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
            "ElevenLabs_2026-06-13T20_12_45_"
            "George Daigle - Charismatic and Crisp_pvc_sp86_s29_sb75_v3.mp3"
        ),
        start_offset=0.60,
    ),
    VoiceLine(
        scene="scene_002.mp4",
        text="Pushy sales are annoying.",
        filename=(
            "ElevenLabs_2026-06-13T20_33_50_"
            "George Daigle - Charismatic and Crisp_pvc_sp86_s29_sb75_v3.mp3"
        ),
        start_offset=0.55,
    ),
    VoiceLine(
        scene="scene_003.mp4",
        text="People are tired of pressure.",
        filename=(
            "ElevenLabs_2026-06-13T20_28_18_"
            "George Daigle - Charismatic and Crisp_pvc_sp86_s29_sb75_v3.mp3"
        ),
        start_offset=0.45,
    ),
    VoiceLine(
        scene="scene_004.mp4",
        text="But they immediately notice themselves.",
        filename=(
            "ElevenLabs_2026-06-13T20_16_49_"
            "George Daigle - Charismatic and Crisp_pvc_sp86_s29_sb75_v3.mp3"
        ),
        start_offset=0.80,
    ),
    VoiceLine(
        scene="scene_005.mp4",
        text="Smart Mirror.",
        filename=(
            "ElevenLabs_2026-06-13T20_17_38_"
            "George Daigle - Charismatic and Crisp_pvc_sp86_s29_sb75_v3.mp3"
        ),
        start_offset=0.90,
    ),
    VoiceLine(
        scene="scene_005.mp4",
        text="Smart Mall.",
        filename=(
            "ElevenLabs_2026-06-13T20_18_05_"
            "George Daigle - Charismatic and Crisp_pvc_sp86_s29_sb75_v3.mp3"
        ),
        start_offset=2.05,
    ),
    VoiceLine(
        scene="scene_005.mp4",
        text="Designed around people.",
        filename=(
            "ElevenLabs_2026-06-13T20_18_48_"
            "George Daigle - Charismatic and Crisp_pvc_sp86_s29_sb75_v3.mp3"
        ),
        start_offset=3.15,
    ),
]
