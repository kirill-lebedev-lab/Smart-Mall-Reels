from dataclasses import dataclass
from pathlib import Path

from video.video_settings import VideoSettings


@dataclass(frozen=True)
class EncodeVideoCommand:
    output_path: Path
    frame_count: int
    video_settings: VideoSettings

    @property
    def argv(self) -> list[str]:
        frame = self.video_settings.frame

        return [
            "ffmpeg",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            frame.pixel_format,
            "-s",
            f"{frame.width}x{frame.height}",
            "-r",
            str(self.video_settings.fps),
            "-i",
            "-",
            "-frames:v",
            str(self.frame_count),
            "-c:v",
            self.video_settings.codec,
            "-preset",
            self.video_settings.preset,
            "-crf",
            self.video_settings.crf,
            "-pix_fmt",
            self.video_settings.pixel_format,
            str(self.output_path),
        ]
