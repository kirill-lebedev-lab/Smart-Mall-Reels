from dataclasses import dataclass
from pathlib import Path

from scene.shot import Shot
from video.video_settings import VideoSettings


@dataclass(frozen=True)
class Scene:
    source_path: Path
    shots: list[Shot]
    video_settings: VideoSettings

    def __post_init__(self) -> None:
        if not self.shots:
            raise ValueError("Scene must contain at least one shot.")
        if any(shot.duration <= 0 for shot in self.shots):
            raise ValueError("Scene shots must have positive duration.")

    @property
    def duration(self) -> float:
        return sum(shot.duration for shot in self.shots)

    @property
    def frame_count(self) -> int:
        return int(round(self.duration * self.video_settings.fps))

    def shot_at_time(self, time: float) -> tuple[Shot, float]:
        if time <= 0:
            return self.shots[0], 0.0

        elapsed = 0.0
        for shot in self.shots:
            shot_end = elapsed + shot.duration
            if time < shot_end:
                return shot, time - elapsed
            elapsed = shot_end

        return self.shots[-1], self.shots[-1].duration
