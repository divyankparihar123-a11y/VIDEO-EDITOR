import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_env_report  # noqa: E402


def _print_header(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> None:
    report = get_env_report()

    _print_header("ffmpeg / ffprobe")
    if report["errors"]:
        for err in report["errors"]:
            print(f"  ERROR: {err}")
    else:
        print(f"  ffmpeg path : {report['ffmpeg_path']}")
        print(f"  ffprobe path: {report['ffprobe_path']}")
        print(f"  version     : {report['ffmpeg_version']}")

    _print_header("NVENC (h264_nvenc)")
    print(f"  available: {report['nvenc_available']}")

    _print_header("libass")
    print(f"  available: {report['libass_available']}")

    _print_header("faster-whisper")
    fw = report["faster_whisper"]
    print(f"  importable: {fw['importable']}")
    print(f"  detail    : {fw['detail']}")

    if fw["importable"]:
        try:
            from faster_whisper import WhisperModel

            WhisperModel("small", device="cuda", compute_type="int8_float16")
            print("  model load: OK on CUDA (device='cuda', compute_type='int8_float16')")
        except Exception as cuda_exc:  # noqa: BLE001 - report any failure reason, then try cpu fallback
            print(f"  model load: CUDA attempt failed ({cuda_exc})")
            try:
                from faster_whisper import WhisperModel

                WhisperModel("small", device="cpu", compute_type="int8")
                print("  model load: OK on CPU fallback (device='cpu', compute_type='int8')")
            except Exception as cpu_exc:  # noqa: BLE001 - never crash the report script
                print(f"  model load: CPU fallback also failed ({cpu_exc})")
    else:
        print("  model load: skipped, faster-whisper not installed yet")

    print()


if __name__ == "__main__":
    main()
