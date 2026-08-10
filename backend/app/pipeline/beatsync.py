"""Milestone 4: beat detection and cut-snapping.

Snaps already-chosen cut points on the output timeline to the nearest beat
in a user-supplied music track, within a tolerance -- never the other way
around (no time-warping/elastic re-timing of clip content, which would
introduce pitch/tempo artifacts and isn't necessary for this MVP).
"""

import bisect

SNAP_TOLERANCE_S = 0.18


def detect_beats(music_path: str) -> tuple[float, list[float]]:
    """Returns (tempo_bpm, beat_times_s)."""
    import librosa

    y, sr = librosa.load(music_path)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # librosa >=0.11 returns tempo as a 0-d/1-element ndarray, not a scalar.
    tempo_value = float(tempo[0]) if hasattr(tempo, "__len__") and len(tempo) else float(tempo)
    return tempo_value, [float(t) for t in beat_times]


def snap_cut_points(cut_points: list[float], beat_times: list[float], tolerance: float = SNAP_TOLERANCE_S) -> list[float]:
    """For each cut point, snap to the nearest beat within tolerance; leave
    it unchanged if nothing is within tolerance.
    """
    if not beat_times:
        return list(cut_points)

    sorted_beats = sorted(beat_times)
    snapped = []
    for cut in cut_points:
        idx = bisect.bisect_left(sorted_beats, cut)
        candidates = [b for b in (sorted_beats[idx - 1] if idx > 0 else None, sorted_beats[idx] if idx < len(sorted_beats) else None) if b is not None]
        if not candidates:
            snapped.append(cut)
            continue
        nearest = min(candidates, key=lambda b: abs(b - cut))
        snapped.append(nearest if abs(nearest - cut) <= tolerance else cut)
    return snapped


def cut_points_from_timeline(timeline_clips: list[dict]) -> list[float]:
    """Cumulative cut-point times (segment boundaries) on the final
    timeline, derived from each segment's own duration.
    """
    points = []
    cursor = 0.0
    for seg in timeline_clips:
        duration = seg["out"] - seg["in"] if "out" in seg else seg.get("duration", 0.0)
        cursor += duration
        points.append(cursor)
    return points


MIN_SEGMENT_DURATION_S = 0.3


def snap_segment_boundaries(
    segments: list[dict],
    source_durations: dict[int, float],
    beat_times: list[float],
    tolerance: float = SNAP_TOLERANCE_S,
) -> list[dict]:
    """Adjusts each segment's end (video: 'out', photo: 'duration') so the
    cumulative cut points land on the nearest beat within tolerance. Each
    segment's start point ('in') is left untouched -- only how much of it we
    use is adjusted -- and video segments are clamped to their source
    clip's available duration so we never ask ffmpeg to read past EOF.
    """
    cut_points = cut_points_from_timeline(segments)
    snapped_points = snap_cut_points(cut_points, beat_times, tolerance)

    out_segments = []
    cursor = 0.0
    for seg, snapped_end in zip(segments, snapped_points):
        new_duration = max(MIN_SEGMENT_DURATION_S, snapped_end - cursor)
        new_seg = dict(seg)

        if seg["type"] == "video":
            available = source_durations.get(seg["clip_id"], seg["out"])
            candidate_out = seg["in"] + new_duration
            new_seg["out"] = min(candidate_out, available)
            actual_duration = new_seg["out"] - seg["in"]
        else:
            new_seg["duration"] = new_duration
            actual_duration = new_duration

        cursor += actual_duration
        out_segments.append(new_seg)

    return out_segments
