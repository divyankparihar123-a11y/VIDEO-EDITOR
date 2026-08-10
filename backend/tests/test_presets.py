from app.pipeline.presets import PRESETS, ColorGrade, StylePreset, get_preset


def test_get_preset_known_name_returns_matching_preset():
    preset = get_preset("energetic")
    assert preset is PRESETS["energetic"]


def test_get_preset_unknown_name_falls_back_to_default():
    preset = get_preset("not-a-real-style")
    assert preset is PRESETS["cinematic"]


def test_transition_for_index_cycles():
    preset = StylePreset(color=ColorGrade(), transitions=["a", "b", "c"])
    assert [preset.transition_for_index(i) for i in range(5)] == ["a", "b", "c", "a", "b"]


def test_transition_for_index_empty_list_defaults_to_fade():
    preset = StylePreset(color=ColorGrade(), transitions=[])
    assert preset.transition_for_index(0) == "fade"


def test_color_grade_filter_chain_includes_vignette_only_when_positive():
    with_vignette = ColorGrade(contrast=1.1, saturation=0.9, gamma=1.0, vignette=0.2)
    without_vignette = ColorGrade(contrast=1.1, saturation=0.9, gamma=1.0, vignette=0.0)

    assert "vignette" in with_vignette.filter_chain()
    assert "vignette" not in without_vignette.filter_chain()
    assert "eq=contrast=1.1:saturation=0.9:gamma=1.0" in without_vignette.filter_chain()


def test_all_presets_have_nonempty_transitions_and_positive_pacing():
    for name, preset in PRESETS.items():
        assert preset.transitions, f"{name} has no transitions"
        assert preset.transition_duration > 0
        assert preset.avg_shot_len > 0
        assert 0 < preset.zoom_intensity < 1
