# -*- coding: utf-8 -*-
"""Dashboard VOLTIS — Agentic AI for the Electricity Sector.

Lancement :
    streamlit run dashboard/app.py --server.port 8033
    python main.py            (dashboard + MCP + A2A)

Le dashboard fonctionne en mode connecté (MCP 8100 / A2A 8101) ou en mode
autonome : les mêmes fonctions métier sont appelées localement.
"""
from __future__ import annotations

import csv
import html
import io
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import mistune
import plotly.graph_objects as go
import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from a2a.agents import handle_agent  # noqa: E402
from a2a.server import _aggregate, _select_agents  # noqa: E402
from langgraph_workflow import graph_spec, run_workflow  # noqa: E402
from shared import electricity_core as core  # noqa: E402

ASSETS = ROOT / "assets"
DOCS = ROOT / "docs"
PRESENTATION = ROOT / "presentation"
JSON_DIR = ROOT / "json"
SCREENSHOTS = ROOT / "screenshots"
DATA = ROOT / "data"
VIDEOS = ROOT / "videos"

MCP_URL = os.getenv("VOLTIS_MCP_URL", "http://127.0.0.1:8100")
A2A_URL = os.getenv("VOLTIS_A2A_URL", "http://127.0.0.1:8101")

NAVY = "#0A1F3C"
NAVY2 = "#14365C"
AMBER = "#F5B301"
TEAL = "#16A6A1"
BLUE = "#3B82C4"
RED = "#D9534F"
GREEN = "#2E8B72"
MUTED = "#64748B"
BG = "#F4F7FB"
PALETTE = [NAVY, AMBER, TEAL, BLUE, "#7A5AA6", "#8A9BB0", RED]

MENU = [
    "Vue d'ensemble",
    "Assistant agentique",
    "MCP Playground",
    "Orchestration A2A",
    "Statistiques",
    "Architecture",
    "Documentation",
]

st.set_page_config(
    page_title="VOLTIS — Agentic AI for the Electricity Sector",
    page_icon=str(ASSETS / "favicon.png") if (ASSETS / "favicon.png").exists() else "⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------------------------------- #
# Style
# --------------------------------------------------------------------------- #
def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        :root {
            --navy:#0A1F3C; --navy2:#14365C; --amber:#F5B301; --teal:#16A6A1;
            --blue:#3B82C4; --bg:#F4F7FB; --ink:#12263F; --muted:#64748B;
        }
        html, body, [class*="css"] { font-family:'Inter','Segoe UI',sans-serif; }
        .stApp { background:radial-gradient(1200px 600px at 85% -10%, #E8F2FF 0%, var(--bg) 45%, #F8FAFD 100%); }
        [data-testid="stHeader"] { background:transparent; }
        #MainMenu {visibility:hidden;} footer {visibility:hidden;}
        .block-container { padding-top:1.2rem; padding-bottom:2.5rem; max-width:1460px; }

        [data-testid="stSidebar"] {
            background:linear-gradient(180deg,#07162A 0%,#0A1F3C 55%,#0E2B4D 100%);
            border-right:1px solid rgba(255,255,255,.06);
        }
        [data-testid="stSidebar"] * { color:#E9F1FA !important; }
        [data-testid="stSidebar"] .stRadio > div { gap:.25rem; }
        [data-testid="stSidebar"] [role="radiogroup"] label {
            border-radius:10px; padding:8px 10px; margin:2px 0; transition:.15s; cursor:pointer;
            border-left:3px solid transparent;
        }
        [data-testid="stSidebar"] [role="radiogroup"] label:hover { background:rgba(255,255,255,.07); }
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
            background:linear-gradient(90deg,rgba(245,179,1,.22),rgba(245,179,1,.04));
            border-left:3px solid var(--amber);
        }
        [data-testid="stSidebar"] [role="radiogroup"] label > div > div:first-child { display:none; }
        [data-testid="stSidebar"] [role="radiogroup"] p { margin:0; font-size:.84rem; font-weight:600; }
        [data-testid="stAppDeployButton"], [data-testid="stToolbar"] { display:none !important; }
        [data-testid="stSidebar"] [data-testid="stImage"] img { border-radius:12px; }
        [data-testid="stSidebar"] .status { color:#0C7B67 !important; background:#EAF8F4 !important; }
        [data-testid="stSidebar"] .status.off { color:#B23B2E !important; background:#FDECEA !important; }

        .hero {
            position:relative; overflow:hidden; border-radius:22px; padding:28px 34px;
            background:linear-gradient(115deg,#07162A 0%,#0A1F3C 52%,#17446F 100%);
            color:#fff; box-shadow:0 18px 40px rgba(10,31,60,.20); margin-bottom:18px;
            border:1px solid rgba(255,255,255,.08);
        }
        .hero:after {
            content:""; position:absolute; right:-90px; top:-110px; width:330px; height:330px;
            border-radius:50%; background:radial-gradient(circle,rgba(245,179,1,.34),rgba(245,179,1,0) 64%);
        }
        .hero:before {
            content:""; position:absolute; right:120px; bottom:-140px; width:270px; height:270px;
            border-radius:50%; border:44px solid rgba(22,166,161,.16);
        }
        .hero-kicker { font-size:.74rem; letter-spacing:.18em; font-weight:800; color:var(--amber); text-transform:uppercase; }
        .hero h1 { font-size:2.05rem; line-height:1.13; margin:.42rem 0 .5rem; font-weight:800; letter-spacing:-.02em; }
        .hero p { color:#C9D8E8; font-size:1.0rem; max-width:920px; margin:0; line-height:1.55; }
        .hero .chips { display:flex; gap:9px; flex-wrap:wrap; margin-top:16px; position:relative; z-index:2; }
        .chip { font-size:.74rem; font-weight:700; padding:6px 11px; border-radius:999px;
                background:rgba(255,255,255,.09); border:1px solid rgba(255,255,255,.14); color:#EAF2FB; }
        .chip.gold { background:rgba(245,179,1,.16); border-color:rgba(245,179,1,.38); color:#FFD666; }
        .chip.teal { background:rgba(22,166,161,.15); border-color:rgba(22,166,161,.38); color:#8FE3DF; }

        .grid { display:grid; gap:13px; }
        .metrics { grid-template-columns:repeat(6,minmax(0,1fr)); }
        @media(max-width:1250px){ .metrics{grid-template-columns:repeat(3,minmax(0,1fr));} }
        @media(max-width:760px){ .metrics{grid-template-columns:repeat(2,minmax(0,1fr));} }
        .metric {
            background:#fff; border:1px solid #E4ECF5; border-radius:16px; padding:14px 15px 13px;
            box-shadow:0 6px 18px rgba(18,38,63,.05); display:flex; gap:11px; align-items:flex-start;
        }
        .metric .ico { width:36px; height:36px; border-radius:10px; display:flex; align-items:center;
            justify-content:center; font-size:1.0rem; background:#EEF5FC; flex:none; }
        .metric .val { font-size:1.42rem; font-weight:800; color:var(--ink); line-height:1.05; letter-spacing:-.02em; }
        .metric .lab { font-size:.74rem; color:var(--muted); font-weight:600; margin-top:3px; }
        .metric .delta { font-size:.68rem; font-weight:700; color:var(--teal); margin-top:4px; }

        .card { background:#fff; border:1px solid #E4ECF5; border-radius:18px; padding:19px 21px;
                box-shadow:0 8px 22px rgba(18,38,63,.05); height:100%; }
        .card h3 { margin:0 0 .35rem; font-size:1.02rem; color:var(--ink); font-weight:800; }
        .card p { color:var(--muted); font-size:.88rem; line-height:1.55; margin:.2rem 0; }
        .card .tag { display:inline-block; margin-top:11px; font-size:.7rem; font-weight:800;
            color:var(--navy); background:#EEF5FC; border-radius:999px; padding:5px 10px; }
        .section-title { font-size:1.08rem; font-weight:800; color:var(--ink); margin:6px 0 9px; letter-spacing:-.01em; }
        .section-sub { color:var(--muted); font-size:.84rem; margin-top:-5px; margin-bottom:12px; }

        .data-warning { background:#FFF7E0; border:1px solid #EEDB9A; border-left:5px solid var(--amber);
            border-radius:12px; padding:11px 15px; margin:0 0 16px; color:#6B5200;
            font-size:.82rem; line-height:1.45; }

        .status { display:inline-flex; align-items:center; gap:7px; font-size:.72rem; font-weight:700;
            padding:6px 10px; border-radius:999px; background:#EAF8F4; color:#0C7B67; }
        .status.off { background:#FDECEA; color:#B23B2E; }
        .dot { width:7px; height:7px; border-radius:50%; background:currentColor; box-shadow:0 0 0 3px rgba(0,0,0,.05); }

        .agent-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }
        @media(max-width:1250px){ .agent-grid{grid-template-columns:repeat(2,minmax(0,1fr));} }
        .agent { background:#fff; border:1px solid #E4ECF5; border-radius:16px; padding:15px 16px;
                 box-shadow:0 6px 18px rgba(18,38,63,.05); position:relative; overflow:hidden; }
        .agent .top { display:flex; align-items:center; gap:9px; }
        .agent .avatar { width:34px; height:34px; border-radius:10px; display:flex; align-items:center; justify-content:center;
                         font-size:1rem; background:#EEF5FC; }
        .agent .name { font-weight:800; font-size:.84rem; color:var(--ink); }
        .agent .port { font-size:.66rem; color:var(--muted); font-weight:600; }
        .agent .desc { font-size:.74rem; color:var(--muted); line-height:1.45; margin:9px 0; min-height:32px; }
        .agent .skill { display:inline-block; font-size:.62rem; font-weight:700; padding:3px 7px; border-radius:6px;
                        background:#F1F5FA; color:#47607B; margin:2px 2px 0 0; }

        .tool-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:10px; }
        @media(max-width:1250px){ .tool-grid{grid-template-columns:repeat(3,minmax(0,1fr));} }
        .tool { background:#fff; border:1px solid #E4ECF5; border-radius:13px; padding:12px 13px; }
        .tool .tname { font-size:.73rem; font-weight:800; color:var(--ink); font-family:Consolas,monospace; }
        .tool .tdesc { font-size:.68rem; color:var(--muted); margin-top:5px; line-height:1.35; }
        .tool .tcat { font-size:.58rem; font-weight:800; color:var(--teal); text-transform:uppercase; letter-spacing:.06em; }

        .trace { border-left:3px solid #DCE8F4; margin-left:9px; padding-left:18px; }
        .trace-item { position:relative; padding:9px 0 9px 2px; }
        .trace-item:before { content:""; position:absolute; left:-25px; top:14px; width:11px; height:11px; border-radius:50%;
                             background:var(--teal); border:2px solid #fff; box-shadow:0 0 0 2px #DCE8F4; }
        .trace-item.failed:before { background:var(--red); }
        .trace-head { display:flex; gap:8px; align-items:center; flex-wrap:wrap; font-size:.78rem; }
        .trace-head b { color:var(--ink); }
        .trace-meta { font-size:.68rem; color:var(--muted); margin-top:3px; }
        .badge { font-size:.64rem; font-weight:800; padding:3px 7px; border-radius:6px; background:#EAF8F4; color:#0C7B67; }
        .badge.local { background:#FFF7E0; color:#8A6100; }
        .badge.failed { background:#FDECEA; color:#B23B2E; }

        .answer-body { background:linear-gradient(180deg,#FFFFFF,#F8FBFF); border:1px solid #DCE8F4;
                       border-radius:16px; padding:20px 24px; line-height:1.6; }
        .answer-body h2 { color:var(--navy); margin:16px 0 7px; font-size:1.02rem; }
        .answer-body h2:first-child { margin-top:0; }
        .answer-body h3 { color:var(--navy2); margin:12px 0 5px; font-size:.94rem; }
        .answer-body p { margin:.35rem 0; color:#33475F; font-size:.86rem; }
        .answer-body ul, .answer-body ol { margin:5px 0 10px 18px; padding:0; }
        .answer-body li { margin:3px 0; color:#33475F; font-size:.85rem; line-height:1.55; }
        .answer-body strong { color:var(--navy); }
        .answer-body code { background:#EEF5FC; color:#0B4A78; padding:1px 4px; border-radius:4px; font-size:.78rem; }
        .answer-body blockquote { border-left:4px solid var(--amber); background:#FFF9E8; margin:12px 0 0; padding:8px 12px;
                                  color:#5F4B00; font-size:.82rem; border-radius:0 8px 8px 0; }

        .source-card { background:#fff; border:1px solid #E4ECF5; border-left:4px solid var(--teal);
                       border-radius:11px; padding:11px 14px; margin-bottom:8px; }
        .source-card .ref { font-size:.68rem; font-weight:800; color:var(--teal); }
        .source-card .title { font-size:.82rem; font-weight:700; color:var(--ink); margin-top:2px; }
        .source-card .text { font-size:.72rem; color:var(--muted); margin-top:4px; line-height:1.45; }

        .doc-row { display:flex; align-items:center; justify-content:space-between; gap:12px;
                   border-bottom:1px solid #EDF2F8; padding:11px 2px; }
        .doc-row:last-child { border-bottom:none; }
        .doc-name { font-size:.84rem; font-weight:700; color:var(--ink); }
        .doc-meta { font-size:.7rem; color:var(--muted); }
        .pill { font-size:.66rem; font-weight:800; padding:4px 8px; border-radius:7px; background:#EEF5FC; color:#2D5A88; }

        .table-wrap { border:1px solid #E4ECF5; border-radius:12px; overflow:auto; background:#fff; }
        table.vtable { width:100%; border-collapse:collapse; font-size:.76rem; }
        table.vtable th { background:#0A1F3C; color:#fff; text-align:left; padding:8px 10px; font-weight:700; white-space:nowrap; }
        table.vtable td { padding:7px 10px; border-bottom:1px solid #EEF3F8; color:#33475F; }
        table.vtable tr:nth-child(even) td { background:#F8FAFD; }
        table.vtable tr:last-child td { border-bottom:none; }
        table.vtable td.num { text-align:right; font-variant-numeric:tabular-nums; }
        .table-note { font-size:.68rem; color:#8193A8; margin-top:5px; }

        .footer { margin-top:24px; padding-top:12px; border-top:1px solid #DDE7F1; color:#8193A8;
                  font-size:.72rem; display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; }

        .stButton > button, .stFormSubmitButton > button {
            border-radius:10px; border:1px solid #D8E4F0; font-weight:700; font-size:.84rem;
            transition:.18s; background:#fff; color:var(--navy);
        }
        .stButton > button:hover, .stFormSubmitButton > button:hover { border-color:var(--amber); color:var(--navy); }
        .stFormSubmitButton > button {
            background:linear-gradient(135deg,#F5B301,#FFD45C); border:none; color:#17263A;
            box-shadow:0 6px 16px rgba(245,179,1,.30);
        }
        [data-testid="stForm"] { background:#fff; border:1px solid #E4ECF5; border-radius:16px; padding:16px 18px;
                                 box-shadow:0 6px 18px rgba(18,38,63,.04); }
        [data-testid="stExpander"] { border:1px solid #E4ECF5; border-radius:12px; background:#fff; }
        .stTabs [data-baseweb="tab-list"] { gap:4px; }
        .stTabs [data-baseweb="tab"] { border-radius:8px 8px 0 0; font-weight:700; font-size:.8rem; }
        .stTabs [aria-selected="true"] { background:#F5B301 !important; color:#17263A !important; }
        div[data-testid="stDataFrame"] { border:1px solid #E4ECF5; border-radius:12px; overflow:hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
@st.cache_data(ttl=4, show_spinner=False)
def mcp_health() -> dict:
    try:
        response = requests.get(f"{MCP_URL}/api/health", timeout=0.8)
        response.raise_for_status()
        return {"online": True, **response.json()}
    except Exception:
        return {"online": False, "tools": [tool["name"] for tool in core.list_tools()], "tool_count": len(core.list_tools())}


@st.cache_data(ttl=4, show_spinner=False)
def a2a_health() -> dict:
    try:
        response = requests.get(f"{A2A_URL}/health", timeout=1.2)
        response.raise_for_status()
        return {"online": True, **response.json()}
    except Exception:
        return {"online": False, "agents_total": 4, "agents_online": 0}


@st.cache_data(ttl=30, show_spinner=False)
def cached_kpis() -> dict:
    return core.national_kpis()


def esc(value: object) -> str:
    return html.escape(str(value))


def compact(value: str) -> str:
    return "".join(line.strip() for line in value.splitlines())


def md_html(value: str) -> str:
    return mistune.html(value)


def set_nav(page: str) -> None:
    st.session_state.nav = page


def hero(kicker: str, title: str, subtitle: str, chips: list[tuple[str, str]] | None = None) -> None:
    chips_html = ""
    if chips:
        chips_html = "<div class='chips'>" + "".join(
            f"<span class='chip {css}'>{esc(label)}</span>" for label, css in chips
        ) + "</div>"
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-kicker">{esc(kicker)}</div>
            <h1>{esc(title)}</h1>
            <p>{esc(subtitle)}</p>
            {chips_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric(label: str, value: str, icon: str, delta: str = "", color: str = "#EEF5FC") -> str:
    delta_html = f"<div class='delta'>{esc(delta)}</div>" if delta else ""
    return (
        f"<div class='metric'><div class='ico' style='background:{color}'>{icon}</div>"
        f"<div><div class='val'>{esc(value)}</div><div class='lab'>{esc(label)}</div>{delta_html}</div></div>"
    )


def metrics_row(items: list[tuple[str, str, str, str, str]]) -> None:
    st.markdown("<div class='grid metrics'>" + "".join(metric(*item) for item in items) + "</div>", unsafe_allow_html=True)


def status_pill(online: bool, label: str) -> str:
    cls = "status" if online else "status off"
    suffix = "en ligne" if online else "hors ligne · repli local"
    return f"<span class='{cls}'><span class='dot'></span>{esc(label)} — {suffix}</span>"


def plot_layout(fig: go.Figure, height: int = 320) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=44, b=52),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color=NAVY, size=11),
        title_font=dict(size=13, color=NAVY),
        legend=dict(orientation="h", yanchor="top", y=-0.16, x=0, font=dict(size=9)),
        hoverlabel=dict(bgcolor="white", font_size=11, font_family="Inter"),
    )
    fig.update_xaxes(showgrid=False, linecolor="#E4ECF5")
    fig.update_yaxes(gridcolor="#EDF2F8", zeroline=False, linecolor="#E4ECF5")
    if any(getattr(trace, "type", "") == "pie" for trace in fig.data):
        fig.update_layout(
            legend=dict(orientation="h", yanchor="top", y=-0.02, x=0.5, xanchor="center", font=dict(size=9)),
            margin=dict(l=8, r=8, t=48, b=52),
        )
    return fig


def card(title: str, body: str, tag: str = "") -> str:
    tag_html = f"<div class='tag'>{esc(tag)}</div>" if tag else ""
    return f"<div class='card'><h3>{esc(title)}</h3><p>{body}</p>{tag_html}</div>"


def file_size(path: Path) -> str:
    if not path.exists():
        return "à générer"
    size = path.stat().st_size
    if size > 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} Mo"
    return f"{size / 1024:.0f} Ko"


def call_mcp(tool: str, arguments: dict) -> tuple[dict, float, str]:
    started = time.perf_counter()
    if mcp_health().get("online"):
        try:
            response = requests.post(f"{MCP_URL}/api/tool", json={"tool": tool, "arguments": arguments}, timeout=8)
            response.raise_for_status()
            body = response.json()
            return body["result"], body.get("latency_ms", round((time.perf_counter() - started) * 1000, 1)), "MCP · HTTP"
        except Exception:
            pass
    result = core.call_tool(tool, arguments)
    return result, round((time.perf_counter() - started) * 1000, 1), "Local · repli"


def trace_html(trace: list[dict]) -> str:
    if not trace:
        return "<p style='color:#64748B'>Aucun appel.</p>"
    items = []
    for item in trace:
        failed = item.get("status") in ("error", "failed")
        items.append(
            f"""
            <div class="trace-item {'failed' if failed else ''}">
                <div class="trace-head"><b>{esc(item.get('step', item.get('tool', '')))}</b>
                    <span class="badge {'failed' if failed else ''}">{esc(item.get('status', 'ok'))}</span>
                    <span class="badge">{esc(item.get('latency_ms', 0))} ms</span>
                </div>
                <div class="trace-meta">{esc(item.get('timestamp', ''))} — {esc(item.get('detail', item.get('summary', '')))}</div>
            </div>
            """
        )
    return "<div class='trace'>" + compact("".join(items)) + "</div>"


def source_cards(sources: list[dict]) -> None:
    for index, source in enumerate(sources, 1):
        st.markdown(
            f"""
            <div class="source-card">
                <div class="ref">[{index}] {esc(source['citation'])}</div>
                <div class="title">{esc(source['title'])}</div>
                <div class="text">{esc(source['text'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def html_table(rows: list[dict], columns: list[str] | None = None, max_rows: int = 24) -> None:
    if not rows:
        st.caption("Aucune donnée.")
        return
    columns = columns or list(rows[0].keys())
    head = "".join(f"<th>{esc(column)}</th>" for column in columns)
    body = []
    for row in rows[:max_rows]:
        cells = []
        for column in columns:
            value = row.get(column, "")
            if isinstance(value, float):
                value = f"{value:,.2f}".replace(",", " ").replace(".", ",")
            elif isinstance(value, int):
                value = f"{value:,}".replace(",", " ")
            cells.append(f"<td>{esc(value)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    st.markdown(
        "<div class='table-wrap'><table class='vtable'>"
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table></div>",
        unsafe_allow_html=True,
    )
    if len(rows) > max_rows:
        st.markdown(f"<div class='table-note'>{len(rows)} lignes · affichage des {max_rows} premières.</div>", unsafe_allow_html=True)


def to_csv(rows: list[dict], columns: list[str] | None = None) -> bytes:
    if not rows:
        return b""
    columns = columns or list(rows[0].keys())
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, delimiter=";")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: row.get(column, "") for column in columns})
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def agent_cards_html(cards: list[dict], online: bool) -> None:
    icons = {"grid-analyst": "▦", "outage-inspector": "⚠", "billing-advisor": "◫", "forecast-agent": "◔"}
    blocks = []
    for item in cards:
        card_data = item.get("card", {})
        agent_id = item.get("agent_id", card_data.get("metadata", {}).get("agent_id", ""))
        keywords = card_data.get("metadata", {}).get("keywords", [])
        if keywords:
            skills = "".join(f"<span class='skill'>{esc(keyword)}</span>" for keyword in keywords[:5])
        else:
            skills = "".join(f"<span class='skill'>{esc(skill['name'])}</span>" for skill in card_data.get("skills", [])[:3])
        port = card_data.get("metadata", {}).get("port", "—")
        status = item.get("status", "carte locale")
        blocks.append(
            f"""
            <div class="agent">
                <div class="top"><div class="avatar">{icons.get(agent_id, '◈')}</div>
                    <div><div class="name">{esc(card_data.get('name', agent_id))}</div>
                    <div class="port">port {esc(port)} · {esc(status)}</div></div>
                </div>
                <div class="desc">{esc(card_data.get('description', ''))[:150]}</div>
                <div>{skills}</div>
            </div>
            """
        )
    st.markdown("<div class='agent-grid'>" + compact("".join(blocks)) + "</div>", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #
def page_home() -> None:
    hero(
        "Agentic AI for the Electricity Sector · 2026",
        "VOLTIS — le hub agentique du réseau électrique",
        "Un assistant qui comprend la question, interroge les données du réseau, cite ses sources, "
        "critique sa propre réponse et fait collaborer quatre agents spécialisés. Une seule plateforme "
        "pour l'exploitation, la maintenance et la relation client.",
        [("MCP · 10 outils", "gold"), ("A2A · 4 agents", "teal"), ("RAG hybride", ""), ("LangGraph Reflexion", "")],
    )
    st.markdown(
        "<div class='data-warning'><b>⚠️ Données 100 % synthétiques.</b> "
        "Aucune API réelle ONEE / ANRE / SCADA / AMI n'est appelée et aucun client réel n'est utilisé. "
        "Les valeurs sont calibrées sur des ordres de grandeur publics, uniquement pour la démonstration.</div>",
        unsafe_allow_html=True,
    )
    kpis = cached_kpis()
    metrics_row(
        [
            ("Consommation annuelle", f"{kpis['consumption_gwh']/1000:.1f} TWh".replace(".", ","), "⚡", "8 régions", "#EEF5FC"),
            ("Clients desservis", f"{kpis['clients']/1_000_000:.2f} M".replace(".", ","), "◉", "2,14 M à Casablanca", "#FFF7E0"),
            ("Pointe nationale (MW)", f"{kpis['peak_mw']:,.0f}".replace(",", " "), "▲", "marge 8 %", "#EAF8F4"),
            ("Part renouvelable", f"{kpis['renewable_share_pct']:.1f} %".replace(".", ","), "☀", "37,9 % du mix", "#FFF7E0"),
            ("SAIDI national", f"{kpis['saidi_min']:.0f} min", "⏱", f"SAIFI {kpis['saifi']:.2f}".replace(".", ","), "#EEF5FC"),
            ("Incidents actifs", str(kpis["active_outages"]), "⚠", f"{kpis['outages_90d']} sur 90 jours", "#FDECEA"),
        ]
    )
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.55, 1], gap="large")
    with col1:
        rows = core.load_curve()
        national: dict[str, float] = {}
        for row in rows:
            national[row["timestamp"]] = national.get(row["timestamp"], 0) + row["load_mw"]
        points = sorted(national.items())
        last = datetime.fromisoformat(points[-1][0])
        cutoff = last - timedelta(days=6)
        filtered = [(datetime.fromisoformat(key), value) for key, value in points if datetime.fromisoformat(key) >= cutoff]
        fig = go.Figure(
            go.Scatter(
                x=[point[0] for point in filtered],
                y=[point[1] for point in filtered],
                mode="lines",
                fill="tozeroy",
                line=dict(color=NAVY, width=2.2),
                fillcolor="rgba(10,31,60,0.10)",
                hovertemplate="%{x|%d/%m %H:%M}<br>%{y:,.0f} MW<extra></extra>",
            )
        )
        fig.update_layout(title="Courbe de charge nationale — 7 derniers jours")
        fig.update_yaxes(title="MW")
        fig.update_xaxes(title="")
        st.plotly_chart(plot_layout(fig, 345), use_container_width=True, config={"displayModeBar": False})
    with col2:
        mix = core.production_mix()
        fig = go.Figure(
            go.Pie(
                labels=[source["source"] for source in mix["sources"]],
                values=[source["share_pct"] for source in mix["sources"]],
                hole=0.62,
                marker=dict(colors=[source["color"] for source in mix["sources"]]),
                textinfo="percent",
                textfont_size=9,
            )
        )
        fig.add_annotation(text=f"<b>{mix['renewable_share_pct']} %</b><br>renouvelable", showarrow=False, font_size=12, font_color=NAVY)
        fig.update_layout(title="Mix de production 2026", showlegend=True)
        st.plotly_chart(plot_layout(fig, 345), use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div class='section-title'>Deux modules, une même plateforme</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        st.markdown(
            card(
                "Assistant agentique",
                "Une question en français, un plan de recherche, des outils MCP, des sources citées "
                "et une boucle Reflexion qui améliore la réponse avant publication.",
                "LangGraph · RAG · Reflexion",
            ),
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Ouvrir l'assistant →", use_container_width=True, key="go_assistant", on_click=set_nav, args=(MENU[1],)):
            st.rerun()
    with col2:
        st.markdown(
            card(
                "MCP Playground",
                "10 outils standards exposés en JSON-RPC : KPI, régions, incidents, prévision, "
                "facturation, recherche documentaire et économies d'énergie.",
                "MCP 2025-06-18 · port 8100",
            ),
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Tester les outils →", use_container_width=True, key="go_mcp", on_click=set_nav, args=(MENU[2],)):
            st.rerun()
    with col3:
        st.markdown(
            card(
                "Collaboration A2A",
                "Un orchestrateur découvre les AgentCards, sélectionne au moins deux spécialistes, "
                "délègue en parallèle et agrège les artifacts avec un correlation_id.",
                "A2A 0.3 · ports 8101-8105",
            ),
            unsafe_allow_html=True,
        )
        st.write("")
        if st.button("Lancer une orchestration →", use_container_width=True, key="go_a2a", on_click=set_nav, args=(MENU[3],)):
            st.rerun()

    st.markdown("<div class='section-title' style='margin-top:20px'>Régions & incidents récents</div>", unsafe_allow_html=True)
    col1, col2 = st.columns([1.15, 1], gap="large")
    with col1:
        table = core.region_table()
        fig = go.Figure(
            go.Bar(
                x=[row["consumption_gwh"] for row in table],
                y=[row["name"] for row in table],
                orientation="h",
                marker=dict(
                    color=[row["renewable_share_pct"] for row in table],
                    colorscale=[[0, "#DCE8F4"], [1, TEAL]],
                    showscale=False,
                ),
                hovertemplate="%{y}<br>%{x:,.0f} GWh<extra></extra>",
            )
        )
        fig.update_layout(title="Consommation par région (GWh/an)")
        fig.update_yaxes(categoryorder="total ascending")
        st.plotly_chart(plot_layout(fig, 330), use_container_width=True, config={"displayModeBar": False})
    with col2:
        incidents = [row for row in core.outages()[:7]]
        rows = [
            {
                "ID": row["incident_id"],
                "Date": row["started_at"],
                "Région": row["region"],
                "Départ": row["feeder"],
                "Cause": row["cause"],
                "Priorité": row["priority"],
                "Statut": row["status"],
            }
            for row in incidents
        ]
        st.markdown("<div class='section-sub'>Derniers incidents du registre</div>", unsafe_allow_html=True)
        html_table(rows)

    st.markdown(
        f"<div class='footer'><span>VOLTIS v1.0 · données 100 % synthétiques · aucune API réelle · 12 novembre 2026</span>"
        f"<span>Dashboard : <b>localhost:8033</b> · MCP : 8100 · A2A : 8101</span></div>",
        unsafe_allow_html=True,
    )


def page_assistant() -> None:
    hero(
        "LangGraph · Agentic RAG · Reflexion",
        "Assistant agentique : posez une question métier, l'agent planifie et se corrige",
        "Le graphe choisit les outils, récupère les documents, rédige une réponse chiffrée, la critique "
        "puis la raffine. Chaque affirmation est reliée à une source et chaque score est affiché.",
        [("10 outils MCP", "gold"), ("RAG hybride", "teal"), ("2 itérations max", ""), ("Sources citées", "")],
    )
    with st.form("assistant_form"):
        st.markdown("<div class='section-title' style='font-size:.95rem;margin-top:0'>Contexte de la requête</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([2.3, 1, 1])
        with c1:
            question = st.text_area(
                "Question",
                value="Analyse la coupure du quartier Maârif hier soir et propose un plan d'action priorisé.",
                height=92,
            )
        with c2:
            region_options = ["NATIONAL"] + [region["code"] for region in core.regions()]
            region = st.selectbox(
                "Région", region_options,
                format_func=lambda code: "National" if code == "NATIONAL" else core.region_name(code),
                index=1,
            )
            audience = st.selectbox("Profil", ["Exploitation", "Direction", "Client", "Maintenance"])
        with c3:
            top_k = st.slider("Sources (top-k)", 2, 6, 4)
            threshold = st.slider("Seuil qualité", 7.0, 9.5, 8.2, 0.1)
            max_iter = st.slider("Itérations max", 1, 3, 2)
        submitted = st.form_submit_button("Lancer le workflow agentique", use_container_width=True)

    if submitted:
        with st.spinner("Planification, retrieval, outils, critique et raffinement…"):
            result = run_workflow(question, region, audience, top_k, threshold, max_iter)
        st.session_state.assistant_result = result
        st.session_state.assistant_question = question

    result = st.session_state.get("assistant_result")
    if not result and st.query_params.get("demo") == "1":
        demo_question = "Analyse la coupure du quartier Maârif hier soir et propose un plan d'action priorisé."
        result = run_workflow(demo_question, "CAS", "Exploitation", 4, 8.2, 2)
        st.session_state.assistant_result = result
        st.session_state.assistant_question = demo_question
    if not result:
        st.info("Posez une question ou utilisez l'exemple pré-rempli pour voir la trace complète du graphe.")
        return

    history = result.get("score_history", [])
    initial = history[0] if history else {}
    final = history[-1] if history else {}
    gain = round(final.get("overall", 0) - initial.get("overall", 0), 1)
    metrics_row(
        [
            ("Intention détectée", result.get("intent_label", "—"), "◈", f"région {result.get('region_code')}", "#EEF5FC"),
            ("Score initial", f"{initial.get('overall', 0)}/10", "◇", "brouillon", "#FDECEA"),
            ("Score final", f"{final.get('overall', 0)}/10", "◆", f"+{gain} pts", "#EAF8F4"),
            ("Itérations", str(result.get("iterations", 0)), "↻", "boucle Reflexion", "#FFF7E0"),
            ("Outils appelés", str(len(result.get("tool_trace", []))), "⚙", "MCP", "#EEF5FC"),
            ("Latence", f"{result.get('elapsed_ms', 0):.0f} ms", "⏱", result.get("confidence", ""), "#FFF7E0"),
        ]
    )
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    tab_answer, tab_quality, tab_sources, tab_json = st.tabs(["Réponse", "Qualité & trace", "Sources", "JSON"])
    with tab_answer:
        st.markdown(
            f"<div class='answer-body'>{md_html(result.get('final_answer', ''))}</div>",
            unsafe_allow_html=True,
        )
        tools = ", ".join(row["tool"] for row in result.get("tool_trace", []))
        st.caption(f"Question : {st.session_state.get('assistant_question', '')} · Outils : {tools}")
        st.download_button(
            "Télécharger la réponse (JSON)",
            data=json.dumps(result, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
            file_name="volt_is_reponse.json",
            mime="application/json",
        )
    with tab_quality:
        col1, col2 = st.columns([1, 1.35], gap="large")
        with col1:
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=final.get("overall", 0),
                    number={"suffix": " /10", "font": {"size": 30, "color": NAVY}},
                    gauge={
                        "axis": {"range": [0, 10], "tickwidth": 1},
                        "bar": {"color": TEAL, "thickness": 0.28},
                        "bgcolor": "white",
                        "steps": [
                            {"range": [0, 6], "color": "#FDECEA"},
                            {"range": [6, 8.2], "color": "#FFF7E0"},
                            {"range": [8.2, 10], "color": "#EAF8F4"},
                        ],
                        "threshold": {"line": {"color": AMBER, "width": 3}, "thickness": 0.8, "value": threshold},
                    },
                    title={"text": "Score Reflexion", "font": {"size": 13}},
                )
            )
            st.plotly_chart(plot_layout(fig, 270), use_container_width=True, config={"displayModeBar": False})
        with col2:
            labels = [item["label"] for item in history]
            criteria = ["clarity", "accuracy", "concision", "coherence"]
            colors = [BLUE, TEAL, AMBER, NAVY2]
            fig = go.Figure()
            for criterion, color in zip(criteria, colors):
                fig.add_trace(
                    go.Bar(
                        name=criterion.capitalize(),
                        x=labels,
                        y=[item["scores"][criterion] for item in history],
                        marker_color=color,
                    )
                )
            fig.update_layout(barmode="group", title="Évolution des quatre critères")
            fig.update_yaxes(range=[0, 10])
            st.plotly_chart(plot_layout(fig, 270), use_container_width=True, config={"displayModeBar": False})

        st.markdown("<div class='section-title'>Trace du graphe</div>", unsafe_allow_html=True)
        st.markdown(trace_html(result.get("trace", [])), unsafe_allow_html=True)
        with st.expander("Détail des appels d'outils", expanded=True):
            rows = [
                {
                    "Outil": row["tool"],
                    "Arguments": json.dumps(row["arguments"], ensure_ascii=False),
                    "Statut": row["status"],
                    "Latence (ms)": row["latency_ms"],
                    "Résumé": row.get("summary", ""),
                }
                for row in result.get("tool_trace", [])
            ]
            html_table(rows)
        with st.expander("Critique initiale et points d'amélioration"):
            st.markdown(
                "\n".join(f"- {issue}" for issue in initial.get("issues", [])) or "Aucun point bloquant."
            )
            st.caption(initial.get("rationale", ""))
    with tab_sources:
        st.markdown("<div class='section-sub'>Extraits utilisés par le Retriever, classés par pertinence.</div>", unsafe_allow_html=True)
        source_cards(result.get("sources", []))
    with tab_json:
        st.json(result, expanded=False)

    st.markdown(
        f"<div class='footer'><span>Graphe LangGraph · {len(graph_spec()['nodes'])} nœuds · seuil {threshold}/10</span>"
        f"<span>Correlation de session : {esc(st.session_state.get('assistant_question', '')[:24])}…</span></div>",
        unsafe_allow_html=True,
    )


def page_mcp() -> None:
    hero(
        "Model Context Protocol · serveur 8100",
        "MCP Playground : dix outils standards pour le réseau électrique",
        "Le serveur publie ses outils avec leur schéma JSON. Le dashboard les appelle en HTTP, "
        "affiche la latence et le résultat brut — comme le ferait un agent LangGraph.",
        [("JSON-RPC 2.0", "gold"), ("10 outils", "teal"), ("SSE / streamable HTTP", ""), ("Traçabilité JSONL", "")],
    )
    health = mcp_health()
    online = health.get("online", False)
    c1, c2, c3 = st.columns([1.5, 1, 1])
    with c1:
        st.markdown(status_pill(online, "Serveur MCP 127.0.0.1:8100"), unsafe_allow_html=True)
    with c2:
        st.markdown(f"<span class='pill'>{health.get('tool_count', len(core.list_tools()))} outils exposés</span>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<span class='pill'>{health.get('calls', 0)} appels journalisés</span>", unsafe_allow_html=True)
    st.write("")

    tools = core.list_tools()
    cards = "".join(
        f"""<div class="tool"><div class="tcat">{esc(tool['category'])}</div>
        <div class="tname">{esc(tool['name'])}</div>
        <div class="tdesc">{esc(tool['description'])}</div></div>"""
        for tool in tools
    )
    st.markdown("<div class='tool-grid'>" + compact(cards) + "</div>", unsafe_allow_html=True)
    st.write("")

    with st.form("mcp_form"):
        st.markdown("<div class='section-title' style='font-size:.95rem;margin-top:0'>Appeler un outil</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1.5, 1, 1])
        with c1:
            tool_name = st.selectbox("Outil", [tool["name"] for tool in tools], index=9)
        with c2:
            region = st.selectbox(
                "Région", ["NATIONAL"] + [region["code"] for region in core.regions()],
                format_func=lambda code: "National" if code == "NATIONAL" else core.region_name(code),
            )
        with c3:
            top_k = st.slider("Top-k (RAG)", 1, 8, 4)
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            query = st.text_input("Requête / question", value="procédure de délestage en cas de pointe")
        with c2:
            segment = st.selectbox("Segment tarifaire", list(core.tariffs().keys()), index=0)
        with c3:
            consumption = st.number_input("Consommation (MWh)", min_value=0.01, value=0.35, step=0.05)
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            status = st.selectbox("Statut incident", ["Tous", "Résolu", "En cours", "Planifié"])
        with c2:
            priority = st.selectbox("Priorité", ["Toutes", "P1", "P2", "P3"])
        with c3:
            customer_id = st.selectbox("Client suivi", [customer["customer_id"] for customer in core.customers()])
        submitted = st.form_submit_button("Exécuter l'outil", use_container_width=True)

    if submitted:
        arguments_map = {
            "get_grid_kpis": {},
            "get_region_profile": {"region_code": region if region != "NATIONAL" else "CAS"},
            "get_consumption": {"region_code": region, "months": 12},
            "get_production_mix": {},
            "query_outages": {"region_code": region, "status": status, "priority": priority, "limit": 10},
            "forecast_load": {"region_code": region, "horizon_h": 24, "temperature_delta": 5},
            "simulate_bill": {"segment": segment, "consumption_mwh": consumption, "region_code": region if region != "NATIONAL" else "CAS"},
            "search_knowledge": {"query": query, "top_k": top_k},
            "recommend_energy_savings": {"customer_id": customer_id},
            "get_service_quality": {"region_code": region},
        }
        result, latency, source = call_mcp(tool_name, arguments_map[tool_name])
        st.session_state.mcp_result = {
            "tool": tool_name,
            "arguments": arguments_map[tool_name],
            "result": result,
            "latency_ms": latency,
            "source": source,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }

    payload = st.session_state.get("mcp_result")
    if payload:
        st.markdown(
            f"<div style='display:flex;gap:8px;align-items:center;margin:8px 0 10px'>"
            f"<span class='badge'>{esc(payload['source'])}</span>"
            f"<span class='badge'>{payload['latency_ms']} ms</span>"
            f"<span class='badge'>{esc(payload['tool'])}</span></div>",
            unsafe_allow_html=True,
        )
        st.json(payload)
    else:
        st.info("Sélectionnez un outil et lancez l'appel pour voir le résultat JSON brut.")

    if online:
        try:
            calls = requests.get(f"{MCP_URL}/api/calls?limit=8", timeout=2).json().get("calls", [])
        except Exception:
            calls = []
        if calls:
            st.markdown("<div class='section-title' style='margin-top:18px'>Derniers appels serveur</div>", unsafe_allow_html=True)
            html_table(calls)

    with st.expander("Exemple JSON-RPC 2.0 (MCP)"):
        st.code(
            json.dumps(
                {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "forecast_load", "arguments": {"region_code": "CAS", "temperature_delta": 5}}},
                ensure_ascii=False,
                indent=2,
            ),
            language="json",
        )
        st.caption("POST http://127.0.0.1:8100/mcp · initialize · tools/list · tools/call · resources/read")
    st.markdown(
        "<div class='footer'><span>MCP 2025-06-18 · FastAPI · JSON-RPC 2.0 · SSE</span>"
        "<span>Les appels sont journalisés dans data/mcp_calls.jsonl</span></div>",
        unsafe_allow_html=True,
    )


def page_a2a() -> None:
    hero(
        "Agent-to-Agent · orchestrateur 8101",
        "Quatre agents, un hub : découvrir, déléguer, agréger",
        "L'orchestrateur interroge les AgentCards, sélectionne au moins deux spécialistes, envoie les tâches "
        "en parallèle avec un correlation_id unique et consolide les artifacts en une réponse traçable.",
        [("4 agents", "gold"), ("AgentCard discovery", "teal"), ("correlation_id", ""), ("Délégation parallèle", "")],
    )
    health = a2a_health()
    online = health.get("online", False)
    c1, c2, c3 = st.columns([1.5, 1, 1])
    with c1:
        st.markdown(status_pill(online, "Orchestrateur A2A 127.0.0.1:8101"), unsafe_allow_html=True)
    with c2:
        st.markdown(f"<span class='pill'>{health.get('agents_online', 0)}/{health.get('agents_total', 4)} agents en ligne</span>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<span class='pill'>{health.get('delegations', 0)} délégations</span>", unsafe_allow_html=True)
    st.write("")

    cards = []
    for agent_id in core.AGENT_CAPABILITIES:
        path = ROOT / "a2a" / "agent_cards" / f"{agent_id}.json"
        cards.append(
            {
                "agent_id": agent_id,
                "status": "en ligne" if online else "carte locale",
                "card": json.loads(path.read_text(encoding="utf-8")) if path.exists() else {},
            }
        )
    agent_cards_html(cards, online)
    st.write("")

    with st.form("a2a_form"):
        st.markdown("<div class='section-title' style='font-size:.95rem;margin-top:0'>Tâche à déléguer</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([2.6, 1, 1])
        with c1:
            question = st.text_area(
                "Question / objectif",
                value="Analyse la coupure de Maârif hier soir, évalue le risque de pointe demain et propose un plan d'action.",
                height=88,
            )
        with c2:
            region = st.selectbox(
                "Région", ["NATIONAL"] + [region["code"] for region in core.regions()],
                format_func=lambda code: "National" if code == "NATIONAL" else core.region_name(code),
                index=1,
            )
            max_agents = st.slider("Agents max", 2, 4, 3)
        with c3:
            st.markdown("<div style='font-size:.78rem;color:#64748B;line-height:1.5;margin-top:8px'>"
                        "Sélection automatique par capacités et mots-clés. Au moins deux agents sont mobilisés."
                        "</div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Lancer l'orchestration A2A", use_container_width=True)

    if submitted:
        if online:
            try:
                response = requests.post(
                    f"{A2A_URL}/orchestrate",
                    json={"question": question, "region_code": region, "max_agents": max_agents},
                    timeout=30,
                )
                response.raise_for_status()
                result = response.json()
            except Exception as error:
                result = _local_orchestration(question, region, max_agents, str(error))
        else:
            result = _local_orchestration(question, region, max_agents, "orchestrateur hors ligne")
        st.session_state.a2a_result = result

    result = st.session_state.get("a2a_result")
    if not result and st.query_params.get("demo") == "1":
        demo_question = "Analyse la coupure de Maârif hier soir, évalue le risque de pointe demain et propose un plan d'action."
        if online:
            try:
                response = requests.post(
                    f"{A2A_URL}/orchestrate",
                    json={"question": demo_question, "region_code": "CAS", "max_agents": 3},
                    timeout=30,
                )
                response.raise_for_status()
                result = response.json()
            except Exception as error:
                result = _local_orchestration(demo_question, "CAS", 3, str(error))
        else:
            result = _local_orchestration(demo_question, "CAS", 3, "orchestrateur hors ligne")
        st.session_state.a2a_result = result
    if not result:
        st.info("Lancez une orchestration pour voir les AgentCards mobilisées, la timeline et les artifacts.")
        return

    correlation = result.get("correlation_id", "—")
    correlation_short = correlation if len(correlation) <= 9 else "…" + correlation[-6:]
    metrics_row(
        [
            ("Correlation ID", correlation_short, "⌘", correlation, "#EEF5FC"),
            ("Agents mobilisés", str(len(result.get("artifacts", []))), "◉", "collaboration", "#EAF8F4"),
            ("Latence hub", f"{result.get('latency_ms', 0):.0f} ms", "⏱", "parallèle", "#FFF7E0"),
            ("Sources", str(sum(len(item.get("sources", [])) for item in result.get("artifacts", []))), "▤", "documents", "#EEF5FC"),
        ]
    )
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    tab_answer, tab_timeline, tab_artifacts, tab_json = st.tabs(["Réponse du hub", "Timeline", "Artifacts", "JSON"])
    with tab_answer:
        st.markdown(
            f"<div class='answer-body'>{md_html(result.get('aggregated_answer', ''))}</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"Protocole : {result.get('protocol', 'A2A 0.3')} · Hub : {result.get('hub', 'VOLTIS')}")
    with tab_timeline:
        st.markdown(trace_html(result.get("timeline", [])), unsafe_allow_html=True)
        try:
            logs = requests.get(f"{A2A_URL}/delegations?limit=10", timeout=2).json().get("delegations", []) if online else []
        except Exception:
            logs = []
        if logs:
            st.markdown("<div class='section-title'>Journal des délégations</div>", unsafe_allow_html=True)
            html_table(logs)
    with tab_artifacts:
        artifacts = result.get("artifacts", [])
        if artifacts:
            columns = st.columns(min(len(artifacts), 3), gap="large")
            for index, artifact in enumerate(artifacts):
                with columns[index % len(columns)]:
                    st.markdown(
                        f"<div class='card'><h3>{esc(artifact.get('agent_label', artifact.get('agent_id', '')))}</h3>"
                        f"<p>{esc(artifact.get('summary', ''))}</p>"
                        f"<div class='tag'>{esc(artifact.get('mode', 'local'))} · {artifact.get('latency_ms', 0)} ms</div></div>",
                        unsafe_allow_html=True,
                    )
                    for finding in artifact.get("findings", [])[:4]:
                        st.markdown(f"- {finding}")
                    if artifact.get("sources"):
                        st.caption("Sources : " + ", ".join(source["citation"] for source in artifact["sources"][:2]))
        else:
            st.info("Aucun artifact.")
    with tab_json:
        st.json(result, expanded=False)
    st.markdown(
        "<div class='footer'><span>A2A 0.3 · AgentCard · message/send · agrégation</span>"
        "<span>Journal : data/a2a_delegations.jsonl</span></div>",
        unsafe_allow_html=True,
    )


def _local_orchestration(question: str, region: str, max_agents: int, reason: str = "") -> dict:
    started = time.perf_counter()
    correlation_id = f"A2A-LOCAL-{datetime.now().strftime('%H%M%S')}"
    selected = _select_agents(question, max(2, max_agents))
    artifacts = [handle_agent(agent_id, question, {"region_code": region}, correlation_id) for agent_id in selected]
    for artifact in artifacts:
        artifact["mode"] = "repli local"
    return {
        "correlation_id": correlation_id,
        "question": question,
        "region_code": region,
        "selected_agents": selected,
        "artifacts": artifacts,
        "aggregated_answer": _aggregate(question, correlation_id, artifacts),
        "timeline": [
            {"step": "selection", "detail": ", ".join(selected), "status": "ok", "latency_ms": 1, "timestamp": datetime.now().strftime("%H:%M:%S")},
            *[
                {"step": "delegation", "detail": artifact.get("summary", "")[:100], "status": artifact.get("status", "ok"), "latency_ms": artifact.get("latency_ms", 0), "timestamp": datetime.now().strftime("%H:%M:%S")}
                for artifact in artifacts
            ],
            {"step": "aggregation", "detail": "réponse consolidée", "status": "ok", "latency_ms": round((time.perf_counter() - started) * 1000, 1), "timestamp": datetime.now().strftime("%H:%M:%S")},
        ],
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        "hub": "VOLTIS Agentic Hub (local)",
        "protocol": "A2A 0.3 · repli local",
        "fallback_reason": reason,
    }


def page_stats() -> None:
    hero(
        "Données & statistiques",
        "Le réseau en chiffres : consommation, mix, qualité et incidents",
        "Explorez les données synthétiques du réseau : huit régions, 42,3 TWh, 9,25 millions de clients "
        "et 90 jours d'incidents. Les graphiques alimentent les agents et la documentation.",
        [("8 régions", "gold"), ("42,3 TWh", "teal"), ("72 incidents", ""), ("12 mois", "")],
    )
    c1, c2, c3 = st.columns([1.3, 1, 1])
    with c1:
        region = st.selectbox(
            "Périmètre", ["NATIONAL"] + [region["code"] for region in core.regions()],
            format_func=lambda code: "National" if code == "NATIONAL" else core.region_name(code),
            key="stats_region",
        )
    with c2:
        metric = st.selectbox("Indicateur", ["Consommation", "Pointe", "Qualité", "Incidents"], key="stats_metric")
    with c3:
        months = st.slider("Fenêtre (mois)", 3, 12, 12, key="stats_months")

    kpis = core.national_kpis()
    quality = core.service_quality(region)
    summary = core.outage_summary(region)
    metrics_row(
        [
            ("Consommation", f"{kpis['consumption_gwh']/1000:.1f} TWh", "⚡", "national", "#EEF5FC"),
            ("Pointe (MW)", f"{kpis['peak_mw']:,.0f}".replace(",", " "), "▲", "national", "#FFF7E0"),
            ("SAIDI", f"{quality.get('saidi_min', 0):.0f} min", "⏱", quality.get("status", ""), "#EAF8F4"),
            ("Pertes", f"{quality.get('losses_pct', 0):.1f} %", "◇", "moyenne", "#FDECEA"),
            ("Incidents", str(summary.get("incidents", 0)), "⚠", f"{summary.get('active', 0)} actifs", "#EEF5FC"),
            ("Renouvelable", f"{kpis['renewable_share_pct']:.1f} %", "☀", "mix national", "#FFF7E0"),
        ]
    )
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.4, 1], gap="large")
    with col1:
        consumption = core.consumption_series(region)[-months:]
        labels = [row["month"] for row in consumption]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=labels, y=[row["consumption_gwh"] for row in consumption], name="GWh", marker_color=NAVY))
        fig.add_trace(
            go.Scatter(
                x=labels, y=[row["peak_mw"] for row in consumption], name="Pointe (MW)", yaxis="y2",
                line=dict(color=AMBER, width=2.5), mode="lines+markers",
            )
        )
        fig.update_layout(
            title="Consommation mensuelle et pointe",
            yaxis=dict(title="GWh"),
            yaxis2=dict(title="MW", overlaying="y", side="right", showgrid=False),
        )
        st.plotly_chart(plot_layout(fig, 340), use_container_width=True, config={"displayModeBar": False})
    with col2:
        mix = core.production_mix()
        fig = go.Figure(
            go.Pie(
                labels=[source["source"] for source in mix["sources"]],
                values=[source["share_pct"] for source in mix["sources"]],
                hole=0.55,
                marker=dict(colors=[source["color"] for source in mix["sources"]]),
                textinfo="percent",
                textfont_size=9,
            )
        )
        fig.update_layout(title="Mix de production")
        st.plotly_chart(plot_layout(fig, 340), use_container_width=True, config={"displayModeBar": False})

    col1, col2 = st.columns(2, gap="large")
    with col1:
        rows = core.load_curve()
        if region != "NATIONAL":
            rows = [row for row in rows if row["region_code"] == region]
        profile: dict[int, list[float]] = {}
        for row in rows:
            profile.setdefault(row["hour"], []).append(row["load_mw"])
        hours = sorted(profile)
        averages = [sum(profile[hour]) / len(profile[hour]) for hour in hours]
        fig = go.Figure(
            go.Scatter(
                x=hours, y=averages, mode="lines+markers",
                line=dict(color=TEAL, width=2.4), marker=dict(size=6),
                hovertemplate="%{x}h · %{y:,.0f} MW<extra></extra>",
            )
        )
        fig.update_layout(title="Profil horaire moyen (30 jours)")
        fig.update_xaxes(title="Heure", dtick=2)
        fig.update_yaxes(title="MW")
        st.plotly_chart(plot_layout(fig, 320), use_container_width=True, config={"displayModeBar": False})
    with col2:
        causes = sorted(summary.get("by_cause", {}).items(), key=lambda item: item[1])
        fig = go.Figure(
            go.Bar(
                x=[count for _, count in causes], y=[cause for cause, _ in causes],
                orientation="h", marker_color=AMBER,
                hovertemplate="%{y} · %{x} incidents<extra></extra>",
            )
        )
        fig.update_layout(title="Incidents par cause")
        st.plotly_chart(plot_layout(fig, 320), use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div class='section-title'>Performance des régions</div>", unsafe_allow_html=True)
    table = core.region_table()
    fig = go.Figure(
        go.Scatter(
            x=[row["losses_pct"] for row in table],
            y=[row["saidi_min"] for row in table],
            mode="markers+text",
            text=[row["name"] for row in table],
            textposition="top center",
            textfont=dict(size=8),
            marker=dict(
                size=[max(10, min(42, row["consumption_gwh"] / 280)) for row in table],
                color=[row["renewable_share_pct"] for row in table],
                colorscale=[[0, "#DCE8F4"], [1, TEAL]],
                showscale=True,
                colorbar=dict(title="% renouv."),
                line=dict(color="white", width=1),
            ),
            hovertemplate="%{text}<br>Pertes %{x:.1f} % · SAIDI %{y:.0f} min<extra></extra>",
        )
    )
    fig.update_layout(title="Pertes vs SAIDI (taille = consommation)")
    fig.update_xaxes(title="Pertes (%)")
    fig.update_yaxes(title="SAIDI (min)")
    st.plotly_chart(plot_layout(fig, 380), use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div class='section-title'>Données détaillées</div>", unsafe_allow_html=True)
    display = [
        {
            "Région": row["name"],
            "Code": row["code"],
            "Clients": row["clients"],
            "Consommation (GWh)": row["consumption_gwh"],
            "Pointe (MW)": row["peak_mw"],
            "% renouv.": row["renewable_share_pct"],
            "Pertes (%)": row["losses_pct"],
            "SAIDI (min)": row["saidi_min"],
            "SAIFI": row["saifi"],
        }
        for row in table
    ]
    html_table(display)
    st.download_button(
        "Télécharger le tableau (CSV)",
        data=to_csv(display),
        file_name="volt_is_regions.csv",
        mime="text/csv",
    )

    st.markdown("<div class='section-title' style='margin-top:20px'>Benchmark Reflexion — 5 tâches</div>", unsafe_allow_html=True)
    bench_path = DATA / "benchmarks.json"
    if bench_path.exists():
        bench = json.loads(bench_path.read_text(encoding="utf-8"))
        bench_rows = [
            {
                "Tâche": task["id"],
                "Question": task["question"][:70] + "…",
                "Initial": task["initial"]["overall"],
                "Final": task["final"]["overall"],
                "Gain": task["gain"],
                "Latence (ms)": task["elapsed_ms"],
                "Citations": task["citations"],
            }
            for task in bench["tasks"]
        ]
        col1, col2 = st.columns([1, 1.6], gap="large")
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Initial", x=[row["Tâche"] for row in bench_rows], y=[row["Initial"] for row in bench_rows], marker_color="#F0C9C4"))
            fig.add_trace(go.Bar(name="Final", x=[row["Tâche"] for row in bench_rows], y=[row["Final"] for row in bench_rows], marker_color=GREEN))
            fig.update_layout(barmode="group", title="Scores avant / après Reflexion", yaxis_range=[0, 10])
            st.plotly_chart(plot_layout(fig, 300), use_container_width=True, config={"displayModeBar": False})
        with col2:
            html_table(bench_rows)
        st.caption(
            f"Moyenne : {bench['averages']['initial']}/10 → {bench['averages']['final']}/10 "
            f"(gain +{bench['averages']['gain']}) · latence {bench['averages']['latency_ms']} ms · "
            f"{bench['averages']['citations']} citations/réponse."
        )
    st.markdown(
        "<div class='footer'><span>Données 100 % synthétiques · calibrées sur des ordres de grandeur réels</span>"
        "<span>Fichiers : data/regions.json · load_curve.csv · outages.csv</span></div>",
        unsafe_allow_html=True,
    )


def page_architecture() -> None:
    hero(
        "Architecture & protocoles",
        "Un hub, trois protocoles, quatre agents",
        "MCP pour les outils, A2A pour la collaboration, LangGraph pour l'orchestration et le RAG hybride "
        "pour la connaissance. Le tout est conteneurisé et observable.",
        [("Hub interopérable", "gold"), ("MCP 8100", "teal"), ("A2A 8101-8105", ""), ("Docker", "")],
    )
    images = [
        ("architecture_hub.png", "Architecture globale — expérience, orchestration, agents, données, infrastructure"),
        ("workflow_langgraph.png", "Workflow LangGraph — Planner → Retriever → Tools → Writer → Critic ⇄ Refiner"),
        ("rag_pipeline.png", "Agentic RAG — planification, retrieval hybride, vérification et citations"),
        ("architecture_mcp.png", "MCP — 10 outils exposés avec schémas et traçabilité"),
        ("architecture_a2a.png", "A2A — découverte, délégation parallèle et agrégation"),
        ("docker_topology.png", "Docker Compose — dashboard, MCP, A2A et volume partagé"),
    ]
    for index in range(0, len(images), 2):
        col1, col2 = st.columns(2, gap="large")
        for column, (filename, caption) in zip((col1, col2), images[index:index + 2]):
            with column:
                path = ASSETS / filename
                if path.exists():
                    st.image(str(path), use_container_width=True)
                st.caption(caption)

    st.markdown("<div class='section-title'>Ports & services</div>", unsafe_allow_html=True)
    ports = [
        {"Service": "Dashboard Streamlit", "Port": 8033, "Protocole": "HTTP", "Rôle": "Interface, formulaires, KPI, traces"},
        {"Service": "Serveur MCP", "Port": 8100, "Protocole": "JSON-RPC 2.0 / SSE", "Rôle": "10 outils, ressources, prompts"},
        {"Service": "Orchestrateur A2A", "Port": 8101, "Protocole": "A2A 0.3", "Rôle": "Discovery, sélection, délégation, agrégation"},
        {"Service": "Grid Analyst", "Port": 8102, "Protocole": "A2A 0.3", "Rôle": "KPI, consommation, mix"},
        {"Service": "Outage Inspector", "Port": 8103, "Protocole": "A2A 0.3", "Rôle": "Incidents, SAIDI/SAIFI, MTTR"},
        {"Service": "Billing Advisor", "Port": 8104, "Protocole": "A2A 0.3", "Rôle": "Factures, tarifs, économies"},
        {"Service": "Forecast Agent", "Port": 8105, "Protocole": "A2A 0.3", "Rôle": "Prévision, pointe, réserve"},
    ]
    html_table(ports)

    st.markdown("<div class='section-title' style='margin-top:18px'>Critères de validation</div>", unsafe_allow_html=True)
    criteria = [
        {"Critère": "Interopérabilité", "Preuve": "MCP JSON-RPC + A2A HTTP + AgentCards ; dashboard appelle les deux."},
        {"Critère": "Agentic RAG", "Preuve": "Planner, retrieval multi-étapes, vérification, citations, critique."},
        {"Critère": "Collaboration ≥ 2 agents", "Preuve": "L'orchestrateur sélectionne 2 à 4 agents et agrège leurs artifacts."},
        {"Critère": "Auto-réflexion", "Preuve": "Boucle Writer → Critic → Refiner, scores avant/après sur 5 tâches."},
        {"Critère": "Architecture", "Preuve": "Schéma du hub, couches, ports, flux et ADR documentés."},
        {"Critère": "Documentation", "Preuve": "DOCX final, README, guide, 5 AgentCards complètes."},
        {"Critère": "Démonstration", "Preuve": "Dashboard live 8033, scénario bout en bout, captures et JSON."},
    ]
    html_table(criteria)

    st.markdown("<div class='section-title' style='margin-top:18px'>Manifests téléchargeables</div>", unsafe_allow_html=True)
    manifests = [
        ("MCP", "mcp_manifest.json"),
        ("A2A", "a2a_manifest.json"),
        ("RAG", "rag_manifest.json"),
        ("LangGraph", "langgraph_manifest.json"),
        ("Architecture", "architecture_manifest.json"),
        ("Tout-en-un", "agentic_ai_electricity_full.json"),
    ]
    columns = st.columns(3, gap="large")
    for index, (label, filename) in enumerate(manifests):
        path = JSON_DIR / filename
        with columns[index % 3]:
            if path.exists():
                st.download_button(
                    f"⬇ {label} · {file_size(path)}",
                    data=path.read_bytes(),
                    file_name=filename,
                    mime="application/json",
                    use_container_width=True,
                    key=f"dl_{filename}",
                )
    st.caption("Les manifests contiennent les schémas, les exemples, les AgentCards et le rapport de benchmark.")
    st.markdown(
        "<div class='footer'><span>Architecture hub · MCP + A2A + RAG + LangGraph</span>"
        "<span>Documentation : docs/Documentation_Finale_VOLTIS.docx</span></div>",
        unsafe_allow_html=True,
    )


def page_docs() -> None:
    hero(
        "Livrables & documentation",
        "Tout le projet dans un seul espace",
        "Documentation finale, présentation, rapports JSON, captures d'écran et guide de lancement. "
        "Les fichiers sont générés par les scripts du dossier scripts/.",
        [("DOCX", "gold"), ("PPTX", "teal"), ("5 AgentCards", ""), ("Captures", "")],
    )
    st.markdown("<div class='section-title'>Documents</div>", unsafe_allow_html=True)
    doc_files = sorted(list(DOCS.glob("*.docx")) + list(DOCS.glob("*.pdf")))
    if doc_files:
        for path in doc_files:
            st.markdown(
                f"<div class='doc-row'><div><div class='doc-name'>{esc(path.name)}</div>"
                f"<div class='doc-meta'>{file_size(path)} · {path.suffix[1:].upper()}</div></div>"
                f"<span class='pill'>{path.suffix[1:].upper()}</span></div>",
                unsafe_allow_html=True,
            )
            st.download_button(
                f"Télécharger {path.name}",
                data=path.read_bytes(),
                file_name=path.name,
                key=f"dl_doc_{path.name}",
            )
    else:
        st.info("Documentation en cours de génération.")

    st.markdown("<div class='section-title' style='margin-top:18px'>Présentation</div>", unsafe_allow_html=True)
    deck_files = sorted(list(PRESENTATION.glob("*.pptx")) + list(PRESENTATION.glob("*.pdf")))
    if deck_files:
        for path in deck_files:
            st.markdown(
                f"<div class='doc-row'><div><div class='doc-name'>{esc(path.name)}</div>"
                f"<div class='doc-meta'>{file_size(path)} · {path.suffix[1:].upper()}</div></div>"
                f"<span class='pill'>{path.suffix[1:].upper()}</span></div>",
                unsafe_allow_html=True,
            )
            st.download_button(
                f"Télécharger {path.name}",
                data=path.read_bytes(),
                file_name=path.name,
                key=f"dl_deck_{path.name}",
            )
    else:
        st.info("Présentation en cours de génération.")

    st.markdown("<div class='section-title' style='margin-top:18px'>Captures du dashboard</div>", unsafe_allow_html=True)
    shots = sorted(SCREENSHOTS.glob("*.png"))
    if shots:
        columns = st.columns(3, gap="large")
        for index, path in enumerate(shots[:6]):
            with columns[index % 3]:
                st.image(str(path), use_container_width=True)
                st.caption(path.name)
    else:
        st.caption("Les captures seront ajoutées après la démonstration.")

    video = VIDEOS / "VOLTIS_Demo.mp4"
    if video.exists():
        st.markdown("<div class='section-title' style='margin-top:18px'>Vidéo de démonstration</div>", unsafe_allow_html=True)
        st.video(str(video))

    st.markdown("<div class='section-title' style='margin-top:18px'>Lancement rapide</div>", unsafe_allow_html=True)
    st.code(
        "python main.py            # dashboard + MCP + A2A\n"
        "python main.py dashboard  # dashboard seul (8033)\n"
        "python main.py mcp        # serveur MCP (8100)\n"
        "python main.py a2a        # orchestrateur + agents (8101-8105)\n"
        "python main.py demo       # benchmark Reflexion + orchestration A2A\n"
        "python main.py check      # validation des données et livrables\n\n"
        "docker compose up --build # tout l'écosystème dans Docker",
        language="bash",
    )
    st.markdown(
        "<div class='footer'><span>VOLTIS v1.0 · documentation finale</span>"
        "<span>README.md · LIVRABLES.md · MANIFEST.txt</span></div>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# Sidebar & routing
# --------------------------------------------------------------------------- #
def sidebar() -> str:
    page_slugs = {
        "assistant": MENU[1],
        "mcp": MENU[2],
        "a2a": MENU[3],
        "stats": MENU[4],
        "architecture": MENU[5],
        "docs": MENU[6],
    }
    requested = st.query_params.get("page", "")
    if requested in page_slugs:
        st.session_state.nav = page_slugs[requested]
    with st.sidebar:
        if (ASSETS / "logo_sidebar.png").exists():
            st.image(str(ASSETS / "logo_sidebar.png"), use_container_width=True)
        st.markdown(
            "<div style='font-size:.72rem;color:#9FB4CC;margin:2px 0 14px'>"
            "Agentic AI for the Electricity Sector</div>",
            unsafe_allow_html=True,
        )
        page = st.radio("Navigation", MENU, key="nav", label_visibility="collapsed")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        mcp = mcp_health()
        a2a = a2a_health()
        st.markdown(status_pill(mcp.get("online", False), "MCP 8100"), unsafe_allow_html=True)
        st.markdown(status_pill(a2a.get("online", False), "A2A 8101"), unsafe_allow_html=True)
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:.68rem;color:#8AA0B8;line-height:1.7'>"
            "10 outils MCP<br>4 agents A2A<br>12 documents / 49 chunks<br>"
            "5 tâches benchmark<br>Docker ready</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:.64rem;color:#6F879F;line-height:1.6'>"
            "v1.0 · 12 novembre 2026<br>Données 100 % synthétiques<br>Aucune API réelle</div>",
            unsafe_allow_html=True,
        )
    return page


def main() -> None:
    inject_css()
    page = sidebar()
    if page == MENU[0]:
        page_home()
    elif page == MENU[1]:
        page_assistant()
    elif page == MENU[2]:
        page_mcp()
    elif page == MENU[3]:
        page_a2a()
    elif page == MENU[4]:
        page_stats()
    elif page == MENU[5]:
        page_architecture()
    else:
        page_docs()


if __name__ == "__main__":
    main()
