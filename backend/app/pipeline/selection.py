"""Milestone 2: best-moment selection.

Pure functions operating on Segment dataclasses and plain (time, score)
tuples -- no ffmpeg/video decode in this module, so it's fully unit
testable with synthetic data. No LLM story-planning: this is a
deterministic scoring + greedy selection heuristic.
"""

from dataclasses import dataclass

DEFAULT_MAX_SEGMENT_S = 6.0
DIMINISHING_RETURNS_FACTOR = 0.15
DEFAULT_TOLERANCE = 0.1


@dataclass
class Segment:
    clip_id: int
    source: str
    start: float
    end: float
    score: float

    @property
    def duration(self) -> float:
        return self.end - self.start


def cap_segment_length(
    segment: Segment,
    scored_points: list[tuple[float, float]],
    max_len: float = DEFAULT_MAX_SEGMENT_S,
    step: float = 0.5,
) -> Segment:
    """If segment is longer than max_len, slide a max_len window across its
    scored points and keep the best-average sub-window. scored_points is a
    list of (t, score) restricted to within [segment.start, segment.end).
    """
    if segment.duration <= max_len or not scored_points:
        return segment

    best_start = segment.start
    best_avg = segment.score
    found_window = False

    t = segment.start
    while t + max_len <= segment.end + 1e-9:
        window = [s for (pt, s) in scored_points if t <= pt < t + max_len]
        if window:
            avg = sum(window) / len(window)
            if not found_window or avg > best_avg:
                best_avg = avg
                best_start = t
                found_window = True
        t += step

    return Segment(segment.clip_id, segment.source, best_start, best_start + max_len, best_avg)


def select_segments(
    candidates: list[Segment],
    target_duration_s: float,
    tolerance: float = DEFAULT_TOLERANCE,
) -> tuple[list[Segment], list[str]]:
    """Greedily pick highest (diminishing-returns-adjusted) scoring,
    non-overlapping segments until close to target_duration_s. Diminishing
    returns are recomputed after every pick to encourage cross-clip variety.
    Falls back to using all available footage (with a warning) if the pool
    can't reach the target duration.
    """
    warnings: list[str] = []
    remaining_pool = list(candidates)
    picked: list[Segment] = []
    picked_ranges: dict[int, list[tuple[float, float]]] = {}
    per_source_count: dict[int, int] = {}
    total = 0.0
    target_hi = target_duration_s * (1 + tolerance)

    def overlaps(clip_id: int, start: float, end: float) -> bool:
        return any(start < e and end > s for s, e in picked_ranges.get(clip_id, []))

    def adjusted_score(seg: Segment) -> float:
        count = per_source_count.get(seg.clip_id, 0)
        return seg.score / (1 + DIMINISHING_RETURNS_FACTOR * count)

    while remaining_pool and total < target_hi:
        remaining_pool.sort(key=adjusted_score, reverse=True)
        cand = remaining_pool.pop(0)
        if overlaps(cand.clip_id, cand.start, cand.end):
            continue
        picked.append(cand)
        picked_ranges.setdefault(cand.clip_id, []).append((cand.start, cand.end))
        per_source_count[cand.clip_id] = per_source_count.get(cand.clip_id, 0) + 1
        total += cand.duration

    if not picked:
        warnings.append("No usable segments were found; the job could not produce any output.")
    elif total < target_duration_s * (1 - tolerance):
        warnings.append(
            f"Not enough good footage to reach the requested duration; "
            f"used all available footage (~{total:.1f}s of {target_duration_s:.1f}s requested)."
        )

    if total > target_hi and picked:
        overshoot = total - target_duration_s
        last = picked[-1]
        if 0 < overshoot < last.duration:
            # Trim the tail of the last segment to land on target
            new_end = last.end - overshoot
            if new_end > last.start:
                picked[-1] = Segment(last.clip_id, last.source, last.start, new_end, last.score)
            else:
                picked.pop()
        elif overshoot >= last.duration:
            # Last segment is entirely surplus — drop it
            picked.pop()

    picked.sort(key=lambda s: (s.clip_id, s.start))
    return picked, warnings
