# -*- coding: utf-8 -*-
"""Génère la présentation finale VOLTIS (PPTX) et son PDF."""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from pptx.enum.text import PP_ALIGN  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402

from pptx_helpers import (  # noqa: E402
    AMBER, AMBER_LIGHT, ASSETS, BG, BLUE, BORDER, GREEN, INK, LIGHT, MUTED,
    NAVY, NAVY2, NAVY3, PURPLE, RED, SOFT_GOLD, SOFT_GREEN, SOFT_RED, TEAL,
    WHITE, blank, card, code, cover, footer, header, image, line, new_deck,
    notes, paragraphs, pill, rect, rich, section, stat, table, txt,
)
from shared import electricity_core as core  # noqa: E402

PRESENTATION = ROOT / "presentation"
PRESENTATION.mkdir(exist_ok=True)
OUT = PRESENTATION / "Presentation_Finale_VOLTIS.pptx"
PDF = PRESENTATION / "Presentation_Finale_VOLTIS.pdf"
TOTAL = 26


def load_bench() -> dict:
    return json.loads((ROOT / "data" / "benchmarks.json").read_text(encoding="utf-8"))


def fmt(value: float, decimals: int = 0) -> str:
    if decimals == 0:
        return f"{value:,.0f}".replace(",", " ")
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")


def build() -> Path:
    kpis = core.national_kpis()
    mix = core.production_mix()
    bench = load_bench()
    avg = bench["averages"]
    prs = new_deck()

    # ------------------------------------------------------------------ #
    # 1. Couverture
    # ------------------------------------------------------------------ #
    slide = cover(
        prs,
        "Mini-projet final · Agentic AI for the Electricity Sector",
        "VOLTIS — le hub agentique du réseau électrique",
        "MCP, A2A, RAG agentique et LangGraph : une plateforme unique pour l'exploitation, "
        "la maintenance et la relation client.",
        "Version 1.0.0 · 12 novembre 2026 · Direction Digitale & Exploitation",
        ["MCP", "A2A", "RAG", "Reflexion"],
    )
    notes(slide, "Bonjour. VOLTIS est une plateforme agentique pour le secteur électrique. Elle relie les données du réseau, "
                 "les procédures internes et quatre agents spécialisés. Le dashboard est accessible sur localhost:8033.")

    # ------------------------------------------------------------------ #
    # 2. Sommaire
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Agenda", "Ce que nous allons démontrer", "")
    items = [
        ("01", "Contexte & problématique", "Pourquoi les dashboards ne suffisent plus."),
        ("02", "Objectifs & critères", "Les sept critères de validation du projet."),
        ("03", "Architecture du hub", "MCP, A2A, RAG et LangGraph en six couches."),
        ("04", "Données & RAG", "12 documents, 49 chunks, retrieval hybride."),
        ("05", "MCP", "10 outils standards et traçables."),
        ("06", "A2A", "4 agents, AgentCards et délégation parallèle."),
        ("07", "Dashboard", "Menu, formulaires, graphiques et statistiques."),
        ("08", "Résultats & perspectives", "Benchmark Reflexion et prochaines étapes."),
    ]
    for index, (number, title, subtitle) in enumerate(items):
        column = index % 2
        row = index // 2
        x = 0.65 + column * 6.25
        y = 1.85 + row * 1.18
        rect(slide, x, y, 0.46, 0.46, AMBER if index % 2 == 0 else TEAL, shape=1)
        txt(slide, x, y + 0.08, 0.46, 0.3, number, 10, NAVY, True, align=PP_ALIGN.CENTER)
        txt(slide, x + 0.62, y - 0.02, 4.9, 0.3, title, 13.5, NAVY, True)
        txt(slide, x + 0.62, y + 0.28, 5.0, 0.3, subtitle, 9.5, MUTED)
    rect(slide, 0.65, 6.12, 12.0, 0.52, NAVY, radius=0.10, shape=5)
    txt(slide, 0.88, 6.27, 11.55, 0.24, "Livrables : dashboard 8033 · DOCX/PDF · PPTX · 6 manifests JSON · 5 AgentCards",
        9.2, WHITE, True)
    footer(slide, 2, TOTAL)
    notes(slide, "Le parcours suit la logique du projet : contexte, architecture, briques techniques, démonstration, résultats.")

    # ------------------------------------------------------------------ #
    # 3. Contexte
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Contexte", "Le réseau électrique sous tension", "4 PRESSIONS")
    stats = [
        (f"{kpis['consumption_gwh']/1000:.1f} TWh".replace(".", ","), "consommation annuelle", "8 régions", NAVY),
        (f"{kpis['peak_mw']:,.0f} MW".replace(",", " "), "pointe nationale", "marge 8 %", AMBER),
        (f"{kpis['renewable_share_pct']:.1f} %".replace(".", ","), "part renouvelable", "intermittence", TEAL),
        (f"{kpis['saidi_min']:.0f} min", "SAIDI moyen", "cible < 300", BLUE),
    ]
    for index, (value, label, sub, accent) in enumerate(stats):
        stat(slide, 0.55 + index * 3.12, 1.72, 2.92, 1.22, value, label, accent, sub, value_size=24)
    pressures = [
        ("Demande", "Urbanisation, climatisation, électrification des usages.", "▲", BLUE),
        ("Intermittence", "Le solaire s'efface à 17 h, au moment de la pointe.", "☀", AMBER),
        ("Actifs vieillissants", "Transformateurs et départs en maintenance conditionnelle.", "⚙", TEAL),
        ("Exigence client", "Comprendre sa facture, signaler, être compensé.", "◉", PURPLE),
    ]
    for index, (title, body, icon, accent) in enumerate(pressures):
        card(slide, 0.55 + index * 3.12, 3.22, 2.92, 1.72, title, body, accent, icon, body_size=9.2, title_size=12.5)
    rect(slide, 0.55, 5.28, 12.22, 0.98, NAVY, radius=0.12, shape=5)
    txt(slide, 0.85, 5.47, 11.6, 0.3, "Le tableau de bord décrit la situation. L'agent doit la comprendre, la expliquer et recommander.",
        13.5, WHITE, True)
    txt(slide, 0.85, 5.82, 11.6, 0.25, "VOLTIS relie la donnée, la procédure et la décision dans un même flux traçable.",
        9.5, RGBColor(0xC9, 0xD8, 0xE8) if False else WHITE)
    footer(slide, 3, TOTAL)
    notes(slide, "Quatre pressions : demande, intermittence, actifs vieillissants, exigence client. Le constat est que les outils descriptifs ne suffisent plus.")

    # ------------------------------------------------------------------ #
    # 4. Problématique
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Problématique", "Pourquoi les dashboards ne suffisent plus", "5 LIMITES")
    limits = [
        ("Silos d'outils", "Chaque API a son format, son auth, son endpoint.", "Intégration coûteuse."),
        ("RAG simple", "Une recherche, pas de reformulation ni de vérification.", "Réponse incomplète."),
        ("Mono-agent", "Un agent ne couvre ni réseau, ni facture, ni prévision.", "Escalade manuelle."),
        ("Réponse non sourcée", "Le LLM peut inventer un chiffre ou une règle.", "Décision non auditable."),
    ]
    for index, (title, body, consequence) in enumerate(limits):
        x = 0.55 + index * 3.12
        rect(slide, x, 1.78, 2.92, 3.25, WHITE, line=BORDER, radius=0.06, shape=5)
        rect(slide, x, 1.78, 2.92, 0.08, RED)
        txt(slide, x + 0.18, 2.02, 2.55, 0.35, f"0{index + 1}", 11, RED, True)
        txt(slide, x + 0.18, 2.38, 2.55, 0.55, title, 13, NAVY, True, line_spacing=0.95)
        txt(slide, x + 0.18, 3.02, 2.55, 1.0, body, 9.3, MUTED, line_spacing=1.08)
        rect(slide, x + 0.18, 4.22, 2.55, 0.52, SOFT_RED, radius=0.08, shape=5)
        txt(slide, x + 0.28, 4.38, 2.35, 0.22, consequence, 8.5, RGBColor(0xB2, 0x3B, 0x2E), True)
    rect(slide, 0.55, 5.35, 12.22, 1.0, SOFT_GOLD, line=RGBColor(0xEE, 0xDB, 0x9A), radius=0.12, shape=5)
    txt(slide, 0.85, 5.55, 11.6, 0.3, "Le vrai besoin : un hub qui planifie, cite ses sources, critique sa réponse et fait collaborer des spécialistes.",
        12.5, RGBColor(0x7A, 0x5B, 0x00), True)
    txt(slide, 0.85, 5.92, 11.6, 0.25, "C'est exactement le rôle de MCP + A2A + RAG + LangGraph.",
        9.5, MUTED)
    footer(slide, 4, TOTAL)
    notes(slide, "Cinq limites : silos, RAG simple, mono-agent, réponses non sourcées, absence de mesure. VOLTIS adresse chacune.")

    # ------------------------------------------------------------------ #
    # 5. Vision
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Vision", "Un hub, trois protocoles, quatre agents", "CIBLE")
    rect(slide, 4.65, 2.55, 4.05, 2.25, NAVY, radius=0.10, shape=5)
    txt(slide, 4.85, 2.75, 3.65, 0.35, "VOLTIS HUB", 15, AMBER, True, align=PP_ALIGN.CENTER)
    txt(slide, 4.85, 3.15, 3.65, 0.9, "LangGraph\nPlanner · Critic · Refiner", 11, WHITE, align=PP_ALIGN.CENTER, line_spacing=1.25)
    txt(slide, 4.85, 4.10, 3.65, 0.3, "localhost:8033", 9, RGBColor(0x9F, 0xB8, 0xD0), align=PP_ALIGN.CENTER)
    blocks = [
        (0.55, 1.78, "MCP 8100", "10 outils\nJSON-RPC 2.0", TEAL),
        (0.55, 4.55, "RAG hybride", "12 documents\nBM25 + TF-IDF", GREEN),
        (9.70, 1.78, "A2A 8101", "4 agents\nAgentCards", PURPLE),
        (9.70, 4.55, "Dashboard 8033", "menu · formulaires\ngraphiques", BLUE),
    ]
    for x, y, title, body, color in blocks:
        rect(slide, x, y, 2.95, 1.55, WHITE, line=BORDER, radius=0.08, shape=5)
        rect(slide, x, y, 2.95, 0.08, color)
        txt(slide, x + 0.15, y + 0.16, 2.65, 0.28, title, 12, NAVY, True)
        txt(slide, x + 0.15, y + 0.50, 2.65, 0.7, body, 8.8, MUTED, line_spacing=1.1)
    line(slide, 3.50, 3.05, 4.65, 3.05, TEAL, 2.0)
    line(slide, 3.50, 4.30, 4.65, 4.30, GREEN, 2.0)
    line(slide, 8.70, 3.05, 9.70, 3.05, PURPLE, 2.0)
    line(slide, 8.70, 4.30, 9.70, 4.30, BLUE, 2.0)
    pill(slide, 3.55, 2.78, 0.9, 0.24, "outils", TEAL, WHITE, 7)
    pill(slide, 3.55, 4.03, 0.9, 0.24, "sources", GREEN, WHITE, 7)
    pill(slide, 8.80, 2.78, 0.9, 0.24, "agents", PURPLE, WHITE, 7)
    pill(slide, 8.80, 4.03, 0.9, 0.24, "UI", BLUE, WHITE, 7)
    rect(slide, 0.55, 6.25, 12.22, 0.52, SOFT_GREEN, radius=0.10, shape=5)
    txt(slide, 0.75, 6.40, 11.8, 0.25, "Un seul point d'entrée · trois protocoles séparés · traçabilité de bout en bout",
        10, GREEN, True)
    footer(slide, 5, TOTAL)
    notes(slide, "Le hub centralise l'orchestration. MCP expose les outils, A2A les agents, le RAG les documents, le dashboard l'expérience.")

    # ------------------------------------------------------------------ #
    # 6. Architecture
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Architecture", "Le hub interopérable en six couches", "SCHÉMA")
    if (ASSETS / "architecture_hub.png").exists():
        image(slide, ASSETS / "architecture_hub.png", 0.55, 1.62, w=9.55)
    card(slide, 10.45, 1.68, 2.35, 1.22, "Expérience", "Dashboard Streamlit 8033.", BLUE, body_size=8.5, title_size=11)
    card(slide, 10.45, 3.05, 2.35, 1.22, "Orchestration", "LangGraph + A2A 8101.", AMBER, body_size=8.5, title_size=11)
    card(slide, 10.45, 4.42, 2.35, 1.22, "Données", "CSV/JSON + corpus.", GREEN, body_size=8.5, title_size=11)
    card(slide, 10.45, 5.79, 2.35, 1.05, "Infra", "Docker Compose.", NAVY2, body_size=8.5, title_size=11)
    footer(slide, 6, TOTAL)
    notes(slide, "Le schéma complet montre les couches, les ports et les flux. On retient la séparation entre outils, agents et connaissance.")

    # ------------------------------------------------------------------ #
    # 7. Données
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Données", "Un jeu de données synthétique, calibré et reproductible", "8 RÉGIONS")
    regions = sorted(core.regions(), key=lambda row: row["consumption_gwh"], reverse=True)
    rows = [
        [row["name"], fmt(row["consumption_gwh"]), fmt(row["peak_mw"]), f"{row['renewable_share_pct']:.0f} %", fmt(row["saidi_min"])]
        for row in regions
    ]
    table(slide, 0.55, 1.72, 8.15, 3.95, ["Région", "GWh/an", "Pointe MW", "% renouv.", "SAIDI"], rows,
          col_widths=[3.1, 1.25, 1.25, 1.15, 1.05], font_size=8.6)
    stat(slide, 9.0, 1.72, 1.78, 1.15, "72", "incidents", AMBER, "90 jours", 24)
    stat(slide, 10.95, 1.72, 1.78, 1.15, "24", "clients", TEAL, "suivis", 24)
    stat(slide, 9.0, 3.05, 1.78, 1.15, "49", "chunks", GREEN, "12 docs", 24)
    stat(slide, 10.95, 3.05, 1.78, 1.15, "8", "régions", BLUE, "national", 24)
    rect(slide, 9.0, 4.38, 3.73, 1.25, SOFT_GOLD, line=RGBColor(0xEE, 0xDB, 0x9A), radius=0.08, shape=5)
    txt(slide, 9.18, 4.55, 3.4, 0.25, "100 % synthétique", 10, RGBColor(0x7A, 0x5B, 0x00), True)
    txt(slide, 9.18, 4.85, 3.4, 0.6, "Graine fixe 20261112 · aucun client réel · reproductible.", 8.3, MUTED)
    txt(slide, 0.55, 5.92, 12.2, 0.3, "Le jeu couvre la consommation, la pointe, les pertes, la continuité, les tarifs et les incidents.",
        10, MUTED)
    footer(slide, 7, TOTAL)
    notes(slide, "Les données sont synthétiques mais calibrées : 42,3 TWh, 9,25 millions de clients, 72 incidents. Elles suffisent à démontrer les mécanismes.")

    # ------------------------------------------------------------------ #
    # 8. LangGraph
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Orchestration", "LangGraph : un graphe d'états explicite", "7 NŒUDS")
    if (ASSETS / "workflow_langgraph.png").exists():
        image(slide, ASSETS / "workflow_langgraph.png", 0.55, 1.65, w=9.45)
    paragraphs(slide, 10.30, 1.85, 2.55, 3.6, [
        ("Planner", " choisit l'intention et les outils."),
        ("Retriever", " cherche et filtre les sources."),
        ("Tools", " appelle MCP et journalise."),
        ("Writer", " rédige, cite et structure."),
        ("Critic", " note 4 critères pondérés."),
        ("Refiner", " réécrit tant que score < seuil."),
        ("Finalize", " ajoute sources et confiance."),
    ], size=9.4, space_after=6)
    rect(slide, 10.30, 5.55, 2.45, 0.78, SOFT_GREEN, radius=0.08, shape=5)
    txt(slide, 10.45, 5.70, 2.15, 0.22, "État typé", 9.5, GREEN, True)
    txt(slide, 10.45, 5.95, 2.15, 0.25, "sérialisable et testable", 7.8, MUTED)
    footer(slide, 8, TOTAL)
    notes(slide, "Le graphe est explicite : chaque nœud a une responsabilité, l'état est typé, la boucle est conditionnelle.")

    # ------------------------------------------------------------------ #
    # 9. Reflexion
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Auto-amélioration", "Reflexion : Generate → Critic → Refine", "QUALITÉ")
    steps = [
        ("1", "Generate", "Le Writer produit un brouillon structuré à partir des sources et des outils.", BLUE),
        ("2", "Critic", "Un score sur 10 : clarté 28 %, exactitude 34 %, concision 14 %, cohérence 24 %.", AMBER),
        ("3", "Refine", "Le Refiner ajoute les sources, le plan d'action, les limites et les indicateurs.", GREEN),
    ]
    for index, (number, title, body, color) in enumerate(steps):
        x = 0.55 + index * 4.12
        rect(slide, x, 1.72, 3.85, 1.95, WHITE, line=BORDER, radius=0.08, shape=5)
        rect(slide, x, 1.72, 3.85, 0.08, color)
        rect(slide, x + 0.18, 1.94, 0.48, 0.48, color, shape=1)
        txt(slide, x + 0.18, 2.03, 0.48, 0.3, number, 12, WHITE, True, align=PP_ALIGN.CENTER)
        txt(slide, x + 0.78, 1.94, 2.7, 0.4, title, 15, NAVY, True)
        txt(slide, x + 0.20, 2.58, 3.45, 0.95, body, 9.2, MUTED, line_spacing=1.08)
    for index in range(2):
        txt(slide, 4.35 + index * 4.12, 2.42, 0.42, 0.4, "→", 22, AMBER, True, align=PP_ALIGN.CENTER)
    rect(slide, 0.55, 4.00, 5.9, 1.45, WHITE, line=BORDER, radius=0.08, shape=5)
    txt(slide, 0.78, 4.18, 3.8, 0.28, "Gain mesuré sur 5 tâches", 10, NAVY, True)
    txt(slide, 0.78, 4.55, 1.7, 0.35, f"{avg['initial']}/10".replace(".", ","), 22, RED, True)
    txt(slide, 1.85, 4.62, 0.5, 0.25, "→", 14, MUTED, True)
    txt(slide, 2.25, 4.55, 1.7, 0.35, f"{avg['final']}/10".replace(".", ","), 22, GREEN, True)
    txt(slide, 3.55, 4.62, 2.65, 0.25, f"gain +{avg['gain']} pts · {avg['citations']} citations", 8.8, MUTED)
    rect(slide, 6.70, 4.00, 6.05, 1.45, SOFT_GOLD, line=RGBColor(0xEE, 0xDB, 0x9A), radius=0.08, shape=5)
    txt(slide, 6.92, 4.18, 5.6, 0.28, "Condition d'arrêt", 10, RGBColor(0x7A, 0x5B, 0x00), True)
    txt(slide, 6.92, 4.50, 5.6, 0.65, "Score ≥ 8,2 ou 2 itérations maximum. Le benchmark force 2 itérations pour mesurer le gain complet.",
        8.8, MUTED, line_spacing=1.1)
    rect(slide, 0.55, 5.75, 12.20, 0.62, NAVY, radius=0.10, shape=5)
    txt(slide, 0.80, 5.92, 11.7, 0.25, "Chaque itération doit apporter une amélioration mesurable — sinon le Refiner ne sert à rien.",
        11, WHITE, True)
    footer(slide, 9, TOTAL)
    notes(slide, "La boucle Reflexion est la signature du projet : générer, critiquer, raffiner, et mesurer le gain à chaque étape.")

    # ------------------------------------------------------------------ #
    # 10. Agentic RAG
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Connaissance", "Agentic RAG : planifier, vérifier, citer", "49 CHUNKS")
    if (ASSETS / "rag_pipeline.png").exists():
        image(slide, ASSETS / "rag_pipeline.png", 0.55, 1.65, w=9.50)
    paragraphs(slide, 10.30, 1.85, 2.55, 3.8, [
        ("Planifier", " la requête et choisir top-k."),
        ("Retriever", " BM25 + TF-IDF, filtre métier."),
        ("Vérifier", " la suffisance (seuil 0,55)."),
        ("Reformuler", " jusqu'à 2 fois si besoin."),
        ("Citer", " chaque affirmation avec [n]."),
        ("Critiquer", " avant publication."),
    ], size=9.2, space_after=6)
    rect(slide, 10.30, 4.72, 2.45, 0.75, SOFT_GREEN, radius=0.08, shape=5)
    txt(slide, 10.45, 4.86, 2.15, 0.22, "0 hallucination", 9.5, GREEN, True)
    txt(slide, 10.45, 5.10, 2.15, 0.22, "détectée sur le benchmark", 7.6, MUTED)
    footer(slide, 10, TOTAL)
    notes(slide, "Le RAG n'est pas une simple recherche : l'agent planifie, vérifie la suffisance, reformule et cite.")

    # ------------------------------------------------------------------ #
    # 11. Retrieval hybride
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Retrieval", "BM25 + TF-IDF : le meilleur des deux mondes", "HYBRIDE")
    cards = [
        ("BM25", "Correspondance lexicale exacte. Idéal pour SAIDI, consignation, tranche.", "k1 = 1,5 · b = 0,75", TEAL),
        ("TF-IDF cosinus", "Proximité sémantique de surface. Gère les reformulations.", "vecteurs creux · stopwords FR", BLUE),
        ("Fusion", "Score hybride + bonus de titre + bonus de phrase exacte.", "0,66 × BM25 + 0,86 × TF-IDF", AMBER),
    ]
    for index, (title, body, meta, color) in enumerate(cards):
        card(slide, 0.55 + index * 4.12, 1.72, 3.85, 1.92, title, body, color, body_size=9.3, title_size=14)
        txt(slide, 0.77 + index * 4.12, 3.25, 3.4, 0.22, meta, 8.2, color, True)
    sample = core.search_documents("procédure de délestage en cas de pointe", 4)
    rows = [
        [item["doc_id"], f"v{item['version']}", f"art. {item['article']}", f"{item['relevance_pct']:.0f} %"]
        for item in sample["results"]
    ]
    table(slide, 0.55, 3.98, 7.55, 2.2, ["Document", "Version", "Article", "Pertinence"], rows,
          col_widths=[3.5, 1.2, 1.1, 1.3], font_size=9)
    rect(slide, 8.35, 3.98, 4.42, 2.2, WHITE, line=BORDER, radius=0.08, shape=5)
    txt(slide, 8.55, 4.15, 4.0, 0.25, "Exemple de requête", 9.5, NAVY, True)
    txt(slide, 8.55, 4.45, 4.0, 0.55, "« procédure de délestage en cas de pointe »", 10.5, NAVY, False, line_spacing=1.1)
    txt(slide, 8.55, 5.10, 4.0, 0.7, "Le filtre métier impose au moins un extrait de la procédure d'incidents et de la procédure de délestage.",
        8.3, MUTED, line_spacing=1.1)
    txt(slide, 0.55, 6.45, 12.2, 0.25, "Chaque chunk = un article versionné · citation DOC-XX · vX.Y · article N.", 9, MUTED)
    footer(slide, 11, TOTAL)
    notes(slide, "BM25 capte les termes exacts, TF-IDF les reformulations. La fusion et le filtre métier évitent les sources hors sujet.")

    # ------------------------------------------------------------------ #
    # 12. MCP concept
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "MCP", "Un langage commun pour les outils", "MCP")
    rect(slide, 0.55, 1.75, 5.65, 3.55, WHITE, line=BORDER, radius=0.08, shape=5)
    txt(slide, 0.78, 1.92, 5.2, 0.28, "AVANT MCP", 9, RED, True, char_spacing=1.5)
    txt(slide, 0.78, 2.25, 5.2, 0.3, "Chaque agent se connecte avec sa propre méthode.", 9.5, MUTED)
    for index, (label, color) in enumerate([("API REST", BLUE), ("Connecteur", TEAL), ("Format", AMBER), ("Auth", PURPLE)]):
        pill(slide, 0.80 + (index % 2) * 2.55, 2.85 + (index // 2) * 0.85, 2.25, 0.55, label, color, WHITE, 8.5)
    rect(slide, 6.55, 1.75, 6.25, 3.55, NAVY, radius=0.08, shape=5)
    txt(slide, 6.78, 1.92, 5.7, 0.28, "APRÈS MCP", 9, AMBER, True, char_spacing=1.5)
    txt(slide, 6.78, 2.25, 5.7, 0.3, "Un serveur expose ses outils, l'agent les découvre.", 9.5, RGBColor(0xC9, 0xD8, 0xE8))
    rect(slide, 6.95, 2.78, 2.2, 0.9, TEAL, radius=0.08, shape=5)
    txt(slide, 7.03, 2.92, 2.04, 0.25, "MCP SERVER", 9, WHITE, True, align=PP_ALIGN.CENTER)
    txt(slide, 7.03, 3.20, 2.04, 0.25, "10 outils", 8, WHITE, align=PP_ALIGN.CENTER)
    for index, label in enumerate(["Search", "Weather", "Database", "Email"]):
        pill(slide, 9.55 + (index % 2) * 1.45, 2.72 + (index // 2) * 0.62, 1.25, 0.42, label, NAVY3, WHITE, 7.2)
    txt(slide, 6.95, 4.15, 5.4, 0.7, "L'agent choisit le bon outil selon la demande, sans connaître l'implémentation.",
        9.2, RGBColor(0xC9, 0xD8, 0xE8), line_spacing=1.1)
    for index, (title, body, color) in enumerate([
        ("Tools", "Actions exécutables.", TEAL),
        ("Resources", "Données consultables.", GREEN),
        ("Prompts", "Instructions réutilisables.", AMBER),
    ]):
        x = 0.55 + index * 4.12
        rect(slide, x, 5.55, 3.85, 0.78, WHITE, line=BORDER, radius=0.08, shape=5)
        rect(slide, x, 5.55, 0.07, 0.78, color)
        txt(slide, x + 0.20, 5.68, 3.4, 0.24, title, 10.5, NAVY, True)
        txt(slide, x + 0.20, 5.96, 3.4, 0.22, body, 8.2, MUTED)
    footer(slide, 12, TOTAL)
    notes(slide, "MCP remplace les intégrations spécifiques par un standard : tools, resources, prompts. Un serveur, dix outils, zéro couplage fort.")

    # ------------------------------------------------------------------ #
    # 13. MCP tools
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "MCP", "Dix outils exposés, un seul schéma", "10 OUTILS")
    tools = core.list_tools()
    for index, tool in enumerate(tools):
        x = 0.55 + (index % 5) * 2.45
        y = 1.78 + (index // 5) * 2.25
        rect(slide, x, y, 2.28, 1.95, WHITE, line=BORDER, radius=0.07, shape=5)
        txt(slide, x + 0.12, y + 0.10, 2.0, 0.2, tool["category"].upper(), 6.5, TEAL, True, char_spacing=1)
        txt(slide, x + 0.12, y + 0.33, 2.05, 0.45, tool["name"], 7.6, NAVY, True, line_spacing=0.95)
        txt(slide, x + 0.12, y + 0.86, 2.02, 0.95, tool["description"], 6.4, MUTED, line_spacing=1.05)
    rect(slide, 0.55, 6.35, 12.22, 0.48, NAVY, radius=0.10, shape=5)
    txt(slide, 0.75, 6.48, 11.8, 0.22, "JSON Schema · découverte automatique · arguments validés · latence journalisée",
        9.5, WHITE, True)
    footer(slide, 13, TOTAL)
    notes(slide, "Dix outils couvrent KPI, régions, incidents, prévision, facturation, RAG, économies et qualité. Chacun a un schéma JSON.")

    # ------------------------------------------------------------------ #
    # 14. MCP demo
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "MCP", "Un appel, une trace, une réponse structurée", "DÉMO")
    code(slide, 0.55, 1.75, 6.0, 3.35, """POST http://127.0.0.1:8100/mcp
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "forecast_load",
    "arguments": {
      "region_code": "CAS",
      "horizon_h": 24,
      "temperature_delta": 5
    }
  }
}""", size=8.2, lang="json")
    code(slide, 6.85, 1.75, 5.9, 3.35, """{
  "result": {
    "structuredContent": {
      "peak_mw": 2912.7,
      "capacity_mw": 3325.2,
      "reserve_margin_pct": 12.4,
      "risk": "Élevé",
      "peak_at": "2026-11-13 19:00"
    },
    "isError": false,
    "metadata": {"latency_ms": 1.9}
  }
}""", size=8.4, lang="json")
    for index, (value, label, color) in enumerate([("1,9 ms", "latence", TEAL), ("ok", "statut", GREEN), ("JSON-RPC", "transport", BLUE)]):
        stat(slide, 0.55 + index * 4.12, 5.38, 3.85, 0.95, value, label, color, "", value_size=20)
    footer(slide, 14, TOTAL)
    notes(slide, "L'appel est standard, la réponse est structurée, la latence est mesurée. Le dashboard affiche le JSON brut.")

    # ------------------------------------------------------------------ #
    # 15. A2A pillars
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "A2A", "Agent-to-Agent : découvrir, déléguer, agréger", "A2A")
    pillars = [
        ("1", "AgentCard", "Chaque agent publie son identité, ses compétences, ses outils et son endpoint.", PURPLE),
        ("2", "Discovery", "L'orchestrateur interroge les cartes et sélectionne le spécialiste le plus pertinent.", TEAL),
        ("3", "Delegation", "La tâche part avec un correlation_id ; l'artifact revient et est agrégé.", AMBER),
    ]
    for index, (number, title, body, color) in enumerate(pillars):
        x = 0.55 + index * 4.12
        rect(slide, x, 1.75, 3.85, 2.55, WHITE, line=BORDER, radius=0.08, shape=5)
        rect(slide, x, 1.75, 3.85, 0.08, color)
        rect(slide, x + 0.20, 1.98, 0.5, 0.5, color, shape=1)
        txt(slide, x + 0.20, 2.08, 0.5, 0.28, number, 12, WHITE, True, align=PP_ALIGN.CENTER)
        txt(slide, x + 0.82, 1.98, 2.75, 0.35, title, 14, NAVY, True)
        txt(slide, x + 0.22, 2.65, 3.42, 1.35, body, 9.3, MUTED, line_spacing=1.1)
    rect(slide, 0.55, 4.55, 12.22, 1.15, NAVY, radius=0.10, shape=5)
    txt(slide, 0.85, 4.75, 11.6, 0.28, "Chaque orchestration génère un correlation_id unique : A2A-XXXXXXXX", 13, WHITE, True)
    txt(slide, 0.85, 5.10, 11.6, 0.25, "Il relie discovery, délégations et agrégation dans le journal data/a2a_delegations.jsonl.",
        9.2, RGBColor(0xC9, 0xD8, 0xE8))
    txt(slide, 0.55, 5.95, 12.2, 0.3, "A2A permet une collaboration inter-agents standardisée, traçable et sécurisée.", 10, MUTED)
    footer(slide, 15, TOTAL)
    notes(slide, "Trois piliers : AgentCard, discovery, delegation. Le correlation_id est la clé de la traçabilité.")

    # ------------------------------------------------------------------ #
    # 16. A2A agents
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "A2A", "Quatre agents, quatre expertises", "AGENTCARDS")
    icons = {"grid-analyst": "▦", "outage-inspector": "⚠", "billing-advisor": "◫", "forecast-agent": "◔"}
    colors = {"grid-analyst": TEAL, "outage-inspector": RED, "billing-advisor": AMBER, "forecast-agent": BLUE}
    for index, (agent_id, info) in enumerate(core.AGENT_CAPABILITIES.items()):
        x = 0.55 + index * 3.12
        rect(slide, x, 1.72, 2.92, 3.65, WHITE, line=BORDER, radius=0.08, shape=5)
        rect(slide, x, 1.72, 2.92, 0.08, colors[agent_id])
        txt(slide, x + 0.18, 1.92, 0.45, 0.4, icons[agent_id], 18, colors[agent_id], True)
        txt(slide, x + 0.68, 1.92, 2.05, 0.35, info["label"], 11.5, NAVY, True)
        txt(slide, x + 0.68, 2.25, 2.05, 0.22, f"port {info['port']}", 7.5, MUTED)
        txt(slide, x + 0.18, 2.65, 2.55, 0.75, info["description"], 8.2, MUTED, line_spacing=1.08)
        for key_index, keyword in enumerate(info["keywords"][:4]):
            pill(slide, x + 0.18 + (key_index % 2) * 1.25, 3.55 + (key_index // 2) * 0.35, 1.18, 0.26, keyword, LIGHT, NAVY2, 6.3)
        txt(slide, x + 0.18, 4.42, 2.55, 0.2, "Outils", 7, MUTED, True)
        txt(slide, x + 0.18, 4.62, 2.55, 0.45, " · ".join(info["tools"][:2]), 6.4, INK)
        pill(slide, x + 0.18, 4.95, 1.05, 0.24, "en ligne", SOFT_GREEN, GREEN, 6.3)
    rect(slide, 0.55, 5.72, 12.22, 0.55, SOFT_GREEN, radius=0.10, shape=5)
    txt(slide, 0.78, 5.88, 11.8, 0.25, "Chaque agent publie /.well-known/agent.json et accepte /message. Le hub peut en ajouter un sans modifier le dashboard.",
        9, GREEN, True)
    footer(slide, 16, TOTAL)
    notes(slide, "Grid Analyst, Outage Inspector, Billing Advisor, Forecast Agent. Chacun a ses outils et ses mots-clés.")

    # ------------------------------------------------------------------ #
    # 17. A2A orchestration
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "A2A", "Une tâche, trois agents, un correlation_id", "DÉLÉGATION")
    rect(slide, 0.55, 1.72, 5.55, 1.05, WHITE, line=BORDER, radius=0.08, shape=5)
    txt(slide, 0.75, 1.85, 5.15, 0.22, "QUESTION", 7.5, AMBER, True, char_spacing=1.5)
    txt(slide, 0.75, 2.08, 5.15, 0.55, "« Analyse la coupure de Maârif, évalue le risque de pointe demain et propose un plan d'action. »",
        8.4, NAVY, line_spacing=1.05)
    rect(slide, 0.55, 2.98, 5.55, 0.85, NAVY, radius=0.08, shape=5)
    txt(slide, 0.75, 3.12, 5.15, 0.22, "ORCHESTRATEUR 8101", 8, AMBER, True, char_spacing=1)
    txt(slide, 0.75, 3.36, 5.15, 0.3, "sélectionne 3 agents · corrélation A2A-4ABEF411", 8.5, WHITE)
    artifacts = [
        ("Outage Inspector", "MAARIF-01 · 96 min · 2 340 clients", RED),
        ("Forecast Agent", "Pointe 2 913 MW · marge 12,4 %", BLUE),
        ("Billing Advisor", "Compensation + plan d'économies", AMBER),
    ]
    for index, (agent, summary, color) in enumerate(artifacts):
        y = 4.10 + index * 0.82
        rect(slide, 0.55, y, 5.55, 0.66, WHITE, line=BORDER, radius=0.08, shape=5)
        rect(slide, 0.55, y, 0.07, 0.66, color)
        txt(slide, 0.72, y + 0.10, 1.85, 0.22, agent, 8.5, NAVY, True)
        txt(slide, 2.55, y + 0.10, 3.4, 0.22, summary, 7.5, MUTED)
    timeline = [
        ("09:15:01", "Discovery", "4 AgentCards interrogées", TEAL),
        ("09:15:02", "Sélection", "Outage + Forecast + Billing", PURPLE),
        ("09:15:03", "Délégation", "3 messages envoyés en parallèle", AMBER),
        ("09:15:04", "Agrégation", "6 sources · réponse consolidée", GREEN),
    ]
    for index, (time, title, body, color) in enumerate(timeline):
        y = 1.78 + index * 1.05
        rect(slide, 6.55, y, 0.1, 0.85, color)
        txt(slide, 6.78, y + 0.03, 0.85, 0.22, time, 7, MUTED, True)
        txt(slide, 7.65, y + 0.02, 1.35, 0.25, title, 9.5, NAVY, True)
        txt(slide, 9.05, y + 0.02, 3.55, 0.6, body, 8.2, MUTED, line_spacing=1.05)
    rect(slide, 6.55, 5.45, 6.2, 0.65, SOFT_GREEN, radius=0.08, shape=5)
    txt(slide, 6.75, 5.60, 5.8, 0.22, "3 artifacts · 6 sources · 134 ms · statut ok", 8.6, GREEN, True)
    footer(slide, 17, TOTAL)
    notes(slide, "L'orchestrateur sélectionne trois agents, délègue en parallèle et agrège. Le correlation_id relie toute la timeline.")

    # ------------------------------------------------------------------ #
    # 18. Dashboard overview
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Dashboard", "Une seule interface pour tout le réseau", "8033")
    if (ROOT / "screenshots" / "home.png").exists():
        image(slide, ROOT / "screenshots" / "home.png", 0.55, 1.68, w=7.85)
    paragraphs(slide, 8.65, 1.90, 4.1, 4.2, [
        ("Vue d'ensemble", " : KPI, courbe de charge, mix et incidents."),
        ("Menu", " : 7 pages, navigation persistante."),
        ("Logo", " : identité VOLTIS, thème navy/ambre."),
        ("Formulaires", " : assistant, MCP et A2A."),
        ("Graphiques", " : Plotly, filtres et exports."),
        ("Statut", " : MCP et A2A en ligne/hors ligne."),
    ], size=9.6, space_after=9)
    for index, (value, label) in enumerate([("42,3", "TWh"), ("72", "incidents"), ("9,3", "score")]):
        x = 8.65 + index * 1.42
        rect(slide, x, 4.55, 1.30, 0.78, WHITE, line=BORDER, radius=0.08, shape=5)
        txt(slide, x + 0.12, 4.65, 1.05, 0.28, value, 14, NAVY, True)
        txt(slide, x + 0.12, 4.98, 1.05, 0.2, label, 7.2, MUTED)
    pill(slide, 8.65, 6.20, 1.25, 0.28, "8033", NAVY, WHITE, 7.5)
    pill(slide, 10.00, 6.20, 1.25, 0.28, "MCP 8100", TEAL, WHITE, 7.5)
    pill(slide, 11.35, 6.20, 1.30, 0.28, "A2A 8101", PURPLE, WHITE, 7.5)
    footer(slide, 18, TOTAL)
    notes(slide, "Le dashboard regroupe tout : KPI, assistant, MCP, A2A, statistiques, architecture et documentation.")

    # ------------------------------------------------------------------ #
    # 19. Dashboard assistant
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Dashboard", "L'assistant montre sa propre qualité", "SCORES")
    if (ROOT / "screenshots" / "assistant.png").exists():
        image(slide, ROOT / "screenshots" / "assistant.png", 0.55, 1.68, w=7.85)
    rect(slide, 8.65, 1.78, 4.1, 1.55, WHITE, line=BORDER, radius=0.08, shape=5)
    txt(slide, 8.85, 1.94, 3.7, 0.25, "Score Reflexion", 9.5, NAVY, True)
    txt(slide, 8.85, 2.28, 1.4, 0.35, "6,4", 22, RED, True)
    txt(slide, 9.55, 2.36, 0.5, 0.25, "→", 12, MUTED, True)
    txt(slide, 9.95, 2.28, 1.4, 0.35, "9,3", 22, GREEN, True)
    txt(slide, 10.95, 2.36, 1.6, 0.25, "+2,9 pts", 9, GREEN, True)
    txt(slide, 8.85, 2.78, 3.75, 0.35, "1 itération · 3 outils · 39 ms", 8, MUTED)
    criteria = [("Clarté", 9.1, BLUE), ("Exactitude", 9.2, TEAL), ("Concision", 10.0, AMBER), ("Cohérence", 8.3, NAVY2)]
    for index, (label, value, color) in enumerate(criteria):
        y = 3.55 + index * 0.62
        txt(slide, 8.65, y, 1.3, 0.22, label, 8, MUTED, True)
        rect(slide, 9.95, y + 0.02, 2.4, 0.16, LIGHT, radius=0.08, shape=5)
        rect(slide, 9.95, y + 0.02, 2.4 * value / 10, 0.16, color, radius=0.08, shape=5)
        txt(slide, 12.45, y - 0.03, 0.45, 0.22, f"{value}", 8, color, True, align=PP_ALIGN.RIGHT)
    rect(slide, 8.65, 6.18, 4.1, 0.5, SOFT_GOLD, radius=0.08, shape=5)
    txt(slide, 8.82, 6.31, 3.8, 0.22, "La réponse finale est sourcée et exportable en JSON.", 7.8, RGBColor(0x7A, 0x5B, 0x00))
    footer(slide, 19, TOTAL)
    notes(slide, "Le formulaire lance le workflow. L'utilisateur voit le score initial, le score final, le gain, les outils et la latence.")

    # ------------------------------------------------------------------ #
    # 20. Dashboard stats
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Dashboard", "Des statistiques qui alimentent les agents", "STATS")
    if (ROOT / "screenshots" / "stats.png").exists():
        image(slide, ROOT / "screenshots" / "stats.png", 0.55, 1.68, w=7.85)
    paragraphs(slide, 8.65, 1.90, 4.1, 3.4, [
        ("Consommation", " : 42,3 TWh, 8 régions, 12 mois."),
        ("Pointe", " : 12 830 MW, profil horaire."),
        ("Qualité", " : SAIDI 224 min, pertes 8,1 %."),
        ("Incidents", " : 72 sur 90 jours, 5 causes."),
        ("Benchmark", " : 5 tâches, scores avant/après."),
    ], size=9.6, space_after=9)
    stat(slide, 8.65, 3.45, 1.95, 0.88, "42,3", "TWh · 8 régions", TEAL, "", 18)
    stat(slide, 10.80, 3.45, 1.95, 0.88, "224", "min SAIDI · cible 300", AMBER, "", 18)
    stat(slide, 8.65, 4.48, 1.95, 0.88, "8,1 %", "pertes · moyenne", BLUE, "", 18)
    stat(slide, 10.80, 4.48, 1.95, 0.88, "72", "incidents · 90 jours", RED, "", 18)
    rect(slide, 8.65, 5.55, 4.1, 0.7, SOFT_GREEN, radius=0.08, shape=5)
    txt(slide, 8.82, 5.68, 3.8, 0.22, "Export CSV + tableau régional", 8.5, GREEN, True)
    txt(slide, 8.82, 5.92, 3.8, 0.22, "Les mêmes données alimentent le RAG et les agents.", 7.5, MUTED)
    footer(slide, 20, TOTAL)
    notes(slide, "La page statistiques montre les mêmes données que celles utilisées par les agents : cohérence garantie.")

    # ------------------------------------------------------------------ #
    # 21. Docker
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Déploiement", "Docker Compose : trois services, un réseau", "DOCKER")
    if (ASSETS / "docker_topology.png").exists():
        image(slide, ASSETS / "docker_topology.png", 0.55, 1.65, w=9.35)
    for index, (name, port, color) in enumerate([("dashboard", "8033", NAVY), ("mcp", "8100", TEAL), ("a2a", "8101-8105", PURPLE)]):
        y = 1.85 + index * 1.28
        rect(slide, 10.25, y, 2.55, 0.98, WHITE, line=BORDER, radius=0.08, shape=5)
        rect(slide, 10.25, y, 0.07, 0.98, color)
        txt(slide, 10.42, y + 0.12, 1.6, 0.25, name, 10.5, NAVY, True)
        txt(slide, 10.42, y + 0.42, 1.9, 0.22, f"port {port}", 7.5, MUTED)
        txt(slide, 11.55, y + 0.12, 1.1, 0.22, "healthy", 6.8, GREEN, True, align=PP_ALIGN.RIGHT)
    code(slide, 10.25, 5.75, 2.55, 0.62, "docker compose up --build", size=7.0, lang="bash")
    footer(slide, 21, TOTAL)
    notes(slide, "Docker compose lance les trois services avec healthchecks et volumes partagés. Une seule commande suffit.")

    # ------------------------------------------------------------------ #
    # 22. Sécurité
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Confiance", "Sécurité, robustesse et observabilité", "SÉCURITÉ")
    risks = [
        ("Injection de prompt", "Périmètre d'outils limité, pas d'exécution arbitraire.", "Filtrage + garde-fous LLM.", RED),
        ("Fuite de données", "Aucune donnée réelle, clients synthétiques.", "Chiffrement + RBAC.", AMBER),
        ("Appel non autorisé", "Validation JSON Schema, liste d'outils.", "Bearer + mTLS + quotas.", PURPLE),
        ("Indisponibilité", "Repli local, healthchecks, redémarrage.", "Réplication + circuit breaker.", TEAL),
    ]
    for index, (title, measure, evolution, color) in enumerate(risks):
        x = 0.55 + (index % 2) * 6.15
        y = 1.75 + (index // 2) * 2.05
        rect(slide, x, y, 5.95, 1.82, WHITE, line=BORDER, radius=0.08, shape=5)
        rect(slide, x, y, 0.08, 1.82, color)
        txt(slide, x + 0.22, y + 0.14, 5.4, 0.28, title, 12, NAVY, True)
        txt(slide, x + 0.22, y + 0.50, 5.45, 0.55, measure, 8.8, MUTED, line_spacing=1.05)
        txt(slide, x + 0.22, y + 1.18, 5.45, 0.25, "Production : " + evolution, 7.8, color, True)
    rect(slide, 0.55, 5.95, 12.22, 0.52, NAVY, radius=0.10, shape=5)
    txt(slide, 0.78, 6.10, 11.8, 0.22, "Aucune manœuvre, consignation ou décision client n'est exécutée sans validation humaine.",
        9.5, WHITE, True)
    footer(slide, 22, TOTAL)
    notes(slide, "Quatre risques et leurs mesures. Le point clé : l'agent assiste, il ne remplace pas l'opérateur.")

    # ------------------------------------------------------------------ #
    # 23. Benchmark
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Résultats", "Cinq tâches, deux itérations, un gain mesurable", "BENCHMARK")
    if (ASSETS / "benchmark_chart.png").exists():
        image(slide, ASSETS / "benchmark_chart.png", 0.55, 1.70, w=7.55)
    rows = [
        [task["id"], f"{task['initial']['overall']}", f"{task['final']['overall']}", f"+{task['gain']}"]
        for task in bench["tasks"]
    ]
    table(slide, 8.35, 1.85, 4.35, 2.55, ["Tâche", "Init.", "Final", "Gain"], rows,
          col_widths=[1.3, 1.0, 1.0, 1.0], font_size=8.8)
    stat(slide, 8.35, 4.65, 2.1, 0.95, f"{avg['initial']:.2f}".replace(".", ","), "score initial", RED, "", 18)
    stat(slide, 10.60, 4.65, 2.1, 0.95, f"{avg['final']:.2f}".replace(".", ","), "score final", GREEN, "", 18)
    rect(slide, 8.35, 5.80, 4.35, 0.55, SOFT_GOLD, radius=0.08, shape=5)
    txt(slide, 8.52, 5.95, 4.0, 0.22, f"Gain moyen +{avg['gain']} pts · {avg['citations']} citations/réponse", 8.2, RGBColor(0x7A, 0x5B, 0x00), True)
    footer(slide, 23, TOTAL)
    notes(slide, "Le benchmark couvre incident, mix, facture, prévision et pertes. Toutes les tâches progressent.")

    # ------------------------------------------------------------------ #
    # 24. Results
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Résultats", "Ce que la boucle apporte concrètement", "RÉSULTATS")
    stats = [
        (f"{avg['initial']:.2f}".replace(".", ","), "score initial", "brouillon", RED),
        (f"{avg['final']:.2f}".replace(".", ","), "score final", "après 2 itérations", GREEN),
        (f"+{avg['gain']:.2f}".replace(".", ","), "gain moyen", "par tâche", AMBER),
        (f"{avg['citations']:.1f}".replace(".", ","), "citations", "par réponse", TEAL),
    ]
    for index, (value, label, sub, color) in enumerate(stats):
        stat(slide, 0.55 + index * 3.12, 1.72, 2.92, 1.18, value, label, color, sub, 26)
    if (ASSETS / "criteria_chart.png").exists():
        image(slide, ASSETS / "criteria_chart.png", 0.55, 2.95, w=6.9, h=3.5)
    rect(slide, 8.15, 2.95, 4.6, 3.3, WHITE, line=BORDER, radius=0.08, shape=5)
    txt(slide, 8.38, 3.12, 4.1, 0.25, "Lecture", 9.5, NAVY, True)
    paragraphs(slide, 8.38, 3.45, 4.1, 2.3, [
        ("Exactitude", " progresse le plus : chiffres et sources."),
        ("Cohérence", " : structure Synthèse → Plan → Limites."),
        ("Concision", " stable : pas de répétition."),
        ("Clarté", " : titres, bullets, gras."),
    ], size=8.5, space_after=5)
    rect(slide, 0.55, 6.55, 12.22, 0.4, SOFT_GREEN, radius=0.10, shape=5)
    txt(slide, 0.78, 6.67, 11.8, 0.22, "Chaque itération apporte une amélioration mesurable : c'est la validation du pattern Reflexion.",
        9.5, GREEN, True)
    footer(slide, 24, TOTAL)
    notes(slide, "Le gain est surtout sur l'exactitude et la cohérence. La concision reste stable, ce qui évite les réponses bavardes.")

    # ------------------------------------------------------------------ #
    # 25. Limites & perspectives
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    header(slide, "Recul", "Limites et perspectives", "RECUL")
    rect(slide, 0.55, 1.72, 5.95, 3.65, SOFT_RED, line=RGBColor(0xF0, 0xC9, 0xC4), radius=0.08, shape=5)
    txt(slide, 0.78, 1.90, 5.4, 0.28, "LIMITES ASSUMÉES", 8.5, RGBColor(0xB2, 0x3B, 0x2E), True, char_spacing=1.5)
    paragraphs(slide, 0.78, 2.30, 5.5, 2.9, [
        ("Données", " synthétiques, pas de SCADA réel."),
        ("Prévision", " par persistance, pas de modèle ML entraîné."),
        ("Retrieval", " TF-IDF, pas d'embeddings."),
        ("Authentification", " absente en démo."),
        ("Haute disponibilité", " non traitée."),
        ("Validation terrain", " : aucune campagne réelle."),
    ], size=10.0, space_after=10, bullet_color=RED)
    rect(slide, 6.80, 1.72, 5.97, 3.65, SOFT_GREEN, line=RGBColor(0xBF, 0xE5, 0xDB), radius=0.08, shape=5)
    txt(slide, 7.03, 1.90, 5.4, 0.28, "PERSPECTIVES", 8.5, GREEN, True, char_spacing=1.5)
    paragraphs(slide, 7.03, 2.30, 5.5, 2.9, [
        ("Connecter", " un SCADA de test et un référentiel réel."),
        ("Embeddings", " + base vectorielle, BM25 conservé."),
        ("Juge LLM", " et tests de non-régression."),
        ("Observabilité", " : OpenTelemetry, traces distribuées."),
        ("Kubernetes", " : auth, quotas, isolation réseau."),
        ("Audit & conformité", " : traçabilité des modèles."),
    ], size=10.0, space_after=10, bullet_color=GREEN)
    rect(slide, 0.55, 5.65, 12.22, 0.45, NAVY, radius=0.10, shape=5)
    txt(slide, 0.78, 5.77, 11.8, 0.22, "Prochaine étape : un pilote sur un périmètre réel, avec validation humaine et mesure continue.",
        9.2, WHITE, True)
    footer(slide, 25, TOTAL)
    notes(slide, "Les limites sont claires : données synthétiques, prévision simple, pas d'auth. Les perspectives sont réalistes.")

    # ------------------------------------------------------------------ #
    # 26. Conclusion
    # ------------------------------------------------------------------ #
    slide = blank(prs)
    rect(slide, 0, 0, 13.333, 7.5, NAVY)
    rect(slide, 10.0, -1.3, 4.3, 4.3, RGBColor(0x12, 0x3A, 0x60), shape=9)
    rect(slide, 11.2, 4.3, 2.5, 2.5, RGBColor(0x0F, 0x31, 0x55), shape=9)
    image(slide, ASSETS / "logo.png", 0.65, 0.50, w=3.2)
    txt(slide, 0.70, 2.05, 8.2, 0.3, "CONCLUSION", 9.5, AMBER, True, char_spacing=2.5)
    txt(slide, 0.70, 2.40, 9.2, 1.5, "Un agent qui décide,\ncite et se corrige.", 32, WHITE, True, "Aptos Display", line_spacing=0.92)
    txt(slide, 0.70, 4.05, 8.8, 0.6, "VOLTIS relie les données, les procédures et les agents dans un hub interopérable, mesurable et démontrable.",
        12.5, RGBColor(0xC9, 0xD8, 0xE8), line_spacing=1.1)
    takeaways = [
        ("MCP", "10 outils standards", TEAL),
        ("A2A", "4 agents · 1 hub", PURPLE),
        ("Reflexion", f"{avg['initial']:.2f} → {avg['final']:.2f}".replace(".", ","), AMBER),
    ]
    for index, (title, body, color) in enumerate(takeaways):
        x = 0.70 + index * 2.85
        rect(slide, x, 5.25, 2.55, 0.95, RGBColor(0x16, 0x3A, 0x5D), line=RGBColor(0x2A, 0x52, 0x77), radius=0.08, shape=5)
        txt(slide, x + 0.18, 5.38, 2.2, 0.25, title, 8.5, color, True, char_spacing=1)
        txt(slide, x + 0.18, 5.65, 2.2, 0.3, body, 10.5, WHITE, True)
    line(slide, 0.70, 6.55, 9.2, 6.55, RGBColor(0x2A, 0x52, 0x77), 0.8)
    txt(slide, 0.70, 6.68, 6.0, 0.35, "Merci · Questions ?", 14, AMBER, True)
    txt(slide, 7.20, 6.70, 5.4, 0.3, "localhost:8033 · Documentation et présentation incluses", 8, RGBColor(0x9F, 0xB8, 0xD0), align=PP_ALIGN.RIGHT)
    footer(slide, 26, TOTAL)
    notes(slide, "Conclusion : un hub qui décide, cite et se corrige. Merci, je suis disponible pour les questions et la démonstration live.")

    prs.save(OUT)
    return OUT


def export_pdf(pptx_path: Path) -> None:
    try:
        import shutil
        import uuid

        import win32com.client  # type: ignore

        temp = pptx_path.with_name(f"_export_{uuid.uuid4().hex[:6]}.pptx")
        shutil.copy2(pptx_path, temp)
        powerpoint = win32com.client.DispatchEx("PowerPoint.Application")
        powerpoint.Visible = 1
        presentation = powerpoint.Presentations.Open(str(temp), WithWindow=False)
        presentation.SaveAs(str(PDF), 32)  # ppSaveAsPDF
        presentation.Close()
        powerpoint.Quit()
        temp.unlink(missing_ok=True)
        print("PDF généré :", PDF)
    except Exception as error:
        print("Export PDF indisponible :", error)


if __name__ == "__main__":
    path = build()
    print("Présentation générée :", path)
    print("Taille :", round(path.stat().st_size / 1024, 1), "Ko")
    export_pdf(path)
