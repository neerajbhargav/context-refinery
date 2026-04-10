"""
Generate Tauri app icons from a source PNG.

Usage:
    python scripts/generate-icons.py [source_png]

If no source PNG is provided, generates placeholder icons with the CR logo.
Requires Pillow: pip install Pillow
"""

import sys
from pathlib import Path

ICONS_DIR = Path(__file__).parent.parent / "src-tauri" / "icons"
SIZES = {
    "32x32.png": 32,
    "128x128.png": 128,
    "128x128@2x.png": 256,
}


def generate_placeholder(size: int):
    """Generate a simple purple gradient placeholder icon."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Purple gradient background with rounded rect
    for y in range(size):
        r = int(100 + (y / size) * 24)
        g = int(40 + (y / size) * 18)
        b = int(200 + (y / size) * 37)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    # Add "CR" text
    try:
        font_size = max(size // 3, 10)
        font = ImageFont.truetype("arial.ttf", font_size)
    except (OSError, IOError):
        font = ImageFont.load_default()

    text = "CR"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) // 2
    y = (size - th) // 2
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    return img


def main():
    ICONS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from PIL import Image
    except ImportError:
        print("Pillow not installed. Creating empty placeholder files.")
        print("Install Pillow for proper icon generation: pip install Pillow")
        for name in SIZES:
            (ICONS_DIR / name).touch()
        # Create empty .ico and .icns
        (ICONS_DIR / "icon.ico").touch()
        (ICONS_DIR / "icon.icns").touch()
        return

    if len(sys.argv) > 1:
        source = Image.open(sys.argv[1]).convert("RGBA")
        for name, size in SIZES.items():
            resized = source.resize((size, size), Image.LANCZOS)
            resized.save(ICONS_DIR / name)
            print(f"  Created {name} ({size}x{size})")
    else:
        for name, size in SIZES.items():
            img = generate_placeholder(size)
            img.save(ICONS_DIR / name)
            print(f"  Created placeholder {name} ({size}x{size})")

    # Generate .ico (Windows)
    source = Image.open(ICONS_DIR / "128x128@2x.png")
    source.save(
        ICONS_DIR / "icon.ico",
        format="ICO",
        sizes=[(32, 32), (64, 64), (128, 128), (256, 256)],
    )
    print("  Created icon.ico")

    # Generate .icns placeholder (macOS) — just copy the 256px PNG
    # Real .icns generation needs iconutil on macOS
    import shutil
    shutil.copy(ICONS_DIR / "128x128@2x.png", ICONS_DIR / "icon.icns")
    print("  Created icon.icns (PNG copy — use iconutil on macOS for real .icns)")

    print(f"\nAll icons saved to {ICONS_DIR}")


if __name__ == "__main__":
    main()
