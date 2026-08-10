"""Milestone 2: per-clip quality scoring.

Samples each video at a low rate (not every frame -- these are short-form
inputs, full-frame analysis is wasted compute) and scores sharpness, camera
shake, and exposure. Scores are normalized relative to the current upload
batch (see score_samples), not a single hardcoded global threshold, so
scoring adapts to the footage actually provided.
"""

import math
from dataclasses import dataclass

import cv2
import numpy as np

CANONICAL_WIDTH = 640
SAMPLE_INTERVAL_S = 0.5
COHERENCE_WINDOW = 5

SHARPNESS_WEIGHT = 0.4
SHAKE_WEIGHT = 0.3
BRIGHTNESS_WEIGHT = 0.2
FACE_WEIGHT = 0.1


@dataclass
class QualitySample:
    t: float
    sharpness: float
    shake_penalty: float
    brightness: float
    face_bonus: float


_face_backend = "unset"
_face_detector = None


def _init_face_detector() -> None:
    """Best-effort face detector: MediaPipe first, OpenCV Haar cascade as a
    fallback (ships free with opencv-python), face bonus disabled entirely
    if neither is available. Never a hard dependency.
    """
    global _face_backend, _face_detector
    if _face_backend != "unset":
        return
    try:
        import mediapipe as mp

        _face_detector = mp.solutions.face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.5
        )
        _face_backend = "mediapipe"
        return
    except Exception:
        pass
    try:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        classifier = cv2.CascadeClassifier(cascade_path)
        if not classifier.empty():
            _face_detector = classifier
            _face_backend = "haar"
            return
    except Exception:
        pass
    _face_backend = "off"


def _has_face(frame_bgr: np.ndarray) -> bool:
    _init_face_detector()
    if _face_backend == "mediapipe":
        results = _face_detector.process(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        return bool(results.detections)
    if _face_backend == "haar":
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = _face_detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
        return len(faces) > 0
    return False


def _rolling_shake_penalty(vectors: list[tuple[float, float]], window: int = COHERENCE_WINDOW) -> list[float]:
    """A consistent-direction run of motion vectors is treated as an
    intentional pan (low penalty); alternating/high-variance direction is
    treated as shake (high penalty), even at the same raw magnitude.
    """
    n = len(vectors)
    half = window // 2
    out = []
    for i in range(n):
        lo, hi = max(0, i - half), min(n, i + half + 1)
        chunk = vectors[lo:hi]
        magnitude = math.hypot(*vectors[i])
        mag_sum = sum(math.hypot(dx, dy) for dx, dy in chunk) or 1e-6
        sx = sum(dx for dx, _ in chunk)
        sy = sum(dy for _, dy in chunk)
        coherence = math.hypot(sx, sy) / mag_sum
        out.append(magnitude * (1.0 - coherence))
    return out


def sample_clip_quality(path: str, duration: float, interval_s: float = SAMPLE_INTERVAL_S) -> list[QualitySample]:
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return []

    raw_points: list[tuple[float, float, float, float, float]] = []
    faces: list[bool] = []
    prev_gray = None

    t = 0.0
    while t < duration:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            t += interval_s
            continue

        h, w = frame.shape[:2]
        scale = CANONICAL_WIDTH / w
        resized = cv2.resize(frame, (CANONICAL_WIDTH, max(1, int(h * scale))))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        dx = dy = 0.0
        if prev_gray is not None and prev_gray.shape == gray.shape:
            try:
                (dx, dy), _response = cv2.phaseCorrelate(np.float32(prev_gray), np.float32(gray))
            except cv2.error:
                dx = dy = 0.0

        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        brightness = float(hsv[:, :, 2].mean())

        raw_points.append((t, sharpness, dx, dy, brightness))
        faces.append(_has_face(resized))
        prev_gray = gray
        t += interval_s

    cap.release()
    if not raw_points:
        return []

    shake_penalties = _rolling_shake_penalty([(dx, dy) for _, _, dx, dy, _ in raw_points])

    return [
        QualitySample(
            t=pt[0],
            sharpness=pt[1],
            shake_penalty=shake_penalties[i],
            brightness=pt[4],
            face_bonus=1.0 if faces[i] else 0.0,
        )
        for i, pt in enumerate(raw_points)
    ]


def score_samples(samples: list[QualitySample]) -> list[float]:
    """Aggregate each sample into one 0-1 score, normalized relative to the
    given batch (pass in every sample across every clip in the current job
    so scoring adapts to that job's own footage quality distribution).
    """
    if not samples:
        return []

    sharpness = np.array([s.sharpness for s in samples])
    shake_penalty = np.array([s.shake_penalty for s in samples])
    brightness = np.array([s.brightness for s in samples])
    face_bonus = np.array([s.face_bonus for s in samples])

    def normalize(arr: np.ndarray) -> np.ndarray:
        lo, hi = np.percentile(arr, [5, 95])
        if hi - lo < 1e-6:
            return np.full_like(arr, 0.5)
        return np.clip((arr - lo) / (hi - lo), 0.0, 1.0)

    sharpness_score = normalize(sharpness)
    shake_score = 1.0 - normalize(shake_penalty)
    brightness_dist = np.clip(np.abs(brightness - 128.0) / 128.0, 0.0, 1.0)
    brightness_score = 1.0 - brightness_dist

    aggregate = (
        SHARPNESS_WEIGHT * sharpness_score
        + SHAKE_WEIGHT * shake_score
        + BRIGHTNESS_WEIGHT * brightness_score
        + FACE_WEIGHT * face_bonus
    )
    return [float(x) for x in np.clip(aggregate, 0.0, 1.0)]
