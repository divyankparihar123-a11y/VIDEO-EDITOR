"""Milestone 3: word-level captions.

Transcribes each source clip once (in the clip's own time coordinates),
remaps word timestamps into final-timeline coordinates after selection has
picked which spans made the cut, chunks words into short caption "cards",
and renders them as ASS karaoke subtitles for burn-in via ffmpeg's
subtitles filter (libass) -- see app/pipeline/render.py.
"""

DEFAULT_MODEL_SIZE = "small"
MAX_WORDS_PER_CARD = 5
MAX_GAP_S = 0.8

_model_cache: dict[str, object] = {}


def _load_model(model_size: str = DEFAULT_MODEL_SIZE):
    if model_size in _model_cache:
        return _model_cache[model_size]

    from faster_whisper import WhisperModel

    try:
        model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
    except Exception:
        model = WhisperModel(model_size, device="cpu", compute_type="int8")

    _model_cache[model_size] = model
    return model


def transcribe_words(path: str, model_size: str = DEFAULT_MODEL_SIZE) -> list[dict]:
    """Word-level timestamps in the clip's own (original-file) time
    coordinates -- start/end are relative to `path`, not the final timeline.
    """
    model = _load_model(model_size)
    segments, _info = model.transcribe(
        path,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
    )

    words: list[dict] = []
    for seg in segments:
        for w in seg.words or []:
            text = (w.word or "").strip()
            if text:
                words.append({"start": w.start, "end": w.end, "word": text})
    return words


def remap_words_to_timeline(timeline_clips: list[dict], words_by_source: dict[str, list[dict]]) -> list[dict]:
    """Slices+shifts each source clip's words into final-timeline
    coordinates as the renderer will lay them out (chronological, per
    timeline_clips). A word that falls outside every selected segment's
    boundary is dropped -- acceptable when a trim cuts mid-sentence. Photo
    entries (no speech, no "in"/"out") just advance the cursor by their
    assigned duration.
    """
    out_words: list[dict] = []
    cursor = 0.0

    for seg in timeline_clips:
        if seg.get("type") == "photo":
            cursor += seg.get("duration", 0.0)
            continue

        seg_in, seg_out = seg["in"], seg["out"]
        duration = seg_out - seg_in
        for word in words_by_source.get(seg["source"], []):
            overlap_start = max(word["start"], seg_in)
            overlap_end = min(word["end"], seg_out)
            if overlap_end <= overlap_start:
                continue
            out_words.append(
                {
                    "start": cursor + (overlap_start - seg_in),
                    "end": cursor + (overlap_end - seg_in),
                    "word": word["word"],
                }
            )
        cursor += duration

    return out_words


def chunk_words(words: list[dict], max_words: int = MAX_WORDS_PER_CARD, max_gap_s: float = MAX_GAP_S) -> list[list[dict]]:
    """Group words into short caption cards (~3-6 words, or split on a
    noticeable gap) -- matches modern short-form caption UX rather than one
    long karaoke line.
    """
    cards: list[list[dict]] = []
    current: list[dict] = []
    prev_end: float | None = None

    for word in words:
        if current and (len(current) >= max_words or (prev_end is not None and word["start"] - prev_end > max_gap_s)):
            cards.append(current)
            current = []
        current.append(word)
        prev_end = word["end"]

    if current:
        cards.append(current)
    return cards


ASS_HEADER_TEMPLATE = """[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font},{fontsize},{primary},{secondary},{outline_colour},{back},{bold},0,0,0,100,100,0,0,1,{outline},{shadow},2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

DEFAULT_CAPTION_STYLE = {
    "font": "Arial",
    "fontsize": 64,
    "primary": "&H00FFFFFF",  # already-spoken word color (opaque white)
    "secondary": "&H0000FFFF",  # not-yet-spoken word color (opaque yellow)
    "outline_colour": "&H00000000",
    "back": "&H80000000",
    "bold": -1,
    "outline": 3,
    "shadow": 0,
    "margin_v": 180,
}


def _format_ass_time(t: float) -> str:
    t = max(0.0, t)
    centiseconds = round(t * 100)
    hours, rem = divmod(centiseconds, 360000)
    minutes, rem = divmod(rem, 6000)
    seconds, cs = divmod(rem, 100)
    return f"{hours:d}:{minutes:02d}:{seconds:02d}.{cs:02d}"


def build_ass(cards: list[list[dict]], width: int, height: int, style: dict | None = None) -> str:
    colors = {**DEFAULT_CAPTION_STYLE, **(style or {})}
    header = ASS_HEADER_TEMPLATE.format(width=width, height=height, **colors)

    lines = [header]
    for card in cards:
        if not card:
            continue
        card_start = card[0]["start"]
        card_end = card[-1]["end"]
        text = "".join(
            f"{{\\k{max(1, round((w['end'] - w['start']) * 100))}}}{w['word']} " for w in card
        ).strip()
        lines.append(
            f"Dialogue: 0,{_format_ass_time(card_start)},{_format_ass_time(card_end)},Caption,,0,0,0,,{text}"
        )
    return "\n".join(lines)
