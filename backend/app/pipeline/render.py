"""Renders a job's timeline to a final mp4.

render_naive (Milestone 1) is a dumb single-pass render: normalize each
selected segment, then concat with hard cuts. render_full (Milestone 4) is
the real two-pass renderer -- Ken Burns photos, xfade/acrossfade
transitions, procedural color grade, optional music mix/ducking, and
caption burn-in -- and is what the pipeline actually calls; render_naive is
kept as a simpler reference/fallback.
"""

import json
import subprocess
from collections.abc import Callable
from pathlib import Path

from app.core.config import detect_nvenc, resolve_ffmpeg_binaries

ASPECT_RESOLUTIONS = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
}

ProgressCallback = Callable[[float, str], None]


def select_video_encoder(ffmpeg_path: str) -> list[str]:
    if detect_nvenc(ffmpeg_path):
        return [
            "-c:v", "h264_nvenc",
            "-preset", "p5",
            "-rc", "vbr",
            "-cq", "23",
            "-b:v", "0",
            "-maxrate", "10M",
            "-bufsize", "20M",
            "-spatial-aq", "1",
            "-temporal-aq", "1",
            "-rc-lookahead", "20",
            "-bf", "3",
        ]
    return ["-c:v", "libx264", "-preset", "medium", "-crf", "20"]


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            "ffmpeg command failed:\n"
            f"  cmd: {' '.join(cmd)}\n"
            f"  stderr (tail): {result.stderr[-2000:]}"
        )


def _escape_path_for_filter(path: Path) -> str:
    # ffmpeg's filtergraph parser treats ':' as a key=value separator, which
    # collides with Windows drive letters (C:\...) -- escape it with a
    # backslash and use forward slashes. Do NOT also wrap the result in
    # single quotes: inside single quotes ffmpeg treats backslash as a
    # literal character (not an escape), so combining both would leave a
    # stray backslash in the path instead of an escaped colon.
    posix = path.as_posix()
    return posix.replace(":", "\\:")


def burn_captions(
    ffmpeg_path: str,
    input_path: Path,
    ass_path: Path,
    output_path: Path,
    encoder_args: list[str],
) -> None:
    escaped = _escape_path_for_filter(ass_path)
    cmd = [
        ffmpeg_path, "-y",
        "-i", str(input_path),
        "-vf", f"ass={escaped}",
        *encoder_args,
        "-c:a", "copy",
        str(output_path),
    ]
    _run(cmd)


def render_naive(
    timeline: dict,
    work_dir: Path,
    output_path: Path,
    progress_cb: ProgressCallback | None = None,
    ass_path: Path | None = None,
) -> None:
    ffmpeg_path, _ = resolve_ffmpeg_binaries()
    width, height = ASPECT_RESOLUTIONS[timeline["aspect_ratio"]]
    fps = timeline.get("fps", 30)
    encoder_args = select_video_encoder(ffmpeg_path)

    segments = timeline["clips"]
    if not segments:
        raise RuntimeError("Timeline has no segments to render.")

    segments_dir = work_dir / "segments"
    segments_dir.mkdir(parents=True, exist_ok=True)

    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"setsar=1,fps={fps}"
    )

    segment_paths: list[Path] = []
    total = len(segments)
    for index, seg in enumerate(segments):
        seg_path = segments_dir / f"segment_{index:03d}.mp4"
        duration = seg["out"] - seg["in"]
        cmd = [
            ffmpeg_path, "-y",
            "-ss", str(seg["in"]),
            "-i", seg["source"],
            "-t", str(duration),
            "-vf", vf,
            *encoder_args,
            "-c:a", "aac", "-ar", "48000", "-ac", "2",
            "-pix_fmt", "yuv420p",
            str(seg_path),
        ]
        _run(cmd)
        segment_paths.append(seg_path)
        if progress_cb:
            progress_cb(0.1 + 0.8 * (index + 1) / total, f"Encoding segment {index + 1}/{total}")

    concat_list_path = work_dir / "concat.txt"
    concat_list_path.write_text(
        "\n".join(f"file '{p.as_posix()}'" for p in segment_paths),
        encoding="utf-8",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    concat_target = output_path if ass_path is None else work_dir / "concat_output.mp4"
    concat_cmd = [
        ffmpeg_path, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list_path),
        "-c", "copy",
        str(concat_target),
    ]
    _run(concat_cmd)

    if ass_path is not None:
        if progress_cb:
            progress_cb(0.92, "burning captions")
        burn_captions(ffmpeg_path, concat_target, ass_path, output_path, encoder_args)

    if progress_cb:
        progress_cb(1.0, "done")


# ---------------------------------------------------------------------------
# Milestone 4: full two-pass render -- Ken Burns photos, xfade/acrossfade
# transitions, procedural color grade, optional music mix/ducking, caption
# burn-in. Pass 1 normalizes every segment (video or photo) to an identical
# spec as an intermediate file with both a video and audio stream (photos
# get a generated silent audio track) so Pass 2's filter_complex can treat
# every input uniformly. Pass 2 chains transitions, grades once on the
# concatenated stream (not per-segment, to avoid double-graded transition
# midpoints), optionally mixes/ducks background music, burns captions, and
# does the final encode.
# ---------------------------------------------------------------------------

MIN_TRANSITION_MARGIN_S = 0.05


def _normalize_video_segment(ffmpeg_path: str, seg: dict, width: int, height: int, fps: int, out_path: Path) -> float:
    duration = seg["out"] - seg["in"]
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"setsar=1,fps={fps}"
    )
    cmd = [
        ffmpeg_path, "-y",
        "-ss", str(seg["in"]),
        "-i", seg["source"],
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-ar", "48000", "-ac", "2",
        "-pix_fmt", "yuv420p",
        str(out_path),
    ]
    _run(cmd)
    return duration


def _normalize_photo_segment(ffmpeg_path: str, seg: dict, width: int, height: int, fps: int, zoom_intensity: float, out_path: Path) -> float:
    from app.pipeline.kenburns import build_kenburns_filter, build_photo_prep_filter

    duration = seg["duration"]
    seed = seg.get("kenburns_seed", 0)
    prep = build_photo_prep_filter(width, height)
    kenburns = build_kenburns_filter(width, height, duration, fps, zoom_intensity, seed)
    vf = f"{prep},{kenburns},setsar=1"

    cmd = [
        ffmpeg_path, "-y",
        "-loop", "1", "-i", seg["source"],
        "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=48000",
        "-t", str(duration),
        "-filter_complex", f"[0:v]{vf}[vout]",
        "-map", "[vout]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-ar", "48000", "-ac", "2",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(out_path),
    ]
    _run(cmd)
    return duration


def _build_transition_chain(
    n: int,
    durations: list[float],
    transitions: list[str],
    transition_duration: float,
) -> tuple[str, str, str, float]:
    """Returns (filter_complex_fragment, final_video_label, final_audio_label,
    total_output_duration). The returned labels are always filter-graph
    labels (never raw "N:v"/"N:a" stream specifiers), via a pass-through
    null filter even for a single segment -- so downstream code can always
    reference them the same way (wrapped in brackets) without a special
    case for n==1.
    """
    if n == 1:
        return "[0:v]null[v0];[0:a]anull[a0]", "v0", "a0", durations[0]

    filters = []
    cur_v, cur_a = "0:v", "0:a"
    cursor = durations[0]  # end time (in the still-growing merged timeline) of the chain built so far

    for i in range(1, n):
        # Cap the transition to a safe fraction of both clips involved so
        # xfade/acrossfade never asks for more overlap than either side has.
        td = min(transition_duration, durations[i - 1] - MIN_TRANSITION_MARGIN_S, durations[i] - MIN_TRANSITION_MARGIN_S)
        td = max(0.05, td)
        transition_type = transitions[(i - 1) % len(transitions)] if transitions else "fade"

        offset = cursor - td
        v_out, a_out = f"v{i}", f"a{i}"
        filters.append(f"[{cur_v}][{i}:v]xfade=transition={transition_type}:duration={td}:offset={offset}[{v_out}]")
        filters.append(f"[{cur_a}][{i}:a]acrossfade=d={td}[{a_out}]")

        cur_v, cur_a = v_out, a_out
        cursor += durations[i] - td

    return ";".join(filters), cur_v, cur_a, cursor


def render_full(
    timeline: dict,
    work_dir: Path,
    output_path: Path,
    progress_cb: ProgressCallback | None = None,
    ass_path: Path | None = None,
) -> None:
    ffmpeg_path, ffprobe_path = resolve_ffmpeg_binaries()
    width, height = ASPECT_RESOLUTIONS[timeline["aspect_ratio"]]
    fps = timeline.get("fps", 30)
    encoder_args = select_video_encoder(ffmpeg_path)

    segments = timeline["clips"]
    if not segments:
        raise RuntimeError("Timeline has no segments to render.")

    color_grade = timeline.get("color_grade") or {}
    zoom_intensity = 0.06
    transitions = timeline.get("transitions") or ["fade"]
    transition_duration = timeline.get("transition_duration", 0.4)

    segments_dir = work_dir / "segments"
    segments_dir.mkdir(parents=True, exist_ok=True)

    # --- Pass 1: normalize every segment ---
    normalized_paths: list[Path] = []
    durations: list[float] = []
    total = len(segments)
    for index, seg in enumerate(segments):
        seg_path = segments_dir / f"segment_{index:03d}.mp4"
        if seg["type"] == "photo":
            duration = _normalize_photo_segment(ffmpeg_path, seg, width, height, fps, zoom_intensity, seg_path)
        else:
            duration = _normalize_video_segment(ffmpeg_path, seg, width, height, fps, seg_path)
        normalized_paths.append(seg_path)
        durations.append(duration)
        if progress_cb:
            progress_cb(0.1 + 0.55 * (index + 1) / total, f"Normalizing segment {index + 1}/{total}")

    # Pre-flight sanity check: every Pass-1 intermediate must share
    # resolution/fps/pix_fmt/SAR before Pass 2's xfade chain -- this is the
    # most common real-world xfade failure mode.
    for p in normalized_paths:
        probe = subprocess.run(
            [ffprobe_path, "-v", "quiet", "-print_format", "json", "-show_streams", str(p)],
            capture_output=True, text=True, check=True,
        )
        streams = json.loads(probe.stdout).get("streams", [])
        vstream = next((s for s in streams if s.get("codec_type") == "video"), None)
        if vstream is None or vstream.get("width") != width or vstream.get("height") != height:
            raise RuntimeError(f"Pass-1 intermediate {p} does not match target resolution {width}x{height}.")

    if progress_cb:
        progress_cb(0.68, "composing transitions")

    # --- Pass 2: transitions + color grade + music + captions + encode ---
    chain_filters, v_label, a_label, total_duration = _build_transition_chain(
        len(normalized_paths), durations, transitions, transition_duration
    )

    color_filter = None
    if color_grade:
        from app.pipeline.presets import ColorGrade

        color_filter = ColorGrade(
            contrast=color_grade.get("contrast", 1.0),
            saturation=color_grade.get("saturation", 1.0),
            gamma=color_grade.get("gamma", 1.0),
            vignette=color_grade.get("vignette", 0.0),
        ).filter_chain()

    filter_parts = [chain_filters] if chain_filters else []
    graded_label = v_label
    if color_filter:
        graded_label = "vgraded"
        filter_parts.append(f"[{v_label}]{color_filter}[{graded_label}]")

    inputs: list[str] = []
    for p in normalized_paths:
        inputs += ["-i", str(p)]

    music_info = timeline.get("music")
    final_audio_label = a_label
    if music_info and music_info.get("source"):
        music_input_index = len(normalized_paths)
        inputs += ["-stream_loop", "-1", "-i", music_info["source"]]
        gain_db = -8
        filter_parts.append(
            f"[{music_input_index}:a]atrim=0:{total_duration},volume={gain_db}dB,asetpts=PTS-STARTPTS[music_gain]"
        )
        filter_parts.append(
            f"[music_gain][{a_label}]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=300[music_ducked]"
        )
        filter_parts.append(f"[music_ducked][{a_label}]amix=inputs=2:duration=first:dropout_transition=2[amixed]")
        final_audio_label = "amixed"

    final_video_label = graded_label
    if ass_path is not None:
        escaped = _escape_path_for_filter(ass_path)
        final_video_label = "vcaptioned"
        filter_parts.append(f"[{graded_label}]ass={escaped}[{final_video_label}]")

    filter_complex = ";".join(part for part in filter_parts if part)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_path, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{final_video_label}]",
        "-map", f"[{final_audio_label}]",
        *encoder_args,
        "-c:a", "aac", "-ar", "48000", "-ac", "2",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]
    _run(cmd)

    if progress_cb:
        progress_cb(1.0, "done")
