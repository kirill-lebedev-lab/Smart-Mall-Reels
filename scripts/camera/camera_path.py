from typing import Protocol

from camera.camera_state import CameraState


class CameraPath(Protocol):
    def state_at(self, index: int, total_frames: int) -> CameraState:
        ...
