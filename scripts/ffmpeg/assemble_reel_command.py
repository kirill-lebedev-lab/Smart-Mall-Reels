from dataclasses import dataclass
from pathlib import Path

from video.video_settings import VideoSettings


@dataclass(frozen=True)
class AssembleReelCommand:
    scene_paths: list[Path]
    output_path: Path
    filtergraph: str
    video_settings: VideoSettings

    @property
    def argv(self) -> list[str]:
        settings = self.video_settings
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
                str(settings.fps),
                "-c:v",
                settings.codec,
                "-preset",
                settings.preset,
                "-crf",
                settings.crf,
                "-pix_fmt",
                settings.pixel_format,
                str(self.output_path),
            ]
        )
        return command
