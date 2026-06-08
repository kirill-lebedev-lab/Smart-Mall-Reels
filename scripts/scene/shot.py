from dataclasses import dataclass

from camera.camera_path import CameraPath


@dataclass(frozen=True)
class Shot:
    duration: float
    camera_path: CameraPath
