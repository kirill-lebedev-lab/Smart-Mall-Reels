from dataclasses import dataclass

from camera.camera_state import CameraState


@dataclass(frozen=True)
class CameraControlPoint:
    progress: float
    camera: CameraState
