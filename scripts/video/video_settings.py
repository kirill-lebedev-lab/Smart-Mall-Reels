from dataclasses import dataclass

from video.frame_settings import FrameSettings


@dataclass(frozen=True)
class VideoSettings:
    frame: FrameSettings
    fps: int
    codec: str
    preset: str
    crf: str
    pixel_format: str = "yuv420p"
