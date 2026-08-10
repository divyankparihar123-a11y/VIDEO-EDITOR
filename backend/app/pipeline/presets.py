"""Milestone 4: style presets.

Each preset deterministically maps a name (chosen by the user in the UI) to
a color-grade recipe (procedural ffmpeg filter parameters -- no hand
authored .cube LUTs needed for this MVP), a cycling list of xfade
transition types, transition duration, average shot length (drives clip
selection's sliding-window length), and Ken Burns zoom intensity. No
free-text prompt interpretation -- that's a good v2 feature once this
deterministic version works.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ColorGrade:
    contrast: float = 1.0
    saturation: float = 1.0
    gamma: float = 1.0
    vignette: float = 0.0

    def to_eq_filter(self) -> str:
        return f"eq=contrast={self.contrast}:saturation={self.saturation}:gamma={self.gamma}"

    def to_vignette_filter(self) -> str | None:
        if self.vignette <= 0:
            return None
        # angle in radians; higher vignette -> stronger corner darkening
        angle = 1.2 + self.vignette
        return f"vignette=angle={angle}"

    def filter_chain(self) -> str:
        parts = [self.to_eq_filter()]
        vig = self.to_vignette_filter()
        if vig:
            parts.append(vig)
        return ",".join(parts)


@dataclass(frozen=True)
class StylePreset:
    color: ColorGrade
    transitions: list[str] = field(default_factory=lambda: ["fade"])
    transition_duration: float = 0.4
    avg_shot_len: float = 3.0
    zoom_intensity: float = 0.06

    def transition_for_index(self, index: int, seed: int = 0) -> str:
        if not self.transitions:
            return "fade"
        return self.transitions[(index + seed) % len(self.transitions)]


PRESETS: dict[str, StylePreset] = {
    "cinematic": StylePreset(
        color=ColorGrade(contrast=1.08, saturation=0.92, gamma=0.95, vignette=0.15),
        transitions=["fade", "smoothleft", "smoothright"],
        transition_duration=0.5,
        avg_shot_len=3.2,
        zoom_intensity=0.06,
    ),
    "energetic": StylePreset(
        color=ColorGrade(contrast=1.15, saturation=1.25),
        transitions=["slideleft", "slideright", "wipeup", "wipedown"],
        transition_duration=0.25,
        avg_shot_len=1.6,
        zoom_intensity=0.14,
    ),
    "vlog": StylePreset(
        color=ColorGrade(contrast=1.03, saturation=1.05),
        transitions=["fade", "dissolve"],
        transition_duration=0.35,
        avg_shot_len=2.5,
        zoom_intensity=0.05,
    ),
    "luxury": StylePreset(
        color=ColorGrade(contrast=1.05, saturation=0.85, gamma=0.92, vignette=0.1),
        transitions=["fade", "smoothdown"],
        transition_duration=0.6,
        avg_shot_len=3.5,
        zoom_intensity=0.04,
    ),
}

DEFAULT_PRESET_NAME = "cinematic"


def get_preset(name: str) -> StylePreset:
    return PRESETS.get(name, PRESETS[DEFAULT_PRESET_NAME])
