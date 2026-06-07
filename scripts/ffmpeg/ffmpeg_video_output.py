import subprocess
from types import TracebackType
from typing import Optional, Type

from PIL import Image

from ffmpeg.encode_video_command import EncodeVideoCommand


class FfmpegVideoOutput:
    def __init__(self, command: EncodeVideoCommand) -> None:
        self.command = command
        self.process: Optional[subprocess.Popen] = None

    def __enter__(self) -> "FfmpegVideoOutput":
        self.process = subprocess.Popen(self.command.argv, stdin=subprocess.PIPE)
        return self

    def write(self, frame: Image.Image) -> None:
        if self.process is None or self.process.stdin is None:
            raise RuntimeError("FfmpegVideoOutput is not open.")

        try:
            self.process.stdin.write(frame.tobytes())
        except BrokenPipeError:
            return_code = self.process.wait()
            self.process = None
            if return_code != 0:
                raise subprocess.CalledProcessError(return_code, self.command.argv)
            raise

    def close(self) -> None:
        if self.process is None:
            return

        if self.process.stdin is not None and not self.process.stdin.closed:
            try:
                self.process.stdin.close()
            except BrokenPipeError:
                pass

        return_code = self.process.wait()
        self.process = None
        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, self.command.argv)

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.close()
