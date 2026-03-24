#!/usr/bin/env python3
"""
TOEIC Speaking Pro — icon generator.

Draws a crisp 256×256 microphone icon, saves as:
  app_icon.ico  (multi-size: 16 / 24 / 32 / 48 / 64 / 128 / 256 px)

Design:
  • Background  : soft light-blue rounded card  #EBF1FF → #F5F7FA
  • Mic capsule : solid dark-blue pill           #003087
  • Grille lines: subtle white lines inside capsule
  • Stand + base: matching dark-blue lines
  • Sound waves : 3 transparent arcs each side, dark-blue with opacity
"""

import math
import os

from PIL import Image, ImageDraw, ImageFilter

# ── Draw scale (internal resolution, scaled to 256 at save time) ─────────────
DRAW_SZ = 512          # draw at 2× then Lanczos-down → sharp edges
S       = DRAW_SZ
HALF    = S // 2
K       = DRAW_SZ / 256   # scale factor for coordinates

# ── Palette ────────────────────────────────────────────────────────────────────
BLUE        = (0,   48, 135, 255)    # #003087
BLUE_A      = lambda a: (0, 48, 135, a)
WHITE_A     = lambda a: (255, 255, 255, a)
BG_TOP      = (235, 241, 255, 255)   # #EBF1FF  light cornflower blue
BG_BOT      = (245, 247, 250, 255)   # #F5F7FA  near-white


def _rounded_rect(draw: ImageDraw.ImageDraw,
                  xy: tuple, radius: int, fill, outline=None, outline_w=1):
    """Draw a rounded rectangle on *draw*."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius,
                            fill=fill, outline=outline, width=outline_w)


def _draw_icon(size: int = DRAW_SZ) -> Image.Image:
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    k    = size / 256          # coordinate scale for this resolution

    def k_(v):
        return int(round(v * k))

    # ── Background gradient (approximated as two-stop linear) ─────────────
    # Build a vertical gradient image and paste it masked with rounded rect
    grad = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for y in range(size):
        t   = y / (size - 1)
        r   = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t)
        g   = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t)
        b   = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t)
        grad.paste((r, g, b, 255), [0, y, size, y + 1])

    mask   = Image.new("L", (size, size), 0)
    m_draw = ImageDraw.Draw(mask)
    bg_r   = k_(44)
    m_draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=bg_r, fill=255)
    img.paste(grad, mask=mask)

    # Subtle border
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=bg_r,
                            fill=None, outline=(192, 210, 240, 160), width=k_(1))

    # ── Microphone capsule ─────────────────────────────────────────────────
    cx      = size // 2
    mic_top = k_(42)
    mic_w   = k_(54)
    mic_h   = k_(90)
    mic_r   = mic_w // 2          # fully rounded (pill shape)
    mic_l   = cx - mic_w // 2
    mic_r_x = cx + mic_w // 2
    mic_bot = mic_top + mic_h

    # Pill shadow (soft, behind capsule)
    shadow_pad = k_(4)
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd     = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        [mic_l - shadow_pad, mic_top - shadow_pad + k_(6),
         mic_r_x + shadow_pad, mic_bot + shadow_pad + k_(6)],
        radius=mic_r + shadow_pad,
        fill=(0, 48, 135, 60),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=k_(7)))
    img.alpha_composite(shadow)
    draw = ImageDraw.Draw(img)   # refresh after composite

    # Capsule fill
    draw.rounded_rectangle(
        [mic_l, mic_top, mic_r_x, mic_bot],
        radius=mic_r,
        fill=BLUE,
    )

    # Highlight gradient on capsule (left quarter-strip, white)
    hl_w  = k_(9)
    hl_l  = mic_l + k_(10)
    hl_t  = mic_top + k_(18)
    hl_b  = mic_bot - k_(22)
    for x in range(hl_w):
        alpha = int(38 * (1 - x / hl_w))
        draw.line([(hl_l + x, hl_t), (hl_l + x, hl_b)],
                  fill=WHITE_A(alpha), width=1)

    # Grille lines (3 horizontal semi-transparent white lines)
    grill_mx = k_(11)
    line_w   = max(1, k_(3))
    for offset in [-k_(15), 0, k_(15)]:
        gy = mic_top + mic_h // 2 + offset
        draw.line(
            [(mic_l + grill_mx, gy), (mic_r_x - grill_mx, gy)],
            fill=WHITE_A(80),
            width=line_w,
        )

    # ── Stand (U-shape + pole + base) ──────────────────────────────────────
    arm_w    = max(3, k_(8))
    arc_half = k_(26)            # half-width of the U opening
    arm_top  = mic_bot - k_(2)   # slight overlap so no gap
    arc_cy   = arm_top + k_(30)  # center-y of the U arc circle
    arc_r_s  = arc_half          # arc circle radius = half-width

    # Left vertical arm
    draw.rectangle(
        [cx - arc_half - arm_w // 2, arm_top,
         cx - arc_half + arm_w // 2, arc_cy],
        fill=BLUE,
    )
    # Right vertical arm
    draw.rectangle(
        [cx + arc_half - arm_w // 2, arm_top,
         cx + arc_half + arm_w // 2, arc_cy],
        fill=BLUE,
    )

    # U-bottom arc: draw filled ellipse arc (semicircle bottom half)
    arc_box = [
        cx - arc_half - arm_w // 2,
        arc_cy - arc_r_s,
        cx + arc_half + arm_w // 2,
        arc_cy + arc_r_s,
    ]
    draw.arc(arc_box, start=0, end=180, fill=BLUE, width=arm_w)

    # Pole
    pole_top = arc_cy + arc_r_s - k_(1)
    pole_bot = pole_top + k_(20)
    draw.rectangle(
        [cx - arm_w // 2, pole_top, cx + arm_w // 2, pole_bot],
        fill=BLUE,
    )

    # Base (horizontal bar)
    base_w = k_(60)
    base_y = pole_bot + k_(1)
    draw.rounded_rectangle(
        [cx - base_w // 2, base_y,
         cx + base_w // 2, base_y + arm_w],
        radius=arm_w // 2,
        fill=BLUE,
    )

    # ── Sound waves (concentric arcs, both sides) ─────────────────────────
    wave_cy  = mic_top + mic_h // 2   # vertical center of mic capsule
    wave_defs = [                      # (radius, alpha)
        (k_(36), 210),
        (k_(50), 150),
        (k_(64),  80),
    ]
    wave_w = max(2, k_(4))

    for r, alpha in wave_defs:
        col = BLUE_A(alpha)
        # Right-facing arcs: PIL angles clockwise; 300→360→60 = right side
        draw.arc(
            [cx - r, wave_cy - r, cx + r, wave_cy + r],
            start=300, end=60,
            fill=col, width=wave_w,
        )
        # Left-facing arcs: 120→180→240 = left side
        draw.arc(
            [cx - r, wave_cy - r, cx + r, wave_cy + r],
            start=120, end=240,
            fill=col, width=wave_w,
        )

    return img


def build_ico(out_path: str):
    base    = _draw_icon(DRAW_SZ)           # draw at 512×512
    sizes   = [16, 24, 32, 48, 64, 128, 256]

    # Pillow ICO: save the 256-px version with sizes= so PIL generates all resolutions
    img256 = base.resize((256, 256), Image.LANCZOS)
    img256.save(
        out_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
    )
    print(f"[icon] Saved {out_path}  ({len(sizes)} sizes: {sizes})")

    # Also save a 256×256 PNG for quick preview
    png_path = out_path.replace(".ico", "_preview.png")
    img256.save(png_path, "PNG")
    print(f"[icon] Preview PNG: {png_path}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(base_dir, "app_icon.ico")
    build_ico(ico_path)
