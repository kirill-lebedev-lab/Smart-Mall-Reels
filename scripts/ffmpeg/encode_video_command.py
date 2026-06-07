from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EncodeVideoCommand:
    output_path: Path
    width: int
    height: int
    fps: int
    frame_count: int
    codec: str
    preset: str
    crf: str
    input_pixel_format: str = "rgb24"
    output_pixel_format: str = "yuv420p"

    @property
    def argv(self) -> list[str]:
        return [
            "ffmpeg",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            self.input_pixel_format,
            "-s",
            f"{self.width}x{self.height}",
            "-r",
            str(self.fps),
            "-i",
            "-",
            "-frames:v",
            str(self.frame_count),
            "-c:v",
            self.codec,
            "-preset",
            self.preset,
            "-crf",
            self.crf,
            "-pix_fmt",
            self.output_pixel_format,
            str(self.output_path),
        ]
