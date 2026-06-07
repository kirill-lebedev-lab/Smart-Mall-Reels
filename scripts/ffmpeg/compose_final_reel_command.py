from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ComposeFinalReelCommand:
    thumbnail_path: Path
    assembled_reel_path: Path
    music_path: Path
    output_path: Path
    filtergraph: str
    fps: int
    thumbnail_duration: float
    codec: str
    preset: str
    crf: str
    pixel_format: str
    audio_codec: str
    audio_bitrate: str

    @property
    def argv(self) -> list[str]:
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
            str(self.fps),
            "-c:v",
            self.codec,
            "-preset",
            self.preset,
            "-crf",
            self.crf,
            "-pix_fmt",
            self.pixel_format,
            "-c:a",
            self.audio_codec,
            "-b:a",
            self.audio_bitrate,
            str(self.output_path),
        ]
