# -*- coding: utf-8 -*-
"""Identité visuelle VOLTIS — logo, marque, favicon."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

NAVY = (10, 31, 60, 255)
NAVY_2 = (16, 45, 82, 255)
NAVY_3 = (22, 58, 102, 255)
AMBER = (245, 179, 1, 255)
AMBER_LIGHT = (255, 205, 74, 255)
TEAL = (22, 166, 161, 255)
WHITE = (255, 255, 255, 255)
MUTED = (150, 172, 196, 255)

FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_SEMI = "C:/Windows/Fonts/seguisb.ttf"
FONT_REG = "C:/Windows/Fonts/segoeui.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", size)


def hexagon(cx: float, cy: float, radius: float, rotation: float = math.pi / 6) -> list[tuple[float, float]]:
    return [
        (cx + radius * math.cos(rotation + index * math.pi / 3), cy + radius * math.sin(rotation + index * math.pi / 3))
        for index in range(6)
    ]


def draw_mark(size: int = 720) -> Image.Image:
    scale = 3
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = int(s * 0.035)
    radius = int(s * 0.24)
    # fond avec dégradé vertical simulé
    d.rounded_rectangle((pad, pad, s - pad, s - pad), radius=radius, fill=NAVY)
    for index in range(30):
        alpha = 255 - index * 4
        y0 = pad + int((s - 2 * pad) * index / 30)
        y1 = pad + int((s - 2 * pad) * (index + 1) / 30) + 1
        d.rounded_rectangle(
            (pad, y0, s - pad, y1),
            radius=radius if index in (0, 29) else 0,
            fill=(14 + index // 3, 40 + index // 2, 78 + index, alpha),
        )
    # halo
    d.ellipse((int(s * 0.12), int(s * 0.12), int(s * 0.88), int(s * 0.88)), outline=(245, 179, 1, 26), width=int(s * 0.012))
    # hexagone
    cx, cy = s / 2, s / 2
    points = hexagon(cx, cy, s * 0.31)
    d.polygon(points, outline=AMBER, width=int(s * 0.018))
    # noeuds aux sommets
    for px, py in points:
        r = s * 0.018
        d.ellipse((px - r, py - r, px + r, py + r), fill=TEAL)
    # éclair
    bolt = [
        (cx + s * 0.055, cy - s * 0.245),
        (cx - s * 0.105, cy + s * 0.015),
        (cx - s * 0.015, cy + s * 0.015),
        (cx - s * 0.055, cy + s * 0.245),
        (cx + s * 0.115, cy - s * 0.025),
        (cx + s * 0.020, cy - s * 0.025),
    ]
    d.polygon(bolt, fill=AMBER)
    # petite étincelle
    d.ellipse((cx + s * 0.235, cy - s * 0.285, cx + s * 0.275, cy - s * 0.245), fill=AMBER_LIGHT)
    return img.resize((size, size), Image.LANCZOS)


def draw_wordmark(dark: bool = True, width: int = 1600, height: int = 420) -> Image.Image:
    scale = 2
    W, H = width * scale, height * scale
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mark = draw_mark(int(H * 0.82))
    img.alpha_composite(mark, (int(H * 0.05), int(H * 0.09)))
    d = ImageDraw.Draw(img)
    x = int(H * 0.96)
    main = WHITE if dark else NAVY
    f1 = font(FONT_BOLD, int(H * 0.30))
    f2 = font(FONT_BOLD, int(H * 0.30))
    f3 = font(FONT_SEMI, int(H * 0.075))
    f4 = font(FONT_REG, int(H * 0.052))
    d.text((x, int(H * 0.12)), "VOLT", font=f1, fill=main)
    volt_w = d.textlength("VOLT", font=f1)
    d.text((x + volt_w, int(H * 0.12)), "IS", font=f2, fill=AMBER)
    d.text((x + 3, int(H * 0.49)), "E N E R G Y   I N T E L L I G E N C E", font=f3, fill=TEAL)
    d.text((x + 2, int(H * 0.63)), "Agentic AI for the Electricity Sector", font=f4,
           fill=(183, 203, 224) if dark else (90, 110, 135))
    d.rounded_rectangle((x, int(H * 0.80), x + int(H * 0.34), int(H * 0.80) + 4), radius=2, fill=AMBER)
    return img.resize((width, height), Image.LANCZOS)


def draw_sidebar_logo(width: int = 1200, height: int = 300) -> Image.Image:
    scale = 2
    W, H = width * scale, height * scale
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mark = draw_mark(int(H * 0.82))
    img.alpha_composite(mark, (int(H * 0.03), int(H * 0.09)))
    d = ImageDraw.Draw(img)
    x = int(H * 0.98)
    f1 = font(FONT_BOLD, int(H * 0.36))
    f2 = font(FONT_BOLD, int(H * 0.36))
    d.text((x, int(H * 0.16)), "VOLT", font=f1, fill=WHITE)
    volt_w = d.textlength("VOLT", font=f1)
    d.text((x + volt_w, int(H * 0.16)), "IS", font=f2, fill=AMBER)
    f3 = font(FONT_SEMI, int(H * 0.095))
    d.text((x + 3, int(H * 0.61)), "E N E R G Y   I N T E L L I G E N C E", font=f3, fill=TEAL)
    return img.resize((width, height), Image.LANCZOS)


def main() -> None:
    mark = draw_mark(720)
    mark.save(ASSETS / "logo_mark.png")
    mark.resize((128, 128), Image.LANCZOS).save(ASSETS / "favicon.png")
    draw_wordmark(dark=True, width=1600, height=420).save(ASSETS / "logo.png")
    draw_wordmark(dark=False, width=1600, height=420).save(ASSETS / "logo_light.png")
    draw_wordmark(dark=False, width=1100, height=290).save(ASSETS / "logo_small.png")
    draw_sidebar_logo().save(ASSETS / "logo_sidebar.png")
    print("Logos générés dans", ASSETS)


if __name__ == "__main__":
    main()
