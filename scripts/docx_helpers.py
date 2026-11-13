# -*- coding: utf-8 -*-
"""Helpers de mise en page python-docx pour la documentation VOLTIS."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

NAVY = RGBColor(0x0A, 0x1F, 0x3C)
NAVY_HEX = "0A1F3C"
NAVY2 = RGBColor(0x14, 0x36, 0x5C)
AMBER = RGBColor(0xF5, 0xB3, 0x01)
AMBER_HEX = "F5B301"
TEAL = RGBColor(0x16, 0xA6, 0xA1)
TEAL_HEX = "16A6A1"
BLUE = RGBColor(0x3B, 0x82, 0xC4)
GREEN = RGBColor(0x2E, 0x8B, 0x72)
RED = RGBColor(0xD9, 0x53, 0x4F)
MUTED = RGBColor(0x64, 0x74, 0x8B)
INK = RGBColor(0x12, 0x26, 0x3F)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_HEX = "F4F7FB"
BORDER_HEX = "DCE7F2"
FONT = "Aptos"
FONT_DISPLAY = "Aptos Display"
FONT_MONO = "Consolas"


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_margins(cell, top=55, start=85, bottom=55, end=85) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for tag, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{tag}"))
        if node is None:
            node = OxmlElement(f"w:{tag}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table, color=BORDER_HEX, size=4) -> None:
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), str(size))
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)
        borders.append(element)
    tbl_pr.append(borders)


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def keep_row_together(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    cant_split.set(qn("w:val"), "true")
    tr_pr.append(cant_split)


def add_page_number(paragraph) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(end)


def add_toc(paragraph) -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-2" \\h \\z \\u'
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(separate)
    run._r.append(end)


def set_character_spacing(run, twips: int = 20) -> None:
    r_pr = run._r.get_or_add_rPr()
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:val"), str(twips))
    r_pr.append(spacing)


def set_paragraph_border(paragraph, color=AMBER_HEX, size=12, position="bottom") -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    border = OxmlElement(f"w:{position}")
    border.set(qn("w:val"), "single")
    border.set(qn("w:sz"), str(size))
    border.set(qn("w:space"), "6")
    border.set(qn("w:color"), color)
    p_bdr.append(border)
    p_pr.append(p_bdr)


def new_document(
    title: str,
    subject: str,
    header_label: str,
    author: str = "Direction Digitale & Exploitation — VOLTIS",
    version: str = "1.0.0 — version finale",
    date: str = "12 novembre 2026",
) -> Document:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.header_distance = Cm(0.75)
    section.footer_distance = Cm(0.75)

    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(10.2)
    normal.font.color.rgb = INK
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.12
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    for name, size, color, before, after in (
        ("Heading 1", 18, NAVY, 12, 7),
        ("Heading 2", 13.5, NAVY2, 10, 5),
        ("Heading 3", 11.3, BLUE, 8, 4),
    ):
        style = doc.styles[name]
        style.font.name = FONT_DISPLAY
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = color
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    for name in ("List Bullet", "List Number"):
        style = doc.styles[name]
        style.font.name = FONT
        style.font.size = Pt(10.2)
        style.paragraph_format.space_after = Pt(3)

    header = section.header
    header.is_linked_to_previous = False
    hp = header.paragraphs[0]
    hp.paragraph_format.tab_stops.clear_all()
    hp.paragraph_format.tab_stops.add_tab_stop(Cm(17), WD_TAB_ALIGNMENT.RIGHT)
    if (ASSETS / "logo_mark.png").exists():
        run = hp.add_run()
        run.add_picture(str(ASSETS / "logo_mark.png"), width=Cm(0.5))
        hp.add_run("  ")
    run = hp.add_run("VOLTIS")
    run.font.name = FONT
    run.font.size = Pt(8.5)
    run.font.bold = True
    run.font.color.rgb = NAVY
    run = hp.add_run("  ·  Agentic AI for the Electricity Sector")
    run.font.size = Pt(7.8)
    run.font.color.rgb = MUTED
    hp.add_run("\t")
    run = hp.add_run(header_label)
    run.font.size = Pt(7.8)
    run.font.bold = True
    run.font.color.rgb = AMBER
    set_paragraph_border(hp, color=BORDER_HEX, size=5)

    footer = section.footer
    footer.is_linked_to_previous = False
    fp = footer.paragraphs[0]
    fp.paragraph_format.tab_stops.clear_all()
    fp.paragraph_format.tab_stops.add_tab_stop(Cm(17), WD_TAB_ALIGNMENT.RIGHT)
    run = fp.add_run(f"VOLTIS v1.0 · données synthétiques · {date}")
    run.font.size = Pt(7.2)
    run.font.color.rgb = MUTED
    fp.add_run("\t")
    run = fp.add_run("page ")
    run.font.size = Pt(7.2)
    run.font.color.rgb = MUTED
    add_page_number(fp)
    for r in fp.runs:
        r.font.name = FONT

    props = doc.core_properties
    props.title = title
    props.subject = subject
    props.author = author
    props.keywords = "Agentic AI, électricité, MCP, A2A, RAG, LangGraph, Docker, Streamlit"
    props.comments = "Documentation finale du mini-projet VOLTIS."
    props.category = "Mini-projet final"
    return doc


def cover(
    doc: Document,
    kicker: str,
    title: str,
    subtitle: str,
    meta_rows: Sequence[tuple[str, str]],
    highlights: Sequence[str],
) -> None:
    if (ASSETS / "logo_light.png").exists():
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.add_run().add_picture(str(ASSETS / "logo_light.png"), width=Cm(11.2))
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(24)
    run = p.add_run(kicker.upper())
    run.font.name = FONT
    run.font.size = Pt(8.8)
    run.font.bold = True
    run.font.color.rgb = AMBER
    set_character_spacing(run, 28)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 0.95
    run = p.add_run(title)
    run.font.name = FONT_DISPLAY
    run.font.size = Pt(30)
    run.font.bold = True
    run.font.color.rgb = NAVY

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(9)
    run = p.add_run(subtitle)
    run.font.name = FONT
    run.font.size = Pt(12.5)
    run.font.color.rgb = RGBColor(0x44, 0x56, 0x6E)

    p = doc.add_paragraph()
    set_paragraph_border(p, color=AMBER_HEX, size=16)
    p.paragraph_format.space_after = Pt(14)

    table = doc.add_table(rows=0, cols=2)
    table.autofit = False
    table.columns[0].width = Cm(4.2)
    table.columns[1].width = Cm(12.2)
    for key, value in meta_rows:
        row = table.add_row()
        c0, c1 = row.cells
        c0.width = Cm(4.2)
        c1.width = Cm(12.2)
        r0 = c0.paragraphs[0].add_run(key.upper())
        r0.font.size = Pt(7.2)
        r0.font.bold = True
        r0.font.color.rgb = MUTED
        r1 = c1.paragraphs[0].add_run(value)
        r1.font.size = Pt(9.6)
        r1.font.color.rgb = INK

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    box = doc.add_table(rows=1, cols=1)
    box.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = box.cell(0, 0)
    set_cell_shading(cell, NAVY_HEX)
    set_cell_margins(cell, top=140, start=170, bottom=130, end=170)
    p = cell.paragraphs[0]
    r = p.add_run("CE QUE COUVRE CE DOCUMENT")
    r.font.size = Pt(7.2)
    r.font.bold = True
    r.font.color.rgb = AMBER
    set_character_spacing(r, 22)
    for item in highlights:
        p = cell.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run("•  " + item)
        r.font.size = Pt(8.8)
        r.font.color.rgb = RGBColor(0xE8, 0xF0, 0xF9)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    r = p.add_run("Données 100 % synthétiques · aucun client réel · projet reproductible")
    r.font.size = Pt(7.2)
    r.font.color.rgb = MUTED
    doc.add_page_break()


def h1(doc: Document, text: str, page_break: bool = True):
    p = doc.add_paragraph(style="Heading 1")
    if page_break:
        p.paragraph_format.page_break_before = True
    p.add_run(text)
    return p


def h2(doc: Document, text: str):
    return doc.add_paragraph(text, style="Heading 2")


def h3(doc: Document, text: str):
    return doc.add_paragraph(text, style="Heading 3")


def para(doc: Document, text: str, bold_lead: str = "", size: float = 10.2, space_after: float = 5, italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    if bold_lead and text.startswith(bold_lead):
        r = p.add_run(bold_lead)
        r.bold = True
        r.font.color.rgb = NAVY
        r.font.size = Pt(size)
        text = text[len(bold_lead):]
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.italic = italic
    return p


def bullets(doc: Document, items: Iterable[str], style: str = "List Bullet"):
    for item in items:
        p = doc.add_paragraph(style=style)
        p.paragraph_format.space_after = Pt(2.5)
        if " : " in item and len(item.split(" : ")[0]) < 70:
            lead, rest = item.split(" : ", 1)
            r = p.add_run(lead + " : ")
            r.bold = True
            r.font.color.rgb = NAVY
            p.add_run(rest)
        else:
            p.add_run(item)


def table(
    doc: Document,
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    widths: Sequence[float] | None = None,
    font_size: float = 8.4,
    header_fill: str = NAVY_HEX,
    zebra: bool = True,
    caption: str = "",
):
    if caption:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(caption)
        r.font.size = Pt(7.8)
        r.font.italic = True
        r.font.color.rgb = MUTED
        p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    set_table_borders(t)
    if widths:
        for index, width in enumerate(widths):
            t.columns[index].width = Cm(width)
    header = t.rows[0]
    set_repeat_table_header(header)
    keep_row_together(header)
    for index, head in enumerate(headers):
        cell = header.cells[index]
        if widths:
            cell.width = Cm(widths[index])
        set_cell_shading(cell, header_fill)
        set_cell_margins(cell)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(str(head))
        r.font.size = Pt(font_size)
        r.font.bold = True
        r.font.color.rgb = WHITE
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    for row_index, row_data in enumerate(rows):
        row = t.add_row()
        keep_row_together(row)
        for index, value in enumerate(row_data):
            cell = row.cells[index]
            if widths:
                cell.width = Cm(widths[index])
            set_cell_margins(cell)
            if zebra and row_index % 2 == 1:
                set_cell_shading(cell, LIGHT_HEX)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            r = p.add_run(str(value))
            r.font.size = Pt(font_size)
            r.font.color.rgb = INK
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def figure(doc: Document, path: Path, caption: str, width_cm: float = 16.2):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(8)
    r = cap.add_run(caption)
    r.font.size = Pt(7.8)
    r.font.italic = True
    r.font.color.rgb = MUTED
    return p


def code_block(doc: Document, code: str, language: str = "python", font_size: float = 7.8):
    t = doc.add_table(rows=2, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    t.columns[0].width = Cm(16.2)
    keep_row_together(t.rows[0])
    keep_row_together(t.rows[1])
    top = t.cell(0, 0)
    set_cell_shading(top, "10263F")
    set_cell_margins(top, top=35, start=105, bottom=25, end=85)
    p = top.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(language.upper())
    r.font.name = FONT_MONO
    r.font.size = Pt(6.6)
    r.font.bold = True
    r.font.color.rgb = AMBER
    set_character_spacing(r, 18)
    body = t.cell(1, 0)
    set_cell_shading(body, "0A1F3C")
    set_cell_margins(body, top=75, start=105, bottom=95, end=105)
    p = body.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    lines = code.strip("\n").splitlines()
    for index, line in enumerate(lines):
        run = p.add_run(line if line else " ")
        run.font.name = FONT_MONO
        run.font.size = Pt(font_size)
        run.font.color.rgb = RGBColor(0xE7, 0xEF, 0xF8)
        if index < len(lines) - 1:
            run.add_break()
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def callout(doc: Document, title: str, text: str, kind: str = "info"):
    palette = {
        "info": ("EEF7FF", "1F5FA8", "EAF2FB"),
        "success": ("EAF8F4", "0C7B67", "D8F0E8"),
        "warning": ("FFF8E1", "8A6100", "F7E7B0"),
        "danger": ("FDECEA", "B23B2E", "F5CFC9"),
    }
    bg, fg, border = palette.get(kind, palette["info"])
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.cell(0, 0)
    set_cell_shading(cell, bg)
    set_cell_margins(cell, top=90, start=140, bottom=90, end=140)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(1)
    r = p.add_run(title)
    r.font.size = Pt(8.8)
    r.font.bold = True
    r.font.color.rgb = RGBColor.from_string(fg)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    r2 = p2.add_run(text)
    r2.font.size = Pt(8.7)
    r2.font.color.rgb = INK
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), "18")
    left.set(qn("w:color"), border)
    borders.append(left)
    tc_pr.append(borders)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def kpi_row(doc: Document, items: Sequence[tuple[str, str, str]]):
    """items = [(valeur, libellé, sous-texte), ...]"""
    t = doc.add_table(rows=1, cols=len(items))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for index, (value, label, sub) in enumerate(items):
        cell = t.cell(0, index)
        set_cell_shading(cell, "F8FAFD")
        set_cell_margins(cell, top=110, start=100, bottom=100, end=100)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(value)
        r.font.name = FONT_DISPLAY
        r.font.size = Pt(15)
        r.font.bold = True
        r.font.color.rgb = NAVY
        p2 = cell.add_paragraph()
        p2.paragraph_format.space_after = Pt(0)
        r2 = p2.add_run(label)
        r2.font.size = Pt(7.4)
        r2.font.bold = True
        r2.font.color.rgb = MUTED
        if sub:
            p3 = cell.add_paragraph()
            p3.paragraph_format.space_after = Pt(0)
            r3 = p3.add_run(sub)
            r3.font.size = Pt(6.6)
            r3.font.color.rgb = TEAL
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
