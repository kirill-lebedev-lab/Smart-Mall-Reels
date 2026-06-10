# Smart Mall Cinematic Reels

This directory contains a framework for generating cinematic, shot-based videos
for the Smart Mall concept. It turns still architectural and interaction
visualizations into vertical cinematic reels driven by deliberate camera
movement.

Learn more about the concept on the
[Smart Mall website](https://kirill-lebedev-lab.github.io/smart-mall/).

The videos explore distributed navigation and digital interaction inside a
future mall: visitors discover route information, inspect interactive screens,
make decisions, and move through the architecture. Camera-driven storytelling
connects these moments into short scenes that communicate both spatial design
and the intended user experience.

The framework provides reusable scene, shot, camera, rendering, and encoding
components so navigation and interaction sequences can be authored as
structured cinematic motion rather than one-off frame calculations.

## Architecture

- `Scene` describes a source image, an ordered list of shots, and video
  settings.
- `Shot` is one logical section of camera motion with its own duration and
  `CameraPath`.
- `CameraState` describes camera zoom, horizontal viewport position, and
  vertical focus. Its `x` value is measured in source-image coordinates.
- `CameraPath` is the protocol for resolving a `CameraState` from normalized
  shot progress.
- `LinearCameraPath` interpolates between two camera states with smooth easing.
- `BezierCameraPath` creates a continuous quadratic or cubic camera trajectory.
- `CameraControlPoint` defines the progress and camera state used to shape a
  Bezier path.
- `SceneFrameRenderer` converts scene time into shot progress, resolves the
  camera state, and renders frames from the source image.
- `EncodeVideoCommand` builds the ffmpeg command for encoding raw frames.
- `FfmpegVideoOutput` streams rendered frames to the ffmpeg process.

## Pipeline

```text
Scene
  -> SceneFrameRenderer
  -> rendered frames
  -> FfmpegVideoOutput
  -> ffmpeg encoded video
```

## Build Scripts

- `build_scene_001.py` through `build_scene_009.py` render individual scenes.
- `build_navigation_reel.py` assembles the scene videos into the navigation
  reel.
- `build_thumbnail.py` builds the reel thumbnail.
- `generate_thumbnails.py` generates preview thumbnails for source images.

Scene scripts can be run directly and support custom input and output paths:

```bash
python scripts/build_scene_001.py
python scripts/build_scene_001.py --input custom.png --output custom.mp4
```
