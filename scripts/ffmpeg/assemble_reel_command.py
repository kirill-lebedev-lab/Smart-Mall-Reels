from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AssembleReelCommand:
    scene_paths: list[Path]
    output_path: Path
    filtergraph: str
    fps: int
    codec: str
    preset: str
    crf: str
    pixel_format: str

    @property
    def argv(self) -> list[str]:
        command = ["ffmpeg", "-y"]
        for path in self.scene_paths:
            command.extend(["-i", str(path)])

        command.extend(
            [
                "-filter_complex",
                self.filtergraph,
                "-map",
                "[vout]",
                "-r",
                str(self.fps),
                "-c:v",
                self.codec,
                "-preset",
                self.preset,
                "-crf",
                self.crf,
                "-pix_fmt",
                self.pixel_format,
                str(self.output_path),
            ]
        )
        return command
