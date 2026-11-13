#!/usr/bin/env bash
# VOLTIS — lancement local guidé (macOS / Linux)
set -e
cd "$(dirname "$0")"
export PYTHONUTF8=1

echo ""
echo "  VOLTIS — Agentic AI for the Electricity Sector"
echo "  Dashboard 8033 · MCP 8100 · A2A 8101-8105"
echo ""

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "Python 3.12+ est requis." >&2
  exit 1
fi

if ! $PY -c "import streamlit, fastapi, langgraph" >/dev/null 2>&1; then
  echo "  Installation des dépendances…"
  $PY -m pip install -r requirements.txt
fi

echo "  Démarrage des services…"
exec $PY main.py
