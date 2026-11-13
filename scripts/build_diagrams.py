# -*- coding: utf-8 -*-
"""Schémas d'architecture, de workflow et de déploiement VOLTIS."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

NAVY = "#0A1F3C"
NAVY2 = "#14365C"
AMBER = "#F5B301"
TEAL = "#16A6A1"
BLUE = "#3B82C4"
GREEN = "#2E8B72"
RED = "#D9534F"
PURPLE = "#7A5AA6"
LIGHT = "#F4F7FB"
BORDER = "#D8E3EF"
INK = "#12263F"
MUTED = "#64748B"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.facecolor": LIGHT,
        "figure.facecolor": LIGHT,
    }
)


def canvas(figsize=(16, 9)):
    fig, ax = plt.subplots(figsize=figsize, dpi=190)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis("off")
    fig.patch.set_facecolor(LIGHT)
    return fig, ax


def rr(ax, x, y, w, h, fc="white", ec=BORDER, lw=1.2, radius=0.12, z=2, alpha=1.0):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.015,rounding_size={radius}",
        facecolor=fc, edgecolor=ec, linewidth=lw, zorder=z, alpha=alpha,
    )
    ax.add_patch(box)
    return box


def label(ax, x, y, text, size=10, color=INK, weight="normal", ha="left", va="center", z=6, style="normal"):
    ax.text(x, y, text, fontsize=size, color=color, weight=weight, ha=ha, va=va,
            zorder=z, style=style)


def arrow(ax, start, end, color=NAVY, lw=1.8, style="-|>", ls="-", rad=0.0, z=5):
    ax.add_patch(
        FancyArrowPatch(
            start, end, arrowstyle=style, mutation_scale=14, color=color,
            linewidth=lw, linestyle=ls, connectionstyle=f"arc3,rad={rad}", zorder=z,
        )
    )


def title(ax, kicker, main, sub=None):
    ax.add_patch(Rectangle((0, 8.55), 16, 0.45, facecolor=NAVY, edgecolor="none", zorder=1))
    label(ax, 0.45, 8.78, kicker.upper(), 8.5, AMBER, "bold")
    label(ax, 0.45, 8.08, main, 21, INK, "bold")
    if sub:
        label(ax, 0.45, 7.70, sub, 9.8, MUTED)


def footer(ax, text):
    ax.plot([0.45, 15.55], [0.38, 0.38], color=BORDER, lw=1)
    label(ax, 0.45, 0.20, text, 7.8, MUTED)
    label(ax, 15.55, 0.20, "VOLTIS · Agentic AI for the Electricity Sector", 7.8, MUTED, ha="right")


def node(ax, x, y, w, h, head, lines, color=NAVY, badge="", fc="white", head_h=0.38):
    box = rr(ax, x, y, w, h, fc=fc, ec=BORDER)
    ax.add_patch(
        FancyBboxPatch(
            (x, y + h - head_h), w, head_h,
            boxstyle="round,pad=0.015,rounding_size=0.1",
            facecolor=color, edgecolor="none", zorder=3,
        )
    )
    label(ax, x + 0.14, y + h - head_h / 2, head, 9.4, "white", "bold")
    if badge:
        label(ax, x + w - 0.12, y + h - head_h / 2, badge, 7.2, "white", "bold", ha="right")
    yy = y + h - head_h - 0.23
    for line in lines:
        label(ax, x + 0.14, yy, line, 7.6, MUTED)
        yy -= 0.205
    return box


def chip(ax, x, y, w, text, color=NAVY, size=7.0):
    rr(ax, x, y, w, 0.22, fc=color, ec="none", radius=0.10)
    label(ax, x + w / 2, y + 0.11, text, size, "white", "bold", ha="center")


def arch_hub():
    fig, ax = canvas()
    title(
        ax,
        "Architecture globale",
        "VOLTIS — un hub agentique interopérable pour le secteur électrique",
        "MCP expose les outils, A2A fait collaborer les agents, LangGraph orchestre la réflexion et le RAG garantit des réponses sourcées.",
    )
    # Experience
    node(ax, 0.45, 5.25, 2.45, 1.75, "Utilisateur", ["Question métier", "Région · profil", "Décision"], BLUE, "Client")
    node(ax, 3.25, 4.85, 2.65, 2.55, "Dashboard 8033", ["Streamlit + Plotly", "Formulaires & KPI", "Trace, scores, sources", "Repli local"], NAVY, "UI")
    # Hub
    node(ax, 6.45, 4.55, 3.10, 3.20, "Hub LangGraph", [
        "Planner → intention",
        "RAG hybride BM25+TF-IDF",
        "Outils MCP · A2A",
        "Writer → Critic → Refiner",
        "Sources + score qualité",
    ], AMBER, "Orchestration", head_h=0.42)
    # MCP
    node(ax, 10.15, 6.15, 2.55, 1.55, "Serveur MCP 8100", ["JSON-RPC 2.0 / SSE", "10 outils · schémas", "Découverte auto"], TEAL, "MCP")
    # A2A
    node(ax, 13.05, 6.15, 2.45, 1.55, "Orchestrateur A2A", ["8101 · AgentCards", "Délégation //", "correlation_id"], PURPLE, "A2A")
    # agents
    agents = [
        ("Grid Analyst", "8102 · KPI & mix", TEAL),
        ("Outage Inspector", "8103 · incidents", RED),
        ("Billing Advisor", "8104 · tarifs", AMBER),
        ("Forecast Agent", "8105 · pointe", BLUE),
    ]
    for index, (name, sub, color) in enumerate(agents):
        x = 10.15 + (index % 2) * 2.72
        y = 4.25 - (index // 2) * 1.18
        rr(ax, x, y, 2.55, 0.92, fc="white", ec=BORDER)
        rr(ax, x, y, 0.07, 0.92, fc=color, ec="none")
        label(ax, x + 0.18, y + 0.62, name, 8.4, INK, "bold")
        label(ax, x + 0.18, y + 0.32, sub, 7.2, MUTED)
    # data + docker
    node(ax, 3.25, 1.55, 5.0, 1.55, "Données & connaissances", [
        "12 documents · 49 chunks · 8 régions",
        "42,3 TWh · 9,25 M clients · 72 incidents",
        "CSV / JSON / Markdown · 100 % synthétique",
    ], GREEN, "Data")
    node(ax, 8.75, 1.55, 4.15, 1.55, "Traçabilité & évaluation", [
        "mcp_calls.jsonl · a2a_delegations.jsonl",
        "Scores Reflexion · 5 tâches benchmark",
        "Logs corrélés par correlation_id",
    ], NAVY2, "Observabilité")
    node(ax, 13.35, 1.55, 2.15, 1.55, "Docker", ["3 services", "Healthchecks", "Ports exposés"], "#546E7A", "Infra")
    # arrows
    arrow(ax, (2.90, 6.10), (3.25, 6.10), BLUE, 2)
    arrow(ax, (5.90, 6.10), (6.45, 6.10), NAVY, 2.2)
    arrow(ax, (9.55, 6.65), (10.15, 6.90), TEAL, 1.8)
    label(ax, 9.62, 6.95, "MCP", 6.8, TEAL, "bold")
    arrow(ax, (9.55, 5.65), (13.05, 6.75), PURPLE, 1.8)
    label(ax, 10.55, 6.32, "A2A", 6.8, PURPLE, "bold")
    arrow(ax, (12.70, 6.40), (13.05, 6.40), PURPLE, 1.6)
    arrow(ax, (12.70, 5.70), (13.05, 5.70), PURPLE, 1.6)
    arrow(ax, (6.00, 5.10), (5.75, 3.10), GREEN, 1.4, ls="--")
    arrow(ax, (9.10, 4.55), (9.10, 3.10), NAVY2, 1.4, ls="--")
    arrow(ax, (11.20, 4.25), (11.20, 3.10), MUTED, 1.3, ls=":")
    arrow(ax, (14.10, 6.15), (14.10, 3.10), MUTED, 1.3, ls=":")
    # protocol band
    rr(ax, 0.45, 0.55, 15.0, 0.55, fc="#E8F5F4", ec="#BCE3DE")
    label(ax, 0.65, 0.82, "Protocoles", 8.2, TEAL, "bold")
    labels = ["MCP 2025-06-18 · JSON-RPC 2.0", "A2A 0.3 · AgentCard + message/send", "RAG hybride · BM25 + TF-IDF", "Reflexion · Generate → Critic → Refine"]
    for index, text in enumerate(labels):
        label(ax, 2.35 + index * 3.35, 0.82, text, 7.2, INK)
    footer(ax, "Hub interopérable · MCP 8100 · A2A 8101 · Dashboard 8033 · 4 agents spécialisés")
    fig.savefig(ASSETS / "architecture_hub.png", bbox_inches="tight", facecolor=LIGHT)
    plt.close(fig)


def workflow_graph():
    fig, ax = canvas((16, 8.2))
    title(
        ax,
        "Workflow LangGraph",
        "Une boucle Reflexion mesurée, du brouillon à la réponse publiable",
        "Chaque nœud est un état typé ; le Critic note la réponse et déclenche le Refiner tant que le seuil n'est pas atteint.",
    )
    y = 4.75
    boxes = [
        ("Question", "langage naturel", BLUE, 0.55, 2.05),
        ("Planner", "intention + outils", NAVY, 2.95, 2.15),
        ("Retriever", "BM25 + TF-IDF", TEAL, 5.45, 2.15),
        ("Tools", "MCP · 10 outils", AMBER, 7.95, 2.15),
        ("Writer", "brouillon", PURPLE, 10.45, 2.05),
        ("Critic", "scores 4 axes", RED, 12.85, 2.05),
    ]
    for head, sub, color, x, w in boxes:
        node(ax, x, y, w, 1.35, head, [sub], color, head_h=0.40)
    for start, end in [(2.60, 2.95), (5.10, 5.45), (7.60, 7.95), (10.10, 10.45), (12.50, 12.85)]:
        arrow(ax, (start, y + 0.68), (end, y + 0.68), NAVY, 2)
    # Refiner loop
    node(ax, 10.45, 2.35, 2.05, 1.25, "Refiner", ["sources + plan", "itération +1"], AMBER, head_h=0.38)
    node(ax, 12.85, 2.35, 2.05, 1.25, "Finalize", ["réponse + confiance"], GREEN, head_h=0.38)
    arrow(ax, (13.85, 4.75), (13.85, 3.60), RED, 1.6)
    label(ax, 13.55, 4.18, "score < 8,2", 7.0, RED, "bold", ha="right")
    arrow(ax, (12.85, 2.95), (12.50, 2.95), AMBER, 1.6)
    arrow(ax, (10.45, 2.95), (10.10, 2.95), AMBER, 1.6)
    arrow(ax, (11.47, 3.60), (11.47, 4.75), AMBER, 1.6)
    label(ax, 11.55, 4.18, "re-critique", 7.0, AMBER, "bold")
    arrow(ax, (14.90, 4.75), (15.45, 4.75), GREEN, 1.6)
    label(ax, 15.50, 4.75, "Réponse", 8.0, GREEN, "bold")
    # score panel
    rr(ax, 0.55, 1.05, 6.35, 1.75, fc="white", ec=BORDER)
    label(ax, 0.75, 2.55, "Mesure du gain (5 tâches)", 9.0, NAVY, "bold")
    label(ax, 0.75, 2.18, "Score initial", 7.4, MUTED)
    label(ax, 2.35, 2.18, "6,48 / 10", 10.0, RED, "bold")
    label(ax, 4.05, 2.18, "Score final", 7.4, MUTED)
    label(ax, 5.55, 2.18, "9,44 / 10", 10.0, GREEN, "bold")
    label(ax, 0.75, 1.72, "Gain moyen +2,96 pts · 2 itérations · 7,2 citations/réponse", 7.4, INK)
    rr(ax, 0.75, 1.30, 5.95, 0.20, fc="#EAF0F7", ec="none", radius=0.08)
    rr(ax, 0.75, 1.30, 5.95 * 0.648, 0.20, fc=RED, ec="none", radius=0.08, alpha=0.55)
    rr(ax, 0.75, 1.30, 5.95 * 0.944, 0.20, fc=GREEN, ec="none", radius=0.08, alpha=0.55)
    # criteria panel
    rr(ax, 7.25, 1.05, 8.20, 1.75, fc="#FFFDF4", ec="#EEDB9A")
    label(ax, 7.45, 2.55, "Critères du Critic", 9.0, "#7A5B00", "bold")
    criteria = [
        ("Clarté", "28 %"), ("Exactitude", "34 %"), ("Concision", "14 %"), ("Cohérence", "24 %"),
    ]
    for index, (name, weight) in enumerate(criteria):
        x = 7.45 + index * 1.92
        label(ax, x, 2.10, name, 8.0, INK, "bold")
        label(ax, x, 1.78, weight, 9.2, "#8A6100", "bold")
    label(ax, 7.45, 1.38, "Seuil de publication : 8,2/10 · max 2 itérations · sources obligatoires", 7.2, MUTED)
    footer(ax, "Graphe LangGraph · 7 nœuds · état typé · boucle conditionnelle · checkpoint désactivé en démo")
    fig.savefig(ASSETS / "workflow_langgraph.png", bbox_inches="tight", facecolor=LIGHT)
    plt.close(fig)


def arch_mcp():
    fig, ax = canvas()
    title(
        ax,
        "Protocole MCP",
        "MCP — exposer les outils du réseau à l'agent",
        "Le serveur publie 10 outils avec leur schéma JSON ; l'agent les découvre, choisit le bon outil et reçoit un résultat structuré.",
    )
    node(ax, 0.45, 4.85, 2.55, 2.15, "Client MCP", ["Dashboard 8033", "LangGraph", "Langflow / IDE"], BLUE, "Client")
    node(ax, 3.45, 3.55, 3.55, 4.35, "Serveur MCP 8100", [
        "Transport : JSON-RPC 2.0",
        "Streamable HTTP : /mcp",
        "SSE : /sse · messages",
        "REST de secours : /api/tool",
        "initialize · tools/list · tools/call",
        "10 outils · 3 ressources · 2 prompts",
    ], TEAL, "MCP", head_h=0.42)
    tools = [
        ("get_grid_kpis", "KPI nationaux"),
        ("get_region_profile", "profil région"),
        ("get_consumption", "série mensuelle"),
        ("get_production_mix", "mix & CO₂"),
        ("query_outages", "incidents"),
        ("forecast_load", "pointe & risque"),
        ("simulate_bill", "facture"),
        ("search_knowledge", "RAG hybride"),
        ("recommend_energy_savings", "économies"),
        ("get_service_quality", "SAIDI/SAIFI"),
    ]
    for index, (name, desc) in enumerate(tools):
        x = 7.45 + (index % 2) * 3.05
        y = 6.55 - (index // 2) * 0.92
        rr(ax, x, y, 2.90, 0.78, fc="white", ec=BORDER)
        label(ax, x + 0.12, y + 0.48, name, 7.4, INK, "bold")
        label(ax, x + 0.12, y + 0.22, desc, 6.7, MUTED)
    node(ax, 7.45, 1.55, 5.95, 1.45, "Données & corpus", [
        "regions.json · load_curve.csv · outages.csv",
        "customers.json · tariffs.json · corpus.json (12 docs)",
    ], GREEN, "Data")
    node(ax, 13.75, 3.95, 1.80, 3.55, "Traçabilité", ["appels", "arguments", "latence", "statut", "logs JSONL"], MUTED, "Audit")
    arrow(ax, (3.00, 5.95), (3.45, 5.95), NAVY, 2)
    arrow(ax, (7.00, 6.25), (7.45, 6.55), TEAL, 1.8, ls="--")
    arrow(ax, (7.00, 5.35), (7.45, 4.10), GREEN, 1.5, ls="--")
    arrow(ax, (13.40, 5.25), (13.75, 5.25), MUTED, 1.3, ls=":")
    label(ax, 7.05, 6.95, "tools/list", 6.6, TEAL, "bold")
    label(ax, 7.05, 4.75, "resources", 6.6, GREEN, "bold")
    footer(ax, "MCP 2025-06-18 · JSON-RPC 2.0 · 10 outils · ressources volt-is:// · prompts diagnostic & briefing")
    fig.savefig(ASSETS / "architecture_mcp.png", bbox_inches="tight", facecolor=LIGHT)
    plt.close(fig)


def arch_a2a():
    fig, ax = canvas()
    title(
        ax,
        "Protocole A2A",
        "A2A — découvrir, déléguer, agréger",
        "Chaque agent publie une AgentCard. L'orchestrateur sélectionne au moins deux spécialistes et trace chaque échange par correlation_id.",
    )
    node(ax, 0.45, 4.55, 2.35, 1.85, "Question", ["objectif métier", "région / priorité", "dashboard"], BLUE, "Input")
    node(ax, 3.20, 3.75, 2.75, 3.45, "Orchestrateur 8101", [
        "GET /agents (discovery)",
        "Sélection par capacités",
        "Délégation parallèle",
        "Agrégation des artifacts",
        "correlation_id unique",
    ], PURPLE, "A2A", head_h=0.42)
    agents = [
        ("Grid Analyst", "8102", ["KPI · mix", "consommation"], TEAL),
        ("Outage Inspector", "8103", ["incidents", "SAIDI/SAIFI"], RED),
        ("Billing Advisor", "8104", ["factures", "économies"], AMBER),
        ("Forecast Agent", "8105", ["pointe", "réserve"], BLUE),
    ]
    for index, (name, port, skills, color) in enumerate(agents):
        y = 6.10 - index * 1.28
        node(ax, 6.65, y, 3.10, 1.05, name, [" · ".join(skills), f"AgentCard · port {port}"], color, port, head_h=0.34)
    node(ax, 10.35, 4.35, 2.55, 2.25, "Agrégation", ["réponse unique", "4 artifacts", "sources dédupliquées"], GREEN, "Output")
    node(ax, 10.35, 1.55, 2.55, 1.75, "Dashboard 8033", ["cartes agents", "timeline", "logs A2A"], NAVY, "UI")
    node(ax, 13.35, 3.95, 2.15, 2.65, "Traçabilité", ["correlation_id", "latence par agent", "statut", "JSONL"], MUTED, "Audit")
    arrow(ax, (2.80, 5.45), (3.20, 5.45), NAVY, 2)
    for index in range(4):
        y = 6.62 - index * 1.28
        arrow(ax, (5.95, 5.55), (6.65, y), agents[index][3], 1.4, ls="--", rad=0.04)
        arrow(ax, (9.75, y), (10.35, 5.35), agents[index][3], 1.8, rad=-0.03)
    arrow(ax, (11.62, 4.35), (11.62, 3.30), NAVY, 1.6)
    arrow(ax, (12.90, 4.90), (13.35, 4.90), MUTED, 1.3, ls=":")
    label(ax, 6.70, 6.95, "discover", 6.8, PURPLE, "bold")
    label(ax, 9.80, 3.55, "aggregate", 6.8, GREEN, "bold")
    footer(ax, "A2A 0.3 · AgentCard /.well-known/agent.json · 4 agents + 1 orchestrateur · correlation_id propagé")
    fig.savefig(ASSETS / "architecture_a2a.png", bbox_inches="tight", facecolor=LIGHT)
    plt.close(fig)


def rag_pipeline():
    fig, ax = canvas((16, 8.5))
    title(
        ax,
        "Agentic RAG",
        "Du moteur de recherche au véritable agent documentaire",
        "L'agent planifie, reformule, vérifie la suffisance et cite ses sources avant de répondre.",
    )
    steps = [
        ("Question", ["langage naturel", "région + intention"], BLUE, 0.55, 2.05),
        ("Planner", ["décompose", "choisit k et filtres"], NAVY, 3.00, 2.05),
        ("Retriever", ["BM25 + TF-IDF", "expansion métier"], TEAL, 5.45, 2.10),
        ("Vérifier", ["suffisance ≥ 0,55", "reformuler si besoin"], AMBER, 7.95, 2.05),
        ("Writer", ["synthèse", "citations [n]"], PURPLE, 10.40, 2.05),
        ("Critic", ["4 scores", "Reflexion"], RED, 12.85, 2.05),
    ]
    y = 4.85
    for head, lines, color, x, w in steps:
        node(ax, x, y, w, 1.45, head, lines, color, head_h=0.38)
    for start, end in [(2.60, 3.00), (5.05, 5.45), (7.55, 7.95), (10.00, 10.40), (12.45, 12.85)]:
        arrow(ax, (start, y + 0.72), (end, y + 0.72), NAVY, 2)
    # reformulation loop
    arrow(ax, (8.97, 4.85), (8.97, 4.05), AMBER, 1.5)
    arrow(ax, (8.97, 4.05), (6.50, 4.05), AMBER, 1.5)
    arrow(ax, (6.50, 4.05), (6.50, 4.85), AMBER, 1.5)
    label(ax, 7.20, 3.88, "reformuler (max 2)", 6.8, "#8A6100", "bold")
    # corpus panel
    rr(ax, 0.55, 1.35, 5.30, 2.05, fc="white", ec=BORDER)
    label(ax, 0.75, 3.12, "Corpus indexé", 8.8, NAVY, "bold")
    docs = ["12 documents · 49 chunks", "Exploitation · maintenance · commercial", "Réglementation · cybersécurité · sécurité", "Chaque chunk = doc + version + article"]
    for index, line in enumerate(docs):
        label(ax, 0.75, 2.75 - index * 0.30, "· " + line, 7.2, MUTED)
    # citation panel
    rr(ax, 6.15, 1.35, 4.55, 2.05, fc="#F4FBF9", ec="#BFE5DB")
    label(ax, 6.35, 3.12, "Réponse sourcée", 8.8, GREEN, "bold")
    label(ax, 6.35, 2.75, "« La marge de réserve minimale est de 8 %… »", 7.4, INK, style="italic")
    label(ax, 6.35, 2.42, "[1] DOC-PREVISION · v2.9 · article 3", 7.0, GREEN, "bold")
    label(ax, 6.35, 2.10, "7,2 citations par réponse · 0 hallucination détectée", 6.8, MUTED)
    # critic panel
    rr(ax, 11.00, 1.35, 4.45, 2.05, fc="#FFF7F6", ec="#F0C9C4")
    label(ax, 11.20, 3.12, "Garde-fous", 8.8, RED, "bold")
    guards = ["Seuil de suffisance 0,55", "Sources obligatoires [n]", "Score Reflexion ≥ 8,2", "Repli local si service indisponible"]
    for index, line in enumerate(guards):
        label(ax, 11.20, 2.75 - index * 0.30, "· " + line, 7.1, MUTED)
    footer(ax, "Agentic RAG · planification · retrieval hybride · vérification · citations · auto-critique")
    fig.savefig(ASSETS / "rag_pipeline.png", bbox_inches="tight", facecolor=LIGHT)
    plt.close(fig)


def docker_topology():
    fig, ax = canvas((16, 8.0))
    title(
        ax,
        "Déploiement",
        "Docker Compose — trois services, un seul réseau",
        "Le dashboard appelle MCP et A2A par HTTP ; chaque service possède un healthcheck et un volume partagé en lecture.",
    )
    # host
    rr(ax, 0.55, 1.10, 14.90, 5.95, fc="#EEF3F9", ec="#C9D8E8", radius=0.15)
    label(ax, 0.80, 6.78, "Hôte Docker", 9.0, NAVY, "bold")
    # services
    node(ax, 1.00, 3.85, 4.30, 2.40, "dashboard", [
        "python main.py dashboard",
        "Streamlit · port 8033",
        "depends_on: mcp, a2a",
        "healthcheck HTTP /",
    ], NAVY, "8033", head_h=0.42)
    node(ax, 5.85, 3.85, 4.30, 2.40, "mcp", [
        "python main.py mcp",
        "FastAPI · port 8100",
        "10 outils · JSON-RPC",
        "healthcheck /api/health",
    ], TEAL, "8100", head_h=0.42)
    node(ax, 10.70, 3.85, 4.30, 2.40, "a2a", [
        "python main.py a2a",
        "orchestrateur 8101",
        "agents 8102 → 8105",
        "healthcheck /health",
    ], PURPLE, "8101-8105", head_h=0.42)
    # shared volume
    rr(ax, 1.00, 1.55, 9.15, 1.55, fc="white", ec=BORDER)
    label(ax, 1.20, 2.78, "Volume partagé (lecture seule)", 8.6, GREEN, "bold")
    label(ax, 1.20, 2.42, "data/ · json/ · docs/ · assets/ · a2a/agent_cards/", 7.2, MUTED)
    label(ax, 1.20, 2.10, "Mêmes données synthétiques pour les 3 services · aucune donnée personnelle", 7.0, MUTED)
    # network
    rr(ax, 10.70, 1.55, 4.30, 1.55, fc="white", ec=BORDER)
    label(ax, 10.90, 2.78, "Réseau & sécurité", 8.6, RED, "bold")
    label(ax, 10.90, 2.42, "réseau bridge dédié", 7.2, MUTED)
    label(ax, 10.90, 2.10, "CORS · Bearer en production", 7.0, MUTED)
    # arrows
    arrow(ax, (5.30, 5.05), (5.85, 5.05), TEAL, 2)
    arrow(ax, (10.15, 5.05), (10.70, 5.05), PURPLE, 2)
    label(ax, 5.42, 5.32, "HTTP", 6.8, TEAL, "bold")
    label(ax, 10.27, 5.32, "HTTP", 6.8, PURPLE, "bold")
    arrow(ax, (3.10, 3.85), (3.10, 3.10), GREEN, 1.4, ls="--")
    arrow(ax, (8.00, 3.85), (8.00, 3.10), GREEN, 1.4, ls="--")
    arrow(ax, (12.85, 3.85), (12.85, 3.10), GREEN, 1.4, ls="--")
    # commands
    rr(ax, 0.55, 0.55, 14.90, 0.42, fc=NAVY, ec="none", radius=0.08)
    label(ax, 0.75, 0.76, "docker compose up --build", 8.2, AMBER, "bold")
    label(ax, 4.60, 0.76, "→  http://localhost:8033  ·  MCP 8100  ·  A2A 8101", 7.4, "white")
    footer(ax, "Dockerfile unique · image python:3.12-slim · 3 services · healthchecks · démarrage en une commande")
    fig.savefig(ASSETS / "docker_topology.png", bbox_inches="tight", facecolor=LIGHT)
    plt.close(fig)


def main() -> None:
    arch_hub()
    workflow_graph()
    arch_mcp()
    arch_a2a()
    rag_pipeline()
    docker_topology()
    print("Schémas générés dans", ASSETS)
    for path in sorted(ASSETS.glob("*architecture*.png")) + sorted(ASSETS.glob("workflow*.png")) + sorted(ASSETS.glob("rag*.png")) + sorted(ASSETS.glob("docker*.png")):
        print(" -", path.name, f"{path.stat().st_size/1024:.0f} Ko")


if __name__ == "__main__":
    main()
