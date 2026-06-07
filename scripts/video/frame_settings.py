from dataclasses import dataclass


@dataclass(frozen=True)
class FrameSettings:
    width: int
    height: int
    pixel_format: str = "rgb24"
