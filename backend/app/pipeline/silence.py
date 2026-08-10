"""Milestone 2: silence detection via ffmpeg's silencedetect audio filter.

Used as a scoring signal (a moment sitting in a silent span is a weaker
candidate) and, later, for trimming dead air -- not as a hard splitter,
since natural speech pauses are fine.
"""

import re
import subprocess

from app.core.config import resolve_ffmpeg_binaries

_SILENCE_START_RE = re.compile(r"silence_start:\s*([\d.]+)")
_SILENCE_END_RE = re.compile(r"silence_end:\s*([\d.]+)\s*\|\s*silence_duration:\s*([\d.]+)")


def detect_silence(path: str, noise_db: str = "-30dB", min_duration_s: float = 0.4) -> list[tuple[float, float]]:
    ffmpeg_path, _ = resolve_ffmpeg_binaries()
    cmd = [
        ffmpeg_path, "-i", path,
        "-af", f"silencedetect=n={noise_db}:d={min_duration_s}",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    stderr = result.stderr or ""

    starts = [float(m.group(1)) for m in _SILENCE_START_RE.finditer(stderr)]
    ends = [float(m.group(1)) for m in _SILENCE_END_RE.finditer(stderr)]

    return list(zip(starts, ends))
