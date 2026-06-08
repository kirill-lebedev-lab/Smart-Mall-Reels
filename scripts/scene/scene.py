from dataclasses import dataclass
from pathlib import Path

from camera.camera_path import CameraPath
from video.video_settings import VideoSettings


@dataclass(frozen=True)
class Scene:
    source_path: Path
    duration: float
    camera_path: CameraPath
    video_settings: VideoSettings

    @property
    def frame_count(self) -> int:
        return int(round(self.duration * self.video_settings.fps))
