from dataclasses import dataclass
from pathlib import Path

from video.video_settings import VideoSettings


@dataclass(frozen=True)
class ComposeFinalReelCommand:
    thumbnail_path: Path
    assembled_reel_path: Path
    music_path: Path
    output_path: Path
    filtergraph: str
    thumbnail_duration: float
    video_settings: VideoSettings
    audio_codec: str
    audio_bitrate: str

    @property
    def argv(self) -> list[str]:
        settings = self.video_settings

        return [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-t",
            f"{self.thumbnail_duration:.3f}",
            "-i",
            str(self.thumbnail_path),
            "-i",
            str(self.assembled_reel_path),
            "-stream_loop",
            "-1",
            "-i",
            str(self.music_path),
            "-filter_complex",
            self.filtergraph,
            "-map",
            "[vout]",
            "-map",
            "[aout]",
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
            "-c:a",
            self.audio_codec,
            "-b:a",
            self.audio_bitrate,
            str(self.output_path),
        ]
