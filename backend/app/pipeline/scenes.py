"""Milestone 2: scene boundary detection within a single clip.

Uses PySceneDetect's AdaptiveDetector, which mitigates false splits from
handheld camera motion better than a plain content-threshold detector --
relevant here since the target footage is often handheld phone video.
"""

MIN_SCENE_LEN_S = 1.0


def detect_scenes(path: str, min_scene_len_s: float = MIN_SCENE_LEN_S) -> list[tuple[float, float]]:
    from scenedetect import SceneManager, open_video
    from scenedetect.detectors import AdaptiveDetector

    video = open_video(path)
    frame_rate = video.frame_rate or 30.0
    scene_manager = SceneManager()
    scene_manager.add_detector(AdaptiveDetector(min_scene_len=max(1, int(min_scene_len_s * frame_rate))))
    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()

    if not scene_list:
        duration = video.duration.get_seconds() if video.duration else 0.0
        return [(0.0, duration)]

    return [(start.get_seconds(), end.get_seconds()) for start, end in scene_list]
