# Scene Generation Framework

The `scripts` directory contains the shot-based framework used to generate the
Smart Mall cinematic reels. It converts still source images into camera-driven
scenes, encodes the rendered frames, and assembles the resulting videos.

## Architecture

- `Scene` describes a source image, an ordered list of shots, and video
  settings.
- `Shot` is one logical section of camera motion with its own duration and
  `CameraPath`.
- `CameraState` describes camera zoom, horizontal viewport position, and
  vertical focus. Its `x` value is measured in source-image coordinates.
- `CameraPath` resolves a `CameraState` from normalized shot progress.
- `LinearCameraPath` interpolates between two camera states with smooth easing.
- `BezierCameraPath` creates a continuous quadratic or cubic camera trajectory.
- `CameraControlPoint` defines the camera states used to shape a Bezier path.
- `SceneFrameRenderer` resolves scene time and camera state, then renders
  frames from the source image.
- `EncodeVideoCommand` builds the ffmpeg encoding command.
- `FfmpegVideoOutput` streams rendered frames to ffmpeg.

## Pipeline

```text
Scene
  -> SceneFrameRenderer
  -> rendered frames
  -> FfmpegVideoOutput
  -> ffmpeg encoded video
```

## Build Scripts

- `mall_navigation/build_scene_001.py` through
  `mall_navigation/build_scene_009.py` render individual scenes.
- `mall_navigation/build_navigation_reel.py` assembles the navigation reel.
- `mall_navigation/build_thumbnail.py` builds the reel thumbnail.
- `mall_navigation/generate_thumbnails.py` generates source-image previews.

Run scene scripts from the project root:

```bash
python scripts/mall_navigation/build_scene_001.py
python scripts/mall_navigation/build_scene_001.py --input custom.png --output custom.mp4
```
