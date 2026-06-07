from dataclasses import dataclass

from camera.camera_state import CameraState


@dataclass(frozen=True)
class LinearCameraPath:
    start: CameraState
    end: CameraState

    def state_at(self, index: int, total_frames: int) -> CameraState:
        progress = 0 if total_frames == 1 else index / (total_frames - 1)
        eased = progress * progress * (3 - 2 * progress)

        return CameraState(
            zoom=self.start.zoom + (self.end.zoom - self.start.zoom) * eased,
            x=self.start.x + (self.end.x - self.start.x) * eased,
            y_focus=(
                self.start.y_focus
                + (self.end.y_focus - self.start.y_focus) * eased
            ),
        )
