# -*- coding: utf-8 -*-
"""Version corrigée des schémas VOLTIS (mise en page)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

from build_diagrams import (
    AMBER, BLUE, BORDER, GREEN, INK, LIGHT, MUTED, NAVY, NAVY2, PURPLE, RED, TEAL,
    arrow, canvas, chip, footer, label, node, rr, title,
)
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"


def arch_hub():
    fig, ax = canvas()
    title(
        ax,
        "Architecture globale",
        "VOLTIS — un hub agentique interopérable pour le secteur électrique",
        "MCP expose les outils, A2A fait collaborer les agents, LangGraph orchestre la réflexion et le RAG garantit des réponses sourcées.",
    )
    node(ax, 0.45, 4.95, 2.45, 1.70, "Utilisateur", ["Question métier", "Région · profil", "Décision"], BLUE, "Client")
    node(ax, 3.25, 4.55, 2.65, 2.40, "Dashboard 8033", ["Streamlit + Plotly", "Formulaires & KPI", "Trace, scores, sources", "Repli local"], NAVY, "UI")
    node(ax, 6.45, 4.05, 3.10, 2.90, "Hub LangGraph", [
        "Planner → intention",
        "RAG hybride BM25+TF-IDF",
        "Outils MCP · A2A",
        "Writer → Critic → Refiner",
        "Sources + score qualité",
    ], AMBER, "Orchestration", head_h=0.40)
    node(ax, 10.15, 5.65, 2.55, 1.35, "Serveur MCP 8100", ["JSON-RPC 2.0 / SSE", "10 outils · schémas", "Découverte auto"], TEAL, "MCP", head_h=0.36)
    node(ax, 10.15, 4.05, 2.55, 1.35, "Orchestrateur A2A", ["8101 · AgentCards", "Délégation //", "correlation_id"], PURPLE, "A2A", head_h=0.36)
    agents = [
        ("Grid Analyst", "8102 · KPI & mix", TEAL, 5.95),
        ("Outage Inspector", "8103 · incidents", RED, 4.95),
        ("Billing Advisor", "8104 · tarifs", AMBER, 3.95),
        ("Forecast Agent", "8105 · pointe", BLUE, 2.95),
    ]
    for name, sub, color, y in agents:
        rr(ax, 13.00, y, 2.50, 0.86, fc="white", ec=BORDER)
        rr(ax, 13.00, y, 0.07, 0.86, fc=color, ec="none")
        label(ax, 13.16, y + 0.58, name, 8.2, INK, "bold")
        label(ax, 13.16, y + 0.29, sub, 7.0, MUTED)
    node(ax, 3.25, 1.35, 5.0, 1.55, "Données & connaissances", [
        "12 documents · 49 chunks · 8 régions",
        "42,3 TWh · 9,25 M clients · 72 incidents",
        "CSV / JSON / Markdown · 100 % synthétique",
    ], GREEN, "Data", head_h=0.34)
    node(ax, 8.75, 1.35, 4.15, 1.55, "Traçabilité & évaluation", [
        "mcp_calls.jsonl · a2a_delegations.jsonl",
        "Scores Reflexion · 5 tâches benchmark",
        "Logs corrélés par correlation_id",
    ], NAVY2, "Observabilité", head_h=0.34)
    node(ax, 13.35, 1.35, 2.15, 1.55, "Docker", ["3 services", "Healthchecks", "Ports exposés"], "#546E7A", "Infra", head_h=0.34)
    arrow(ax, (2.90, 5.80), (3.25, 5.80), BLUE, 2)
    arrow(ax, (5.90, 5.80), (6.45, 5.80), NAVY, 2.2)
    arrow(ax, (9.55, 6.35), (10.15, 6.32), TEAL, 1.8)
    label(ax, 9.63, 6.56, "MCP", 6.8, TEAL, "bold")
    arrow(ax, (9.55, 4.72), (10.15, 4.72), PURPLE, 1.8)
    label(ax, 9.63, 4.94, "A2A", 6.8, PURPLE, "bold")
    ax.plot([12.82, 12.82], [6.38, 3.38], color=PURPLE, lw=1.3, zorder=4, alpha=0.65)
    arrow(ax, (12.70, 4.72), (12.82, 4.72), PURPLE, 1.3)
    for _, _, color, y in agents:
        arrow(ax, (12.82, y + 0.43), (13.00, y + 0.43), color, 1.4)
    arrow(ax, (6.00, 4.55), (5.75, 2.90), GREEN, 1.4, ls="--")
    arrow(ax, (9.10, 4.05), (9.10, 2.90), NAVY2, 1.4, ls="--")
    rr(ax, 0.45, 0.45, 15.0, 0.52, fc="#E8F5F4", ec="#BCE3DE")
    label(ax, 0.65, 0.71, "Protocoles", 8.2, TEAL, "bold")
    labels = ["MCP 2025-06-18 · JSON-RPC 2.0", "A2A 0.3 · AgentCard + message/send", "RAG hybride · BM25 + TF-IDF", "Reflexion · Generate → Critic → Refine"]
    for index, text in enumerate(labels):
        label(ax, 2.35 + index * 3.35, 0.71, text, 7.2, INK)
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
    y = 5.30
    boxes = [
        ("Question", "langage naturel", BLUE, 0.55, 1.65),
        ("Planner", "intention + outils", NAVY, 2.45, 1.75),
        ("Retriever", "BM25 + TF-IDF", TEAL, 4.45, 1.75),
        ("Tools", "MCP · 10 outils", AMBER, 6.45, 1.75),
        ("Writer", "brouillon", PURPLE, 8.45, 1.75),
        ("Critic", "scores 4 axes", RED, 10.70, 1.80),
        ("Finalize", "réponse + confiance", GREEN, 12.90, 2.35),
    ]
    for head, sub, color, x, w in boxes:
        node(ax, x, y, w, 1.35, head, [sub], color, head_h=0.40)
    for start, end in [(2.20, 2.45), (4.20, 4.45), (6.20, 6.45), (8.20, 8.45), (10.20, 10.70)]:
        arrow(ax, (start, y + 0.68), (end, y + 0.68), NAVY, 2)
    node(ax, 10.70, 3.10, 1.80, 1.20, "Refiner", ["sources + plan", "itération +1"], AMBER, head_h=0.38)
    arrow(ax, (11.05, y), (11.05, 4.30), AMBER, 1.6)
    label(ax, 11.12, 4.72, "score < 8,2", 7.0, "#8A6100", "bold")
    arrow(ax, (12.05, 4.30), (12.05, y), AMBER, 1.6)
    label(ax, 12.12, 4.72, "re-critique", 7.0, AMBER, "bold")
    arrow(ax, (12.50, y + 0.68), (12.90, y + 0.68), GREEN, 1.8)
    label(ax, 12.58, y + 0.98, "≥ 8,2", 6.4, GREEN, "bold", ha="right")
    # score panel
    rr(ax, 0.55, 1.00, 6.35, 1.75, fc="white", ec=BORDER)
    label(ax, 0.75, 2.50, "Mesure du gain (5 tâches)", 9.0, NAVY, "bold")
    label(ax, 0.75, 2.13, "Score initial", 7.4, MUTED)
    label(ax, 2.35, 2.13, "6,48 / 10", 10.0, RED, "bold")
    label(ax, 4.05, 2.13, "Score final", 7.4, MUTED)
    label(ax, 5.55, 2.13, "9,40 / 10", 10.0, GREEN, "bold")
    label(ax, 0.75, 1.67, "Gain moyen +2,92 pts · 2 itérations · 8,6 citations/réponse", 7.4, INK)
    rr(ax, 0.75, 1.25, 5.95, 0.20, fc="#EAF0F7", ec="none", radius=0.08)
    rr(ax, 0.75, 1.25, 5.95 * 0.648, 0.20, fc=RED, ec="none", radius=0.08, alpha=0.55)
    rr(ax, 0.75, 1.25, 5.95 * 0.944, 0.20, fc=GREEN, ec="none", radius=0.08, alpha=0.55)
    # criteria panel
    rr(ax, 7.25, 1.00, 8.20, 1.75, fc="#FFFDF4", ec="#EEDB9A")
    label(ax, 7.45, 2.50, "Critères du Critic", 9.0, "#7A5B00", "bold")
    criteria = [("Clarté", "28 %"), ("Exactitude", "34 %"), ("Concision", "14 %"), ("Cohérence", "24 %")]
    for index, (name, weight) in enumerate(criteria):
        x = 7.45 + index * 1.92
        label(ax, x, 2.05, name, 8.0, INK, "bold")
        label(ax, x, 1.73, weight, 9.2, "#8A6100", "bold")
    label(ax, 7.45, 1.33, "Seuil de publication : 8,2/10 · max 2 itérations · sources obligatoires", 7.2, MUTED)
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
    node(ax, 0.45, 4.90, 2.55, 1.45, "Client MCP", ["Dashboard 8033", "LangGraph", "Langflow / IDE"], BLUE, "Client")
    node(ax, 3.45, 3.75, 3.55, 2.20, "Serveur MCP 8100", [
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
        y = 6.60 - (index // 2) * 0.82
        rr(ax, x, y, 2.90, 0.70, fc="white", ec=BORDER)
        label(ax, x + 0.12, y + 0.44, name, 7.3, INK, "bold")
        label(ax, x + 0.12, y + 0.20, desc, 6.6, MUTED)
    node(ax, 7.45, 1.20, 5.95, 1.05, "Données & corpus", [
        "regions.json · load_curve.csv · outages.csv",
        "customers.json · tariffs.json · corpus.json (12 docs)",
    ], GREEN, "Data", head_h=0.34)
    node(ax, 13.75, 3.75, 1.80, 2.20, "Traçabilité", ["appels", "arguments", "latence", "statut", "logs JSONL"], MUTED, "Audit")
    arrow(ax, (3.00, 5.85), (3.45, 5.85), NAVY, 2)
    arrow(ax, (7.00, 6.35), (7.45, 6.55), TEAL, 1.6, ls="--")
    ax.plot([5.22, 5.22], [3.75, 2.15], color=GREEN, lw=1.4, ls="--", zorder=4)
    arrow(ax, (5.22, 2.15), (7.42, 2.15), GREEN, 1.4, ls="--")
    arrow(ax, (13.40, 3.30), (13.75, 4.10), MUTED, 1.2, ls=":")
    label(ax, 5.32, 3.48, "resources", 6.4, GREEN, "bold")
    rr(ax, 7.45, 0.55, 5.95, 0.38, fc="#FFF7E0", ec="#EEDB9A", radius=0.08)
    label(ax, 7.62, 0.74, "Chaque appel est journalisé avec ses arguments, sa latence et son statut.", 6.8, "#7A5B00")
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
    node(ax, 0.45, 4.60, 2.30, 1.75, "Question", ["objectif métier", "région / priorité", "dashboard"], BLUE, "Input")
    node(ax, 3.20, 4.20, 2.75, 2.05, "Orchestrateur 8101", [
        "GET /agents (discovery)",
        "Sélection par capacités",
        "Délégation parallèle",
        "Agrégation des artifacts",
        "correlation_id unique",
    ], PURPLE, "A2A", head_h=0.40)
    agents = [
        ("Grid Analyst", "8102", ["KPI · mix · consommation"], TEAL, 6.10),
        ("Outage Inspector", "8103", ["incidents · SAIDI/SAIFI"], RED, 4.95),
        ("Billing Advisor", "8104", ["factures · économies"], AMBER, 3.80),
        ("Forecast Agent", "8105", ["pointe · réserve"], BLUE, 2.65),
    ]
    for name, port, skills, color, y in agents:
        node(ax, 6.65, y, 3.35, 0.95, name, [" · ".join(skills), f"AgentCard · port {port}"], color, port, head_h=0.32)
    node(ax, 10.45, 4.35, 2.45, 1.75, "Agrégation", ["réponse unique", "4 artifacts", "sources dédupliquées"], GREEN, "Output", head_h=0.36)
    node(ax, 10.45, 2.35, 2.45, 1.25, "Dashboard 8033", ["cartes agents", "timeline", "logs A2A"], NAVY, "UI", head_h=0.36)
    node(ax, 13.35, 4.15, 2.15, 2.15, "Traçabilité", ["correlation_id", "latence par agent", "statut", "JSONL"], MUTED, "Audit", head_h=0.36)
    arrow(ax, (2.75, 5.45), (3.20, 5.45), NAVY, 2)
    # bus discovery
    ax.plot([6.25, 6.25], [6.57, 3.12], color=PURPLE, lw=1.3, zorder=4, alpha=0.55)
    arrow(ax, (5.95, 5.45), (6.25, 5.45), PURPLE, 1.3)
    for _, _, _, color, y in agents:
        arrow(ax, (6.25, y + 0.47), (6.65, y + 0.47), color, 1.5)
    # bus aggregation
    ax.plot([10.15, 10.15], [6.57, 3.12], color=GREEN, lw=1.3, zorder=4, alpha=0.55)
    for _, _, _, color, y in agents:
        arrow(ax, (10.00, y + 0.47), (10.15, y + 0.47), color, 1.5)
    arrow(ax, (10.15, 5.45), (10.45, 5.45), GREEN, 1.8)
    arrow(ax, (11.67, 4.35), (11.67, 3.60), NAVY, 1.6)
    arrow(ax, (12.90, 5.10), (13.35, 5.10), MUTED, 1.3, ls=":")
    label(ax, 5.55, 6.98, "discover", 6.4, PURPLE, "bold", ha="right")
    label(ax, 10.05, 6.98, "aggregate", 6.4, GREEN, "bold", ha="right")
    # trace band
    rr(ax, 0.45, 0.55, 15.0, 0.72, fc="#F8FAFD", ec=BORDER, radius=0.10)
    label(ax, 0.65, 1.05, "Trace exemple", 7.8, NAVY, "bold")
    label(ax, 2.20, 1.05, "A2A-8F3C21D4", 7.4, PURPLE, "bold")
    label(ax, 4.35, 1.05, "09:15:01 discovery → 09:15:02 delegation x3 → 09:15:04 aggregation", 7.0, MUTED)
    label(ax, 0.65, 0.79, "Chaque ligne contient : correlation_id · agent_id · statut · latence · task · mode (HTTP ou repli local).", 6.7, MUTED)
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
    y = 5.25
    for head, lines, color, x, w in steps:
        node(ax, x, y, w, 1.35, head, lines, color, head_h=0.38)
    for start, end in [(2.60, 3.00), (5.05, 5.45), (7.55, 7.95), (10.00, 10.40), (12.45, 12.85)]:
        arrow(ax, (start, y + 0.68), (end, y + 0.68), NAVY, 2)
    arrow(ax, (8.97, y), (8.97, 4.45), AMBER, 1.5)
    arrow(ax, (8.97, 4.45), (6.50, 4.45), AMBER, 1.5)
    arrow(ax, (6.50, 4.45), (6.50, y), AMBER, 1.5)
    label(ax, 7.20, 4.28, "reformuler (max 2)", 6.8, "#8A6100", "bold")
    rr(ax, 0.55, 1.75, 5.30, 1.95, fc="white", ec=BORDER)
    label(ax, 0.75, 3.42, "Corpus indexé", 8.8, NAVY, "bold")
    docs = ["12 documents · 49 chunks", "Exploitation · maintenance · commercial", "Réglementation · cybersécurité · sécurité", "Chaque chunk = doc + version + article"]
    for index, line in enumerate(docs):
        label(ax, 0.75, 3.05 - index * 0.30, "· " + line, 7.2, MUTED)
    rr(ax, 6.15, 1.75, 4.55, 1.95, fc="#F4FBF9", ec="#BFE5DB")
    label(ax, 6.35, 3.42, "Réponse sourcée", 8.8, GREEN, "bold")
    label(ax, 6.35, 3.05, "« La marge de réserve minimale est de 8 %… »", 7.4, INK, style="italic")
    label(ax, 6.35, 2.72, "[1] DOC-PREVISION · v2.9 · article 3", 7.0, GREEN, "bold")
    label(ax, 6.35, 2.40, "8,6 citations par réponse · 0 hallucination détectée", 6.8, MUTED)
    rr(ax, 11.00, 1.75, 4.45, 1.95, fc="#FFF7F6", ec="#F0C9C4")
    label(ax, 11.20, 3.42, "Garde-fous", 8.8, RED, "bold")
    guards = ["Seuil de suffisance 0,55", "Sources obligatoires [n]", "Score Reflexion ≥ 8,2", "Repli local si service indisponible"]
    for index, line in enumerate(guards):
        label(ax, 11.20, 3.05 - index * 0.30, "· " + line, 7.1, MUTED)
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
    rr(ax, 0.55, 1.05, 14.90, 5.65, fc="#EEF3F9", ec="#C9D8E8", radius=0.15)
    label(ax, 0.80, 6.48, "Hôte Docker", 9.0, NAVY, "bold")
    node(ax, 1.00, 4.55, 4.30, 1.70, "dashboard", [
        "python main.py dashboard",
        "Streamlit · port 8033",
        "depends_on: mcp, a2a",
        "healthcheck HTTP /",
    ], NAVY, "8033", head_h=0.38)
    node(ax, 5.85, 4.55, 4.30, 1.70, "mcp", [
        "python main.py mcp",
        "FastAPI · port 8100",
        "10 outils · JSON-RPC",
        "healthcheck /api/health",
    ], TEAL, "8100", head_h=0.38)
    node(ax, 10.70, 4.55, 4.30, 1.70, "a2a", [
        "python main.py a2a",
        "orchestrateur 8101",
        "agents 8102 → 8105",
        "healthcheck /health",
    ], PURPLE, "8101-8105", head_h=0.38)
    rr(ax, 1.00, 2.35, 13.95, 1.35, fc="white", ec=BORDER)
    label(ax, 1.20, 3.42, "Volume partagé (lecture seule)", 8.6, GREEN, "bold")
    label(ax, 1.20, 3.08, "data/ · json/ · docs/ · assets/ · a2a/agent_cards/", 7.2, MUTED)
    label(ax, 1.20, 2.76, "Mêmes données synthétiques pour les 3 services · aucune donnée personnelle", 7.0, MUTED)
    label(ax, 11.30, 3.08, "Réseau bridge dédié", 7.4, RED, "bold")
    label(ax, 11.30, 2.76, "CORS · Bearer en production", 7.0, MUTED)
    ax.plot([10.95, 10.95], [2.50, 3.55], color=BORDER, lw=1.0, zorder=3)
    info = [("restart: unless-stopped", 2.05), ("healthcheck: 30 s", 1.75), (".env / secrets", 1.45), ("logs JSONL", 1.30)]
    x = 1.00
    for text, width in info:
        chip(ax, x, 1.42, width, text, NAVY2, 6.4)
        x += width + 0.18
    arrow(ax, (5.30, 5.40), (5.85, 5.40), TEAL, 2)
    arrow(ax, (10.15, 5.40), (10.70, 5.40), PURPLE, 2)
    label(ax, 5.42, 5.66, "HTTP", 6.8, TEAL, "bold")
    label(ax, 10.27, 5.66, "HTTP", 6.8, PURPLE, "bold")
    arrow(ax, (3.10, 4.55), (3.10, 3.70), GREEN, 1.3, ls="--")
    arrow(ax, (8.00, 4.55), (8.00, 3.70), GREEN, 1.3, ls="--")
    arrow(ax, (12.85, 4.55), (12.85, 3.70), GREEN, 1.3, ls="--")
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
    print("Schémas corrigés générés dans", ASSETS)


if __name__ == "__main__":
    main()
