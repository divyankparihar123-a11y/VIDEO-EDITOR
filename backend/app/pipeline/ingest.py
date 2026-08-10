import json
import subprocess

from PIL import Image

from app.core.config import resolve_ffmpeg_binaries


def _ffprobe_json(path: str) -> dict:
    _, ffprobe_path = resolve_ffmpeg_binaries()
    result = subprocess.run(
        [ffprobe_path, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def _parse_fps(rate: str) -> float | None:
    try:
        num, den = rate.split("/")
        den_f = float(den)
        return float(num) / den_f if den_f else None
    except (ValueError, ZeroDivisionError):
        return None


def probe_video(path: str) -> dict:
    data = _ffprobe_json(path)
    fmt = data.get("format", {})
    duration = float(fmt.get("duration", 0.0) or 0.0)
    video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    width = height = None
    fps = None
    if video_stream is not None:
        width = video_stream.get("width")
        height = video_stream.get("height")
        fps = _parse_fps(video_stream.get("r_frame_rate", "0/1"))
    return {"duration_s": duration, "width": width, "height": height, "fps": fps}


def probe_audio(path: str) -> dict:
    data = _ffprobe_json(path)
    duration = float(data.get("format", {}).get("duration", 0.0) or 0.0)
    return {"duration_s": duration, "width": None, "height": None, "fps": None}


def probe_photo(path: str) -> dict:
    with Image.open(path) as img:
        width, height = img.size
    return {"duration_s": None, "width": width, "height": height, "fps": None}
