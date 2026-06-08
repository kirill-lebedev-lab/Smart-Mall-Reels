from dataclasses import dataclass

from camera.camera_state import CameraState


@dataclass(frozen=True)
class LinearCameraPath:
    start: CameraState
    end: CameraState

    def state_at_progress(self, progress: float) -> CameraState:
        progress = max(0.0, min(progress, 1.0))
        eased = progress * progress * (3 - 2 * progress)

        return CameraState(
            zoom=self.start.zoom + (self.end.zoom - self.start.zoom) * eased,
            x=self.start.x + (self.end.x - self.start.x) * eased,
            y_focus=(
                self.start.y_focus
                + (self.end.y_focus - self.start.y_focus) * eased
            ),
        )
