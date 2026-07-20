"""
Recording architecture for future MP4 / GIF / PNG-sequence export.

This phase defines interfaces only. Screenshots are implemented via the viewer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class RecordingFormat(str, Enum):
    """Supported future recording containers."""

    MP4 = "mp4"
    GIF = "gif"
    PNG_SEQUENCE = "png_sequence"


@dataclass(slots=True)
class RecordingSettings:
    """Parameters for a recording session."""

    output_path: Path
    format: RecordingFormat = RecordingFormat.MP4
    fps: float = 30.0
    width: int = 1920
    height: int = 1080
    include_hud: bool = True


class Recorder(ABC):
    """Abstract animation recorder."""

    @abstractmethod
    def start(self, settings: RecordingSettings) -> None:
        """Begin a recording session."""

    @abstractmethod
    def write_frame(self) -> None:
        """Capture the current framebuffer."""

    @abstractmethod
    def stop(self) -> Path:
        """Finalize and return the output path."""


# TODO: Open3DRecorder, MatplotlibRecorder, FFmpegPipeRecorder
