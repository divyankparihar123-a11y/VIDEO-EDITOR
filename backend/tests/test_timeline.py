from types import SimpleNamespace

from app.pipeline.timeline import build_naive_timeline


def _clip(id_, duration_s, path="clip.mp4"):
    return SimpleNamespace(id=id_, duration_s=duration_s, stored_path=path)


def test_build_naive_timeline_takes_clips_in_order_until_target_reached():
    clips = [_clip(1, 10.0, "a.mp4"), _clip(2, 10.0, "b.mp4"), _clip(3, 10.0, "c.mp4")]

    tl = build_naive_timeline(clips, target_duration_s=15.0, aspect_ratio="9:16", style="cinematic")

    assert tl["aspect_ratio"] == "9:16"
    assert tl["style"] == "cinematic"
    assert len(tl["clips"]) == 2
    assert tl["clips"][0]["clip_id"] == 1
    assert tl["clips"][0]["out"] == 10.0
    assert tl["clips"][1]["clip_id"] == 2
    assert tl["clips"][1]["out"] == 5.0
    assert tl["warnings"] == []


def test_build_naive_timeline_warns_when_footage_insufficient():
    clips = [_clip(1, 5.0)]

    tl = build_naive_timeline(clips, target_duration_s=30.0, aspect_ratio="16:9", style="vlog")

    total = sum(seg["out"] - seg["in"] for seg in tl["clips"])
    assert total == 5.0
    assert any("Not enough" in w for w in tl["warnings"])


def test_build_naive_timeline_skips_zero_duration_clips():
    clips = [_clip(1, 0.0), _clip(2, 8.0)]

    tl = build_naive_timeline(clips, target_duration_s=8.0, aspect_ratio="1:1", style="luxury")

    assert len(tl["clips"]) == 1
    assert tl["clips"][0]["clip_id"] == 2


def test_build_naive_timeline_no_clips_warns():
    tl = build_naive_timeline([], target_duration_s=30.0, aspect_ratio="9:16", style="cinematic")

    assert tl["clips"] == []
    assert any("No usable clips" in w for w in tl["warnings"])
