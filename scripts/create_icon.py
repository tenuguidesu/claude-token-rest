"""
.icns アイコンを生成する。
ビルド時に scripts/create_icon.py として実行する。
"""

import os
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("pillow が必要です: pip install pillow")

ASSETS = Path(__file__).parent.parent / "assets"
ICONSET = ASSETS / "icon.iconset"
ICNS = ASSETS / "icon.icns"

SIZES = [16, 32, 64, 128, 256, 512, 1024]
BG   = (79, 70, 229)   # indigo-600
FG   = (255, 255, 255)


def _draw(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    pad = max(1, size // 8)
    d.ellipse([pad, pad, size - pad, size - pad], fill=BG)

    # 文字 "C" を中央に描く
    font_size = max(4, int(size * 0.45))
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except Exception:
        font = ImageFont.load_default()

    bbox = d.textbbox((0, 0), "C", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1]
    d.text((x, y), "C", fill=FG, font=font)
    return img


def main() -> None:
    ICONSET.mkdir(parents=True, exist_ok=True)

    for s in SIZES:
        img = _draw(s)
        img.save(ICONSET / f"icon_{s}x{s}.png")
        if s <= 512:
            img2 = img.resize((s * 2, s * 2), Image.LANCZOS)
            img2.save(ICONSET / f"icon_{s}x{s}@2x.png")

    result = subprocess.run(
        ["iconutil", "-c", "icns", str(ICONSET), "-o", str(ICNS)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.exit(f"iconutil failed: {result.stderr}")

    print(f"Icon generated: {ICNS}")


if __name__ == "__main__":
    main()
