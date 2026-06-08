from typing import Protocol

from camera.camera_state import CameraState


class CameraPath(Protocol):
    def state_at_progress(self, progress: float) -> CameraState:
        ...
