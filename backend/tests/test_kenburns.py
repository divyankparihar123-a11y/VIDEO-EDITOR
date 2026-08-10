from app.pipeline.kenburns import build_kenburns_filter, build_photo_prep_filter, random_seed_for_index


def test_build_kenburns_filter_includes_target_size_and_fps():
    filt = build_kenburns_filter(width=1080, height=1920, duration_s=3.0, fps=30, zoom_intensity=0.1, seed=0)

    assert "s=1080x1920" in filt
    assert "fps=30" in filt
    assert "d=90" in filt  # 3.0s * 30fps


def test_build_kenburns_filter_zoom_cap_reflects_intensity():
    filt = build_kenburns_filter(width=1080, height=1920, duration_s=2.0, fps=30, zoom_intensity=0.2, seed=0)
    assert "min(zoom+" in filt
    assert ",1.2)" in filt  # max_zoom = 1.0 + 0.2


def test_build_kenburns_filter_different_seeds_can_pan_differently():
    filters = {build_kenburns_filter(1080, 1920, 3.0, 30, 0.1, seed=s) for s in range(5)}
    # 5 seeds cycle through 5 pan directions -- expect more than one distinct filter string
    assert len(filters) > 1


def test_build_photo_prep_filter_pads_and_blurs_background():
    filt = build_photo_prep_filter(1080, 1920)
    assert "gblur" in filt
    assert "overlay" in filt
    assert "1080:1920" in filt


def test_random_seed_for_index_is_deterministic():
    assert random_seed_for_index(3) == random_seed_for_index(3)
