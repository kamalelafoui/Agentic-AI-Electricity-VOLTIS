# -*- coding: utf-8 -*-
"""Helpers de design pour la présentation VOLTIS (python-pptx)."""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

NAVY = RGBColor(0x0A, 0x1F, 0x3C)
NAVY2 = RGBColor(0x14, 0x36, 0x5C)
NAVY3 = RGBColor(0x1D, 0x4B, 0x78)
AMBER = RGBColor(0xF5, 0xB3, 0x01)
AMBER_LIGHT = RGBColor(0xFF, 0xD1, 0x5C)
TEAL = RGBColor(0x16, 0xA6, 0xA1)
BLUE = RGBColor(0x3B, 0x82, 0xC4)
GREEN = RGBColor(0x2E, 0x8B, 0x72)
RED = RGBColor(0xD9, 0x53, 0x4F)
PURPLE = RGBColor(0x7A, 0x5A, 0xA6)
MUTED = RGBColor(0x64, 0x74, 0x8B)
INK = RGBColor(0x12, 0x26, 0x3F)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BG = RGBColor(0xF4, 0xF7, 0xFB)
LIGHT = RGBColor(0xEA, 0xF2, 0xFA)
BORDER = RGBColor(0xDC, 0xE7, 0xF2)
SOFT_GOLD = RGBColor(0xFF, 0xF7, 0xE0)
SOFT_RED = RGBColor(0xFD, 0xEC, 0xEA)
SOFT_GREEN = RGBColor(0xEA, 0xF8, 0xF4)

TITLE_FONT = "Aptos Display"
BODY_FONT = "Aptos"


def new_deck() -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def blank(prs: Presentation):
    return prs.slides.add_slide(prs.slide_layouts[6])


def rect(slide, x, y, w, h, fill, line=None, radius=None, shadow=False, shape=MSO_SHAPE.RECTANGLE):
    shp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(0.8)
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            shp.adjustments[0] = radius
        except Exception:
            pass
    if not shadow:
        shp.shadow.inherit = False
    shp.text_frame.text = ""
    return shp


def line(slide, x1, y1, x2, y2, color=AMBER, width=1.5, dash=False):
    from pptx.enum.dml import MSO_LINE_DASH_STYLE
    from pptx.enum.shapes import MSO_CONNECTOR

    connector = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    connector.line.color.rgb = color
    connector.line.width = Pt(width)
    if dash:
        connector.line.dash_style = MSO_LINE_DASH_STYLE.DASH


def txt(
    slide, x, y, w, h, text, size=16, color=INK, bold=False, font=BODY_FONT,
    align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False, line_spacing=1.0,
    margins=(0.02, 0.02, 0.02, 0.02), char_spacing=None,
):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(margins[0])
    tf.margin_right = Inches(margins[1])
    tf.margin_top = Inches(margins[2])
    tf.margin_bottom = Inches(margins[3])
    tf.vertical_anchor = anchor
    lines = str(text).split("\n")
    for index, line in enumerate(lines):
        p = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        run = p.add_run()
        run.text = line
        run.font.name = font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = color
        if char_spacing is not None:
            from pptx.oxml.ns import qn

            run._r.get_or_add_rPr().set("spc", str(int(char_spacing * 100)))
    return box


def rich(slide, x, y, w, h, segments: Sequence[tuple[str, dict]], size=16, color=INK,
         font=BODY_FONT, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.0):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(0.02)
    tf.margin_right = Inches(0.02)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    for text, opts in segments:
        run = p.add_run()
        run.text = text
        run.font.name = opts.get("font", font)
        run.font.size = Pt(opts.get("size", size))
        run.font.bold = opts.get("bold", False)
        run.font.italic = opts.get("italic", False)
        run.font.color.rgb = opts.get("color", color)
    return box


def paragraphs(slide, x, y, w, h, items: Sequence[tuple[str, str]], size=15, color=INK,
               bullet_color=AMBER, space_after=7, line_spacing=1.05, lead_color=NAVY):
    """items = [(texte_gras, texte_normal), ...]"""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = Inches(0.02)
    tf.margin_right = Inches(0.02)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    for index, (lead, body) in enumerate(items):
        p = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        run = p.add_run()
        run.text = "•  "
        run.font.name = BODY_FONT
        run.font.size = Pt(size)
        run.font.bold = True
        run.font.color.rgb = bullet_color
        if lead:
            run = p.add_run()
            run.text = lead
            run.font.name = BODY_FONT
            run.font.size = Pt(size)
            run.font.bold = True
            run.font.color.rgb = lead_color
        if body:
            run = p.add_run()
            run.text = body
            run.font.name = BODY_FONT
            run.font.size = Pt(size)
            run.font.color.rgb = color
    return box


def bg(slide, color=BG):
    rect(slide, 0, 0, 13.333, 7.5, color)
    rect(slide, 12.15, -0.7, 2.0, 2.0, RGBColor(0xE6, 0xEF, 0xFA), shape=MSO_SHAPE.OVAL)
    rect(slide, -0.6, 6.55, 1.5, 1.5, RGBColor(0xFD, 0xF3, 0xD6), shape=MSO_SHAPE.OVAL)


def header(slide, kicker, title, day="", subtitle=""):
    bg(slide)
    rect(slide, 0, 0, 0.16, 7.5, AMBER)
    txt(slide, 0.55, 0.32, 10.8, 0.28, kicker.upper(), 8.5, AMBER, True, char_spacing=2)
    txt(slide, 0.55, 0.60, 11.9, 0.85, title, 26, NAVY, True, TITLE_FONT, line_spacing=0.95)
    if subtitle:
        txt(slide, 0.55, 1.48, 11.7, 0.45, subtitle, 11.5, MUTED)
    if day:
        pill_width = max(0.80, min(1.70, 0.10 * len(day) + 0.55))
        pill(slide, 12.75 - pill_width, 0.34, pill_width, 0.32, day, NAVY, WHITE, 7.2)


def footer(slide, number, total=26, label="VOLTIS · Agentic AI for the Electricity Sector"):
    line(slide, 0.55, 7.04, 12.78, 7.04, BORDER, 0.8)
    txt(slide, 0.55, 7.10, 8.8, 0.24, label, 7.5, MUTED)
    txt(slide, 12.0, 7.10, 0.8, 0.24, f"{number:02d} / {total:02d}", 7.5, MUTED, align=PP_ALIGN.RIGHT)


def pill(slide, x, y, w, h, text, fill=NAVY, color=WHITE, size=8.5, bold=True, line_color=None):
    shp = rect(slide, x, y, w, h, fill, line=line_color, radius=0.5, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    tf = shp.text_frame
    tf.clear()
    tf.margin_left = Inches(0.03)
    tf.margin_right = Inches(0.03)
    tf.margin_top = Inches(0.01)
    tf.margin_bottom = Inches(0.01)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    run.font.name = BODY_FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return shp


def card(slide, x, y, w, h, title, body="", accent=AMBER, icon="", tag="", body_size=12, title_size=14.5):
    rect(slide, x, y, w, h, WHITE, line=BORDER, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(slide, x, y, 0.07, h, accent)
    if icon:
        txt(slide, x + 0.16, y + 0.12, 0.5, 0.4, icon, 17, NAVY, True)
    txt(slide, x + (0.68 if icon else 0.22), y + 0.14, w - (0.88 if icon else 0.42), 0.55,
        title, title_size, NAVY, True, line_spacing=0.95)
    if body:
        body_height = max(0.06, h - 0.92)
        txt(slide, x + 0.22, y + 0.72, w - 0.42, body_height, body, body_size, MUTED, line_spacing=1.05)
    if tag:
        txt(slide, x + 0.22, y + h - 0.34, w - 0.42, 0.24, tag, 8, accent, True)


def stat(slide, x, y, w, h, value, label, accent=TEAL, sub="", value_size=28):
    rect(slide, x, y, w, h, WHITE, line=BORDER, radius=0.08, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(slide, x, y, w, 0.06, accent)
    txt(slide, x + 0.16, y + 0.14, w - 0.28, 0.55, value, value_size, NAVY, True, TITLE_FONT, line_spacing=0.9)
    txt(slide, x + 0.16, y + 0.72, w - 0.28, 0.35, label, 8.8, MUTED, True)
    if sub:
        txt(slide, x + 0.16, y + h - 0.32, w - 0.28, 0.24, sub, 7.8, accent, True)


def image(slide, path: Path, x, y, w=None, h=None):
    kwargs = {}
    if w:
        kwargs["width"] = Inches(w)
    if h:
        kwargs["height"] = Inches(h)
    return slide.shapes.add_picture(str(path), Inches(x), Inches(y), **kwargs)


def code(slide, x, y, w, h, text, size=10, lang="python"):
    rect(slide, x, y, w, h, RGBColor(0x08, 0x1B, 0x30), radius=0.05, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(slide, x, y, w, 0.26, RGBColor(0x10, 0x2A, 0x48), radius=0.05, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    txt(slide, x + 0.13, y + 0.045, w - 0.26, 0.18, lang.upper(), 7, AMBER, True, char_spacing=1.5)
    txt(slide, x + 0.16, y + 0.34, w - 0.28, h - 0.40, text, size, RGBColor(0xE7, 0xEF, 0xF8),
        font="Consolas", line_spacing=0.95)


def table(slide, x, y, w, h, headers, rows, col_widths=None, font_size=9.5, header_fill=NAVY):
    shape = slide.shapes.add_table(len(rows) + 1, len(headers), Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = shape.table
    if col_widths:
        for index, width in enumerate(col_widths):
            tbl.columns[index].width = Inches(width)
    for index, head in enumerate(headers):
        cell = tbl.cell(0, index)
        cell.text = ""
        cell.fill.solid()
        cell.fill.fore_color.rgb = header_fill
        p = cell.text_frame.paragraphs[0]
        run = p.add_run()
        run.text = head
        run.font.name = BODY_FONT
        run.font.size = Pt(font_size)
        run.font.bold = True
        run.font.color.rgb = WHITE
        cell.margin_left = Inches(0.07)
        cell.margin_right = Inches(0.05)
        cell.margin_top = Inches(0.03)
        cell.margin_bottom = Inches(0.03)
    for row_index, row in enumerate(rows, 1):
        for column, value in enumerate(row):
            cell = tbl.cell(row_index, column)
            cell.text = ""
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if row_index % 2 else RGBColor(0xF4, 0xF7, 0xFB)
            p = cell.text_frame.paragraphs[0]
            run = p.add_run()
            run.text = str(value)
            run.font.name = BODY_FONT
            run.font.size = Pt(font_size)
            run.font.color.rgb = INK
            cell.margin_left = Inches(0.07)
            cell.margin_right = Inches(0.05)
            cell.margin_top = Inches(0.02)
            cell.margin_bottom = Inches(0.02)
    return tbl


def notes(slide, text: str):
    slide.notes_slide.notes_text_frame.text = text


def cover(prs, kicker, title, subtitle, meta, chips):
    slide = blank(prs)
    rect(slide, 0, 0, 13.333, 7.5, NAVY)
    rect(slide, 9.4, -1.8, 5.6, 5.6, RGBColor(0x12, 0x3A, 0x60), shape=MSO_SHAPE.OVAL)
    rect(slide, 10.8, 4.0, 2.9, 2.9, RGBColor(0x0F, 0x31, 0x55), shape=MSO_SHAPE.OVAL)
    rect(slide, 10.0, 0.2, 3.1, 3.1, RGBColor(0xF5, 0xB3, 0x01), shape=MSO_SHAPE.OVAL)
    rect(slide, 8.8, -0.3, 3.3, 3.3, NAVY, shape=MSO_SHAPE.OVAL)
    # réseau décoratif
    for x1, y1, x2, y2 in [(10.6, 2.2, 12.1, 3.4), (10.6, 2.2, 9.8, 4.1), (12.1, 3.4, 12.6, 5.1), (9.8, 4.1, 11.2, 5.4)]:
        line(slide, x1, y1, x2, y2, RGBColor(0x2A, 0x52, 0x77), 1.0)
    for cx, cy in [(10.6, 2.2), (12.1, 3.4), (9.8, 4.1), (12.6, 5.1), (11.2, 5.4)]:
        rect(slide, cx - 0.06, cy - 0.06, 0.12, 0.12, TEAL, shape=MSO_SHAPE.OVAL)
    image(slide, ASSETS / "logo.png", 0.55, 0.40, w=3.4)
    txt(slide, 0.62, 2.05, 8.6, 0.28, kicker.upper(), 9, AMBER, True, char_spacing=2.5)
    txt(slide, 0.62, 2.42, 8.6, 1.55, title, 33, WHITE, True, TITLE_FONT, line_spacing=0.92)
    txt(slide, 0.62, 4.15, 8.4, 0.8, subtitle, 13.5, RGBColor(0xC9, 0xD8, 0xE8), line_spacing=1.08)
    for index, chip in enumerate(chips):
        pill(slide, 0.62 + index * 2.35, 5.35, 2.12, 0.33, chip, RGBColor(0x16, 0x3A, 0x5D), WHITE, 8.5,
             line_color=RGBColor(0x2A, 0x52, 0x77))
    line(slide, 0.62, 6.45, 8.5, 6.45, RGBColor(0x2A, 0x52, 0x77), 0.8)
    txt(slide, 0.62, 6.58, 8.5, 0.35, meta, 8.5, RGBColor(0x9F, 0xB8, 0xD0))
    return slide


def section(prs, kicker, title, subtitle="", day="", number=0, total=26):
    slide = blank(prs)
    bg(slide)
    rect(slide, 0, 0, 0.16, 7.5, AMBER)
    txt(slide, 0.55, 1.05, 11.4, 0.32, kicker.upper(), 9, AMBER, True, char_spacing=2)
    txt(slide, 0.55, 1.48, 11.4, 1.5, title, 31, NAVY, True, TITLE_FONT, line_spacing=0.95)
    if subtitle:
        txt(slide, 0.55, 3.10, 10.2, 0.8, subtitle, 13.5, MUTED, line_spacing=1.15)
    if day:
        pill_width = max(0.80, min(1.70, 0.10 * len(day) + 0.55))
        pill(slide, 12.75 - pill_width, 0.34, pill_width, 0.32, day, NAVY, WHITE, 7.2)
    footer(slide, number, total)
    return slide
