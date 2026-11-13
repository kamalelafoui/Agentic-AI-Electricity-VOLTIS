# -*- coding: utf-8 -*-
"""Diagnostic : isole chaque slide pour trouver celle qui bloque PowerPoint."""
from __future__ import annotations

import sys
from pathlib import Path

from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "presentation" / "Presentation_Finale_VOLTIS.pptx"


def keep_only(prs, keep: int, out: Path) -> None:
    sld_ids = prs.slides._sldIdLst
    for index in reversed(range(len(sld_ids))):
        if index == keep:
            continue
        sld_id = sld_ids[index]
        prs.part.drop_rel(sld_id.rId)
        sld_ids.remove(sld_id)
    prs.save(out)


def main() -> None:
    import win32com.client

    app = win32com.client.DispatchEx("PowerPoint.Application")
    app.Visible = 1
    for index in range(26):
        prs = Presentation(SRC)
        out = ROOT / "presentation" / f"_one_{index + 1:02d}.pptx"
        keep_only(prs, index, out)
        try:
            presentation = app.Presentations.Open(str(out), ReadOnly=True, WithWindow=False)
            print(f"slide {index + 1:02d}: OK ({presentation.Slides.Count})")
            presentation.Close()
        except Exception as error:
            print(f"slide {index + 1:02d}: FAIL {str(error)[:120]}")
        out.unlink(missing_ok=True)
    app.Quit()


if __name__ == "__main__":
    main()
