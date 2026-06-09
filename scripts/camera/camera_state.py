from dataclasses import dataclass


@dataclass(frozen=True)
class CameraState:
    """Camera state with x measured in source image coordinates."""

    zoom: float
    x: float
    y_focus: float
