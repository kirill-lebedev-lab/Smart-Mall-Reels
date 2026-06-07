from dataclasses import dataclass


@dataclass(frozen=True)
class CameraState:
    zoom: float
    x: float
    y_focus: float
