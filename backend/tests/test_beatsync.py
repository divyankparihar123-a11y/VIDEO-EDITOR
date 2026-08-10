from app.pipeline.beatsync import (
    cut_points_from_timeline,
    snap_cut_points,
    snap_segment_boundaries,
)


def test_cut_points_from_timeline_video_and_photo():
    segments = [
        {"type": "video", "clip_id": 1, "in": 0.0, "out": 3.0},
        {"type": "photo", "clip_id": 2, "duration": 2.0},
        {"type": "video", "clip_id": 1, "in": 5.0, "out": 9.0},
    ]
    assert cut_points_from_timeline(segments) == [3.0, 5.0, 9.0]


def test_snap_cut_points_snaps_within_tolerance_only():
    cuts = [3.0, 5.02, 9.5]
    beats = [0.0, 1.0, 2.0, 3.1, 4.0, 5.0, 6.0, 9.0]

    snapped = snap_cut_points(cuts, beats, tolerance=0.18)

    assert snapped[0] == 3.1  # within tolerance of 3.0
    assert snapped[1] == 5.0  # within tolerance of 5.02
    assert snapped[2] == 9.5  # nearest beat (9.0) is 0.5 away, outside tolerance


def test_snap_cut_points_no_beats_returns_unchanged():
    cuts = [1.0, 2.0]
    assert snap_cut_points(cuts, []) == cuts


def test_snap_segment_boundaries_clamps_video_to_available_duration():
    segments = [
        {"type": "video", "clip_id": 1, "source": "a.mp4", "in": 0.0, "out": 3.0},
        {"type": "video", "clip_id": 2, "source": "b.mp4", "in": 0.0, "out": 6.0},
    ]
    # Beat lands slightly past clip 1's boundary; nudging "out" further is
    # fine as long as it doesn't exceed the source clip's own duration.
    beats = [3.15]
    source_durations = {1: 10.0, 2: 10.0}

    result = snap_segment_boundaries(segments, source_durations, beats, tolerance=0.2)

    assert result[0]["out"] <= source_durations[1]
    assert result[0]["out"] > 3.0


def test_snap_segment_boundaries_keeps_photo_within_min_duration():
    segments = [
        {"type": "video", "clip_id": 1, "source": "a.mp4", "in": 0.0, "out": 3.0},
        {"type": "photo", "clip_id": 2, "source": "p.jpg", "duration": 2.0},
    ]
    result = snap_segment_boundaries(segments, {1: 10.0}, beat_times=[], tolerance=0.18)

    assert result[1]["duration"] >= 0.3
