from dataclasses import dataclass

from camera.camera_control_point import CameraControlPoint
from camera.camera_state import CameraState


@dataclass(frozen=True)
class BezierCameraPath:
    control_points: list[CameraControlPoint]

    def __post_init__(self) -> None:
        if len(self.control_points) not in (3, 4):
            raise ValueError(
                "BezierCameraPath requires three or four control points."
            )

        previous_progress = None
        for control_point in self.control_points:
            if not 0.0 <= control_point.progress <= 1.0:
                raise ValueError(
                    "Control point progress must be between 0.0 and 1.0."
                )
            if (
                previous_progress is not None
                and control_point.progress <= previous_progress
            ):
                raise ValueError(
                    "Control points must have unique progress values "
                    "in ascending order."
                )
            previous_progress = control_point.progress

        if self.control_points[0].progress != 0.0:
            raise ValueError("The first control point must have progress 0.0.")
        if self.control_points[-1].progress != 1.0:
            raise ValueError("The last control point must have progress 1.0.")

    def state_at_progress(self, progress: float) -> CameraState:
        progress = max(0.0, min(progress, 1.0))

        if progress <= 0.0:
            return self.control_points[0].camera
        if progress >= 1.0:
            return self.control_points[-1].camera

        eased = progress * progress * (3 - 2 * progress)
        curve_position = self._curve_position_at_progress(eased)

        return CameraState(
            zoom=self._bezier_value(
                [
                    control_point.camera.zoom
                    for control_point in self.control_points
                ],
                curve_position,
            ),
            x=self._bezier_value(
                [
                    control_point.camera.x
                    for control_point in self.control_points
                ],
                curve_position,
            ),
            y_focus=self._bezier_value(
                [
                    control_point.camera.y_focus
                    for control_point in self.control_points
                ],
                curve_position,
            ),
        )

    def _curve_position_at_progress(self, progress: float) -> float:
        progress_points = [
            control_point.progress
            for control_point in self.control_points
        ]
        low = 0.0
        high = 1.0

        for _ in range(32):
            middle = (low + high) / 2
            curve_progress = self._bezier_value(
                progress_points,
                middle,
            )
            if curve_progress < progress:
                low = middle
            else:
                high = middle

        return (low + high) / 2

    @staticmethod
    def _bezier_value(points: list[float], progress: float) -> float:
        values = points[:]

        while len(values) > 1:
            values = [
                left + (right - left) * progress
                for left, right in zip(values, values[1:])
            ]

        return values[0]
