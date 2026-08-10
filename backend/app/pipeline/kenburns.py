"""Milestone 4: Ken Burns zoom/pan for photos.

Builds an ffmpeg zoompan filter expression. Since zoompan distorts
mismatched aspect ratios, photos whose native ratio doesn't match the
target output ratio are padded with a blurred full-bleed copy of
themselves rather than stretched.
"""

import random

# (start_corner -> end_corner) pan directions; x/y expressions target the
# zoompan output frame's top-left corner as the pan progresses.
_PAN_DIRECTIONS = ["tl->br", "tr->bl", "bl->tr", "br->tl", "center"]


def _pan_xy_exprs(direction: str) -> tuple[str, str]:
    # zoompan x/y are the top-left corner of the crop window, in source
    # pixel coordinates scaled by the current zoom; iw/ih are the (upscaled)
    # input width/height, zoom is the current zoom expression value.
    if direction == "tl->br":
        return "(iw-iw/zoom)*on/duration", "(ih-ih/zoom)*on/duration"
    if direction == "tr->bl":
        return "(iw-iw/zoom)*(1-on/duration)", "(ih-ih/zoom)*on/duration"
    if direction == "bl->tr":
        return "(iw-iw/zoom)*on/duration", "(ih-ih/zoom)*(1-on/duration)"
    if direction == "br->tl":
        return "(iw-iw/zoom)*(1-on/duration)", "(ih-ih/zoom)*(1-on/duration)"
    return "(iw-iw/zoom)/2", "(ih-ih/zoom)/2"  # center


def build_kenburns_filter(
    width: int,
    height: int,
    duration_s: float,
    fps: int,
    zoom_intensity: float,
    seed: int = 0,
) -> str:
    frames = max(1, round(duration_s * fps))
    max_zoom = 1.0 + zoom_intensity
    rate = zoom_intensity / max(1, frames)
    direction = _PAN_DIRECTIONS[seed % len(_PAN_DIRECTIONS)]
    x_expr, y_expr = _pan_xy_exprs(direction)

    # Upscale generously first so zoompan has sub-pixel room to pan/zoom
    # without revealing edges; pad+blur handles aspect mismatches before
    # this filter runs (see build_photo_prep_filter).
    zoompan = (
        f"zoompan=z='min(zoom+{rate},{max_zoom})':x='{x_expr}':y='{y_expr}':"
        f"d={frames}:s={width}x{height}:fps={fps}"
    )
    return zoompan


def build_photo_prep_filter(width: int, height: int) -> str:
    """Pad a photo to the target aspect ratio with a blurred, scaled-up
    full-bleed copy of itself behind it, instead of stretching -- then
    upscale for zoompan headroom.
    """
    return (
        f"split=2[bg][fg];"
        f"[bg]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},gblur=sigma=20[bg_blurred];"
        f"[fg]scale={width}:{height}:force_original_aspect_ratio=decrease[fg_scaled];"
        f"[bg_blurred][fg_scaled]overlay=(W-w)/2:(H-h)/2,"
        f"scale={width * 2}:{height * 2}"
    )


def random_seed_for_index(index: int) -> int:
    rng = random.Random(index)
    return rng.randint(0, 10_000)
