"""
Generate TOEIC Speaking Pro icon — 256×256 rounded-square ICO
Upper half : symmetric audio waveform bars
Lower half : "TOEIC" bold sans-serif
Palette    : pure white bg, steel-blue (#4A7BC4) foreground
"""

from PIL import Image, ImageDraw, ImageFont
import math, os, sys

# ── palette ────────────────────────────────────────────────────────────────
BG        = (255, 255, 255, 255)          # pure white
FG        = (58, 110, 185, 255)           # steel blue  #3A6EB9
RADIUS    = 40                            # corner radius
SIZE      = 256

# ── canvas ─────────────────────────────────────────────────────────────────
img  = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# rounded-rectangle background (white)
draw.rounded_rectangle([0, 0, SIZE-1, SIZE-1], radius=RADIUS, fill=BG)

# ── waveform bars (upper half) ──────────────────────────────────────────────
#  7 bars, symmetric, centre bar tallest
BAR_HEIGHTS = [14, 28, 46, 68, 78, 68, 46, 28, 14]   # 9 bars, smoother bell
BAR_W       = 9                               # bar width  (px)
BAR_GAP     = 8                               # gap between bars
N_BARS      = len(BAR_HEIGHTS)
WAVE_CY     = 98                              # vertical centre of wave zone

total_w = N_BARS * BAR_W + (N_BARS - 1) * BAR_GAP
x_start = (SIZE - total_w) // 2

for i, h in enumerate(BAR_HEIGHTS):
    x0 = x_start + i * (BAR_W + BAR_GAP)
    x1 = x0 + BAR_W
    y0 = WAVE_CY - h // 2
    y1 = WAVE_CY + h // 2
    r  = BAR_W // 2
    draw.rounded_rectangle([x0, y0, x1, y1], radius=r, fill=FG)

# ── "TOEIC" text (lower zone) ──────────────────────────────────────────────
TEXT      = "TOEIC"
TEXT_Y    = 162          # top of text zone

# Try system fonts (bold sans-serif), fall back to default
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "C:/Windows/Fonts/arialbd.ttf",
]

font = None
for path in FONT_CANDIDATES:
    if os.path.exists(path):
        try:
            font = ImageFont.truetype(path, size=54)
            print(f"Font: {path}")
            break
        except Exception:
            pass

if font is None:
    # Pillow built-in bitmap fallback — scale up manually
    font = ImageFont.load_default(size=54)
    print("Using built-in font")

# measure & centre
bbox = draw.textbbox((0, 0), TEXT, font=font)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]
tx = (SIZE - tw) // 2 - bbox[0]
ty = TEXT_Y - bbox[1]
draw.text((tx, ty), TEXT, font=font, fill=FG)

# ── separator line ─────────────────────────────────────────────────────────
SEP_Y = 143
draw.line([(36, SEP_Y), (SIZE - 36, SEP_Y)], fill=(*FG[:3], 80), width=1)

# ── export ─────────────────────────────────────────────────────────────────
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
ico_path = os.path.join(OUT_DIR, "app_icon.ico")
png_path = os.path.join(OUT_DIR, "app_icon_256.png")

# Save PNG preview
img.save(png_path, "PNG")
print(f"PNG saved: {png_path}")

# Build multi-size ICO (256, 128, 64, 48, 32, 16)
sizes = [256, 128, 64, 48, 32, 16]
ico_images = []
for s in sizes:
    resized = img.resize((s, s), Image.LANCZOS)
    ico_images.append(resized)

ico_images[0].save(
    ico_path,
    format="ICO",
    sizes=[(s, s) for s in sizes],
    append_images=ico_images[1:],
)
print(f"ICO saved : {ico_path}")
print("Done.")
