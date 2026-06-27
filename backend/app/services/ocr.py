import subprocess
from pathlib import Path
from shutil import which


class OcrUnavailableError(RuntimeError):
    pass


def tesseract_available() -> bool:
    return which("tesseract") is not None


def extract_text_from_image(image_path: str) -> str:
    executable = which("tesseract")
    if executable is None:
        raise OcrUnavailableError(
            "Tesseract OCR is not installed or is not available on PATH."
        )

    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Receipt image not found: {image_path}")

    completed = subprocess.run(
        [executable, str(path), "stdout"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()
