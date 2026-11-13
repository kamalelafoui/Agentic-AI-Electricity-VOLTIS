# -*- coding: utf-8 -*-
"""Capture les écrans du dashboard VOLTIS avec Playwright (Chrome headless)."""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "screenshots"
OUT.mkdir(exist_ok=True)
BASE = "http://127.0.0.1:8033"

PAGES = [
    ("home", BASE, "VOLTIS — le hub agentique"),
    ("assistant", f"{BASE}/?page=assistant&demo=1", "Synthèse"),
    ("a2a", f"{BASE}/?page=a2a&demo=1", "Réponse consolidée du hub A2A"),
    ("stats", f"{BASE}/?page=stats", "Performance des régions"),
    ("mcp", f"{BASE}/?page=mcp", "MCP Playground"),
    ("architecture", f"{BASE}/?page=architecture", "Ports & services"),
    ("docs", f"{BASE}/?page=docs", "Livrables & documentation"),
]


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=r"C:\Users\HP\AppData\Local\ms-playwright\chromium-1248\chrome-win64\chrome.exe",
        )
        context = browser.new_context(viewport={"width": 1600, "height": 1050}, device_scale_factor=1)
        page = context.new_page()
        for name, url, marker in PAGES:
            print(f"  · capture {name} …")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_selector(f"text={marker}", timeout=60000)
                try:
                    page.wait_for_selector(".js-plotly-plot", timeout=15000)
                except Exception:
                    pass
                page.wait_for_timeout(4500)
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUT / f"{name}.png"), full_page=False)
                print("    ok")
            except Exception as error:
                print(f"    échec : {str(error)[:160]}")
        browser.close()
    print("Captures dans", OUT)


if __name__ == "__main__":
    main()
