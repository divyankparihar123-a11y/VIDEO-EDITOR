from app.pipeline.selection import Segment, cap_segment_length, select_segments


def test_select_segments_converges_near_target_duration():
    candidates = [
        Segment(clip_id=1, source="a.mp4", start=0.0, end=5.0, score=0.9),
        Segment(clip_id=1, source="a.mp4", start=6.0, end=10.0, score=0.5),
        Segment(clip_id=2, source="b.mp4", start=0.0, end=6.0, score=0.8),
        Segment(clip_id=2, source="b.mp4", start=7.0, end=12.0, score=0.7),
        Segment(clip_id=3, source="c.mp4", start=0.0, end=4.0, score=0.6),
    ]
    picked, warnings = select_segments(candidates, target_duration_s=15.0, tolerance=0.1)

    total = sum(s.duration for s in picked)
    assert 13.5 <= total <= 16.5
    assert warnings == []


def test_select_segments_never_overlaps_within_a_source():
    candidates = [
        Segment(clip_id=1, source="a.mp4", start=0.0, end=5.0, score=0.9),
        Segment(clip_id=1, source="a.mp4", start=3.0, end=8.0, score=0.85),
        Segment(clip_id=1, source="a.mp4", start=9.0, end=12.0, score=0.4),
    ]
    picked, _ = select_segments(candidates, target_duration_s=20.0, tolerance=0.1)

    by_clip: dict[int, list[Segment]] = {}
    for seg in picked:
        by_clip.setdefault(seg.clip_id, []).append(seg)

    for segs in by_clip.values():
        segs.sort(key=lambda s: s.start)
        for a, b in zip(segs, segs[1:]):
            assert a.end <= b.start


def test_select_segments_prefers_diversity_via_diminishing_returns():
    # Source 1 has two great segments; source 2 has one merely-good segment.
    # Diminishing returns should still let source 2 in rather than picking
    # only from source 1.
    candidates = [
        Segment(clip_id=1, source="a.mp4", start=0.0, end=5.0, score=0.95),
        Segment(clip_id=1, source="a.mp4", start=6.0, end=11.0, score=0.94),
        Segment(clip_id=2, source="b.mp4", start=0.0, end=5.0, score=0.7),
    ]
    picked, _ = select_segments(candidates, target_duration_s=15.0, tolerance=0.1)

    sources = {seg.clip_id for seg in picked}
    assert 2 in sources


def test_select_segments_warns_when_footage_insufficient():
    candidates = [Segment(clip_id=1, source="a.mp4", start=0.0, end=3.0, score=0.5)]
    picked, warnings = select_segments(candidates, target_duration_s=30.0, tolerance=0.1)

    assert len(picked) == 1
    assert any("Not enough" in w for w in warnings)


def test_select_segments_empty_pool_warns_and_returns_nothing():
    picked, warnings = select_segments([], target_duration_s=30.0)

    assert picked == []
    assert any("No usable segments" in w for w in warnings)


def test_cap_segment_length_keeps_short_segments_unchanged():
    seg = Segment(clip_id=1, source="a.mp4", start=0.0, end=3.0, score=0.5)
    points = [(0.0, 0.5), (1.0, 0.5), (2.0, 0.5)]

    result = cap_segment_length(seg, points, max_len=6.0)

    assert result is seg


def test_cap_segment_length_picks_best_scoring_window():
    seg = Segment(clip_id=1, source="a.mp4", start=0.0, end=12.0, score=0.5)
    # Scores rise then fall; the best 4s window should center on t=6-8.
    points = [(float(t), 0.9 if 6.0 <= t < 8.0 else 0.2) for t in range(0, 12)]

    result = cap_segment_length(seg, points, max_len=4.0, step=1.0)

    assert result.duration == 4.0
    assert 4.0 <= result.start <= 6.0
    assert result.score > 0.5
