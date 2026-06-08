from types import TracebackType
from typing import Optional, Type

from PIL import Image

from camera.camera_state import CameraState
from scene.scene import Scene


class SceneFrameRenderer:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.source: Optional[Image.Image] = None

    def __enter__(self) -> "SceneFrameRenderer":
        self.source = Image.open(self.scene.source_path).convert("RGB")
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        if self.source is not None:
            self.source.close()
            self.source = None

    def frames(self):
        for index in range(self.scene.frame_count):
            yield self.render_frame(index)

    def render_frame(self, index: int) -> Image.Image:
        if self.source is None:
            raise RuntimeError("SceneFrameRenderer is not open.")

        camera = self.scene.camera_path.state_at(
            index,
            self.scene.frame_count,
        )
        return self.render_frame_from_camera(camera)

    def render_frame_from_camera(self, camera: CameraState) -> Image.Image:
        if self.source is None:
            raise RuntimeError("SceneFrameRenderer is not open.")

        frame_settings = self.scene.video_settings.frame

        scale = (frame_settings.height / self.source.height) * camera.zoom

        scaled_width = self.source.width * scale
        scaled_height = self.source.height * scale

        x = camera.x
        y = (scaled_height - frame_settings.height) * camera.y_focus

        x = max(0.0, min(x, scaled_width - frame_settings.width))
        y = max(0.0, min(y, scaled_height - frame_settings.height))

        crop_box = (
            x / scale,
            y / scale,
            (x + frame_settings.width) / scale,
            (y + frame_settings.height) / scale,
        )

        return self.source.transform(
            (frame_settings.width, frame_settings.height),
            Image.Transform.EXTENT,
            crop_box,
            Image.Resampling.BICUBIC,
        )