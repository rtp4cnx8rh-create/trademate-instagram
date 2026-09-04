#!/usr/bin/env python3
"""
Rendert die HTML-Vorlagen aus templates/ zu fertigen Instagram-Bildern.

Gerendert wird mit dem headless Chromium, das in der Umgebung ohnehin liegt;
danach wird auf sRGB-JPEG umgestellt, weil die Graph API PNG zwar annimmt,
JPEG aber deutlich kleiner ausfaellt.

Voraussetzungen: Pillow (pip install pillow) und die Schrift Inter im System.

    python3 render.py templates/post.html  images/KW-37/01-Mo.jpg 1080 1080
    python3 render.py templates/story.html images/stories/2026-09-07.jpg 1080 1920
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent

CHROME_KANDIDATEN = [
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    "/opt/pw-browsers/chromium/chrome-linux/chrome",
    shutil.which("chromium") or "",
    shutil.which("google-chrome") or "",
]


def chrome() -> str:
    for pfad in CHROME_KANDIDATEN:
        if pfad and Path(pfad).is_file():
            return pfad
    sys.exit("Kein Chromium gefunden. Pfad in CHROME_KANDIDATEN ergaenzen.")


def render(vorlage: Path, ziel: Path, breite: int, hoehe: int) -> None:
    ziel.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "shot.png"
        subprocess.run(
            [
                chrome(),
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
                "--allow-file-access-from-files",
                f"--window-size={breite},{hoehe}",
                f"--screenshot={png}",
                vorlage.resolve().as_uri(),
            ],
            check=True,
            capture_output=True,
        )
        bild = Image.open(png).convert("RGB")

    if bild.size != (breite, hoehe):
        bild = bild.resize((breite, hoehe), Image.LANCZOS)
    bild.save(ziel, "JPEG", quality=92, subsampling=0, optimize=True)
    print(f"{ziel}  {bild.size[0]}x{bild.size[1]}  {ziel.stat().st_size // 1024} KB")


def main() -> None:
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    render(Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))


if __name__ == "__main__":
    main()
