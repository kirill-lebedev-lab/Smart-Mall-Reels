from dataclasses import dataclass
from pathlib import Path

from camera.linear_camera_path import LinearCameraPath
from video.video_settings import VideoSettings


@dataclass(frozen=True)
class Scene:
    source_path: Path
    duration: float
    camera_path: LinearCameraPath
    video_settings: VideoSettings
