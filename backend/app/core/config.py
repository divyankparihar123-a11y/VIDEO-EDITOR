import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AARS_", env_file=".env", extra="ignore")

    STORAGE_DIR: Path = Path(__file__).resolve().parents[2] / "storage"
    DB_PATH: Path = STORAGE_DIR / "app.db"
    MAX_CONCURRENT_JOBS: int = 1

    def model_post_init(self, __context) -> None:
        self.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.DB_PATH = self.STORAGE_DIR / "app.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

_RESOLVED_BINARIES: tuple[str, str] | None = None


def _find_winget_gyan_ffmpeg() -> tuple[str, str] | None:
    packages_root = Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
    if not packages_root.is_dir():
        return None

    candidates: list[Path] = []
    for pkg_dir in packages_root.glob("Gyan.FFmpeg_*"):
        for build_dir in pkg_dir.glob("ffmpeg-*-full_build"):
            ffmpeg_exe = build_dir / "bin" / "ffmpeg.exe"
            ffprobe_exe = build_dir / "bin" / "ffprobe.exe"
            if ffmpeg_exe.is_file() and ffprobe_exe.is_file():
                candidates.append(build_dir)

    if not candidates:
        return None

    newest = max(candidates, key=lambda p: p.stat().st_mtime)
    return (
        str(newest / "bin" / "ffmpeg.exe"),
        str(newest / "bin" / "ffprobe.exe"),
    )


def resolve_ffmpeg_binaries() -> tuple[str, str]:
    global _RESOLVED_BINARIES
    if _RESOLVED_BINARIES is not None:
        return _RESOLVED_BINARIES

    which_ffmpeg = shutil.which("ffmpeg")
    which_ffprobe = shutil.which("ffprobe")
    if which_ffmpeg and which_ffprobe:
        _RESOLVED_BINARIES = (which_ffmpeg, which_ffprobe)
        return _RESOLVED_BINARIES

    found = _find_winget_gyan_ffmpeg()
    if found is not None:
        _RESOLVED_BINARIES = found
        return _RESOLVED_BINARIES

    env_ffmpeg = os.environ.get("FFMPEG_BINARY")
    env_ffprobe = os.environ.get("FFPROBE_BINARY")
    if env_ffmpeg and env_ffprobe and Path(env_ffmpeg).is_file() and Path(env_ffprobe).is_file():
        _RESOLVED_BINARIES = (env_ffmpeg, env_ffprobe)
        return _RESOLVED_BINARIES

    raise RuntimeError(
        "Could not locate ffmpeg/ffprobe binaries. Install ffmpeg with "
        "'winget install Gyan.FFmpeg', ensure it is on PATH, or set the "
        "FFMPEG_BINARY and FFPROBE_BINARY environment variables to the "
        "full paths of ffmpeg.exe and ffprobe.exe."
    )


def ffmpeg_version(ffmpeg_path: str) -> str:
    result = subprocess.run(
        [ffmpeg_path, "-version"],
        capture_output=True,
        text=True,
        check=False,
    )
    first_line = (result.stdout or "").splitlines()[0] if result.stdout else "unknown"
    return first_line.strip()


def detect_nvenc(ffmpeg_path: str) -> bool:
    # Check if encoder is compiled in
    res = subprocess.run(
        [ffmpeg_path, "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        check=False,
    )
    if "h264_nvenc" not in (res.stdout or ""):
        return False

    # Test if GPU driver actually supports the NVENC API version
    test_cmd = [
        ffmpeg_path, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "color=c=black:s=64x64:d=0.1",
        "-c:v", "h264_nvenc",
        "-f", "null", "-",
    ]
    test_res = subprocess.run(test_cmd, capture_output=True, text=True, check=False)
    return test_res.returncode == 0


def detect_libass(ffmpeg_path: str) -> bool:
    result = subprocess.run(
        [ffmpeg_path, "-hide_banner", "-version"],
        capture_output=True,
        text=True,
        check=False,
    )
    return "--enable-libass" in (result.stdout or "")


def get_env_report() -> dict:
    report: dict = {
        "ffmpeg_path": None,
        "ffprobe_path": None,
        "ffmpeg_version": None,
        "nvenc_available": False,
        "libass_available": False,
        "faster_whisper": {"importable": False, "detail": "not checked"},
        "errors": [],
    }

    try:
        ffmpeg_path, ffprobe_path = resolve_ffmpeg_binaries()
        report["ffmpeg_path"] = ffmpeg_path
        report["ffprobe_path"] = ffprobe_path
        report["ffmpeg_version"] = ffmpeg_version(ffmpeg_path)
        report["nvenc_available"] = detect_nvenc(ffmpeg_path)
        report["libass_available"] = detect_libass(ffmpeg_path)
    except RuntimeError as exc:
        report["errors"].append(str(exc))

    try:
        import faster_whisper  # noqa: F401

        report["faster_whisper"] = {
            "importable": True,
            "detail": f"faster-whisper {getattr(faster_whisper, '__version__', 'unknown version')}",
        }
    except ImportError as exc:
        report["faster_whisper"] = {
            "importable": False,
            "detail": f"not installed yet ({exc})",
        }

    return report
