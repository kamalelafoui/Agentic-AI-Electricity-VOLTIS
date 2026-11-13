# -*- coding: utf-8 -*-
"""Crée l'archive finale en excluant secrets, caches et fichiers temporaires."""
from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Agentic_AI_Electricity_FINAL.zip"

ROOT_FILES = [
    "main.py",
    "README.md",
    "LIVRABLES.md",
    "MANIFEST.txt",
    "LICENSE",
    "requirements.txt",
    "requirements-dev.txt",
    "Dockerfile",
    "docker-compose.yml",
    "start_demo.ps1",
    "start_demo.sh",
    ".env.example",
    ".gitignore",
    ".dockerignore",
    ".streamlit/config.toml",
]
DIRS = [
    "assets", "a2a", "dashboard", "data", "docs", "json",
    "langgraph_workflow", "mcp_server", "presentation", "screenshots",
    "scripts", "shared", "tests", "videos",
]
EXCLUDED_DIRS = {"__pycache__", ".venv", "venv", ".git", "logs", "_preview", "_preview2", "_preview3"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log"}
EXCLUDED_FILES = {"mcp_calls.jsonl", "a2a_delegations.jsonl", "demo_report.json", "_test.pptx", "_resaved.pptx"}
EXCLUDED_PREFIXES = ("_export_", "_one_", "_embedded_", "_debug_")


def included(path: Path) -> bool:
    if set(path.parts) & EXCLUDED_DIRS:
        return False
    if path.name in EXCLUDED_FILES or path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    if path.name.startswith(EXCLUDED_PREFIXES):
        return False
    return True


def main() -> None:
    files: list[Path] = []
    for name in ROOT_FILES:
        path = ROOT / name
        if path.exists():
            files.append(path)
    for dirname in DIRS:
        base = ROOT / dirname
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and included(path):
                files.append(path)
    files = sorted(set(files), key=lambda p: str(p.relative_to(ROOT)).lower())
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
    size = OUT.stat().st_size / (1024 * 1024)
    print(f"Archive : {OUT.name} — {len(files)} fichiers — {size:.1f} Mo")
    print("Vérification : .env exclu =", all(path.name != ".env" for path in files))


if __name__ == "__main__":
    main()
