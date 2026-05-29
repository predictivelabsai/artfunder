"""Compose Kanvas.ai demo screenshots into an animated GIF.

Usage:
    python -m scripts.make_gif
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "screenshots"
OUT_GIF = ROOT / "docs" / "kanvas.gif"

# App-focused tour — skips landing pages (the GIF lives on the landing page).
FRAMES = [
    ("05-chat-empty.png",          1800),
    ("06-chat-artist.png",         3200),
    ("07-chat-market.png",         3200),
    ("08-chat-advise.png",         3200),
    ("09-analytics-empty.png",     1800),
    ("10-analytics-artists.png",   3200),
    ("11-analytics-category.png",  3200),
]

TARGET_W = 1200
TARGET_H = 820
BG = (255, 255, 255)  # white (#FFFFFF)


def load_frame(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    ratio = TARGET_W / img.width
    img = img.resize((TARGET_W, int(img.height * ratio)), Image.LANCZOS)
    if img.height > TARGET_H:
        img = img.crop((0, 0, TARGET_W, TARGET_H))
    else:
        canvas = Image.new("RGB", (TARGET_W, TARGET_H), BG)
        canvas.paste(img, (0, 0))
        img = canvas
    return img


def main() -> None:
    frames: list[Image.Image] = []
    durations: list[int] = []
    for fname, dur in FRAMES:
        p = SHOTS / fname
        if not p.exists():
            print(f"  skip (missing): {p}")
            continue
        frames.append(load_frame(p))
        durations.append(dur)
        print(f"  added {fname}  ({dur} ms)")

    if not frames:
        raise SystemExit("No frames found -- run scripts/capture_screenshots.py first.")

    OUT_GIF.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUT_GIF,
        save_all=True,
        append_images=frames[1:],
        optimize=True,
        duration=durations,
        loop=0,
        disposal=2,
    )
    print(f"\nWrote {OUT_GIF}  ({OUT_GIF.stat().st_size / 1024:.1f} KB, {len(frames)} frames)")


if __name__ == "__main__":
    main()
