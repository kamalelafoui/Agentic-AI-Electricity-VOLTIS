# -*- coding: utf-8 -*-
"""Génère la documentation finale VOLTIS au format DOCX (et PDF via Word)."""
from __future__ import annotations

import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(ROOT / "scripts"))

from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: E402

from docx_helpers import (  # noqa: E402
    AMBER, ASSETS, GREEN, MUTED, NAVY, RED, TEAL, add_toc, bullets, callout,
    code_block, cover, figure, h1, h2, h3, kpi_row, new_document, para, table,
)
from langgraph_workflow import graph_spec  # noqa: E402
from shared import electricity_core as core  # noqa: E402

DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)
OUT = DOCS / "Documentation_Finale_VOLTIS.docx"
PDF = DOCS / "Documentation_Finale_VOLTIS.pdf"


def load_benchmarks() -> dict:
    return json.loads((ROOT / "data" / "benchmarks.json").read_text(encoding="utf-8"))


def fmt(value: float, decimals: int = 0) -> str:
    if decimals == 0:
        return f"{value:,.0f}".replace(",", " ")
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")


def build() -> Path:
    kpis = core.national_kpis()
    mix = core.production_mix()
    bench = load_benchmarks()
    spec = graph_spec()
    avg = bench["averages"]
    regions = core.regions()
    documents = core.corpus()
    tools = core.list_tools()
    customers = core.customers()

    doc = new_document(
        title="VOLTIS — Documentation finale",
        subject="Agentic AI for the Electricity Sector — MCP, A2A, RAG, LangGraph, dashboard et Docker",
        header_label="Documentation finale",
    )
    cover(
        doc,
        "Mini-projet final · Agentic AI for the Electricity Sector",
        "VOLTIS — le hub agentique du réseau électrique",
        "MCP, A2A, RAG agentique, LangGraph et dashboard : une plateforme unique pour l'exploitation, "
        "la maintenance et la relation client.",
        [
            ("Version", "1.0.0 — version finale corrigée"),
            ("Date", "12 novembre 2026"),
            ("Auteur", "Direction Digitale & Exploitation — VOLTIS"),
            ("Périmètre", "8 régions · 9,25 M clients · 12 documents · 10 outils MCP · 4 agents A2A"),
            ("Stack", "Python 3.12 · Streamlit · FastAPI · LangGraph · Plotly · Docker"),
            ("Livrables", "Dashboard 8033 · DOCX/PDF · PPTX · 6 manifests JSON · 5 AgentCards"),
        ],
        [
            "Architecture du hub interopérable MCP + A2A + RAG + LangGraph.",
            "Dashboard Streamlit complet : menu, logo, formulaires, graphiques et statistiques.",
            "Serveur MCP exposant 10 outils avec schémas JSON et traçabilité.",
            "Orchestrateur A2A et 4 agents spécialisés avec AgentCards et correlation_id.",
            "Boucle Reflexion mesurée sur 5 tâches : scores avant/après et sources citées.",
            "Déploiement Docker en trois services et guide de démonstration.",
        ],
    )

    # ------------------------------------------------------------------ #
    # Résumé exécutif
    # ------------------------------------------------------------------ #
    h1(doc, "Résumé exécutif", page_break=False)
    para(
        doc,
        "Le secteur électrique fait face à une équation inédite : une demande qui croît, une production "
        "renouvelable intermittente, un parc vieillissant et des clients qui attendent des réponses immédiates. "
        "Les tableaux de bord classiques décrivent la situation, mais ils ne décident pas, ne citent pas leurs "
        "sources et n'apprennent pas de leurs erreurs. VOLTIS répond à ce manque avec une plateforme agentique "
        "qui relie les données du réseau, les procédures internes et des agents spécialisés.",
    )
    para(
        doc,
        "La plateforme repose sur quatre briques complémentaires. MCP expose les outils métier de façon standard : "
        "KPI, profils régionaux, incidents, prévision de charge, facturation, recherche documentaire. A2A fait "
        "collaborer quatre agents — Grid Analyst, Outage Inspector, Billing Advisor et Forecast Agent — sous la "
        "coordination d'un orchestrateur qui découvre leurs AgentCards et trace chaque délégation. Un RAG hybride "
        "BM25 + TF-IDF apporte les procédures et référentiels, avec une citation pour chaque affirmation. Enfin, "
        "LangGraph organise le workflow Planner → Retriever → Tools → Writer → Critic → Refiner, avec une boucle "
        "Reflexion mesurée.",
    )
    para(
        doc,
        f"Les résultats sont concrets : {avg['initial']}/10 en moyenne pour le brouillon initial, "
        f"{avg['final']}/10 après deux itérations, soit un gain de +{avg['gain']} points sur cinq tâches "
        f"représentatives. Le dashboard 8033 centralise la démonstration, les traces, les scores et les sources. "
        "L'ensemble se lance en une commande locale ou avec Docker Compose.",
    )
    kpi_row(
        doc,
        [
            (f"{kpis['consumption_gwh']/1000:.1f} TWh", "consommation annuelle", "8 régions"),
            (f"{kpis['clients']/1_000_000:.2f} M", "clients desservis", "données synthétiques"),
            (str(len(tools)), "outils MCP", "JSON-RPC 2.0"),
            ("4", "agents A2A", "AgentCards publiées"),
            (f"{len(documents)}", "documents RAG", f"{sum(len(d['chunks']) for d in documents)} chunks"),
            (f"{avg['final']}/10", "score Reflexion", f"+{avg['gain']} pts"),
        ],
    )
    callout(
        doc,
        "Ce qui distingue VOLTIS",
        "Un seul point d'entrée pour l'utilisateur, mais trois protocoles séparés et complémentaires. "
        "Chaque réponse est chiffrée, sourcée, notée et traçable. Le système continue de fonctionner en repli "
        "local si un service est indisponible, ce qui le rend démontrable hors ligne.",
        "success",
    )

    # ------------------------------------------------------------------ #
    # Sommaire
    # ------------------------------------------------------------------ #
    doc.add_page_break()
    h1(doc, "Sommaire", page_break=False)
    p = doc.add_paragraph()
    add_toc(p)
    para(
        doc,
        "Le sommaire se met à jour automatiquement à l'ouverture du document (Ctrl+A puis F9) ou lors de "
        "l'export PDF. Les numéros de page correspondent à la version PDF livrée.",
        size=8.2,
        italic=True,
    )

    # ------------------------------------------------------------------ #
    # 1. Contexte
    # ------------------------------------------------------------------ #
    h1(doc, "1. Contexte et problématique")
    h2(doc, "1.1 Le réseau électrique sous tension")
    para(
        doc,
        "Le réseau de distribution est soumis à quatre pressions simultanées. La première est la croissance de la "
        "demande, portée par l'urbanisation, la climatisation et l'électrification des usages. La deuxième est "
        "l'intermittence des énergies renouvelables : le solaire s'efface après 17 h, précisément lorsque la pointe "
        "du soir se forme. La troisième est le vieillissement des actifs : transformateurs, départs et postes "
        "sources demandent une maintenance conditionnelle. La quatrième est l'exigence client : les abonnés veulent "
        "comprendre leur facture, signaler une coupure et obtenir une compensation sans attendre.",
    )
    bullets(
        doc,
        [
            "Pointe du soir : la marge de réserve peut descendre sous 8 % lors des vagues de chaleur.",
            "Pertes techniques et non techniques : environ 8 % de l'énergie injectée n'est pas facturée.",
            "Continuité : le SAIDI national doit rester sous 300 minutes par client et par an.",
            "Renouvelables : 37,9 % du mix, avec une production variable et difficile à prévoir à J+1.",
            "Relation client : les réclamations et les demandes de compensation restent dispersées.",
        ],
    )
    h2(doc, "1.2 Les limites des approches classiques")
    table(
        doc,
        ["Approche", "Limite", "Conséquence opérationnelle"],
        [
            ["Tableau de bord descriptif", "Montre des KPI mais n'explique pas et ne recommande pas.",
             "L'opérateur reconstruit le raisonnement à la main."],
            ["RAG simple", "Une seule recherche, pas de reformulation ni de vérification.",
             "Réponse incomplète si la question est ambiguë."],
            ["Scripts métier isolés", "Chaque outil a sa propre interface et ses propres formats.",
             "Intégration coûteuse, pas de découverte automatique."],
            ["Assistants mono-agent", "Un seul agent ne couvre ni le réseau, ni la facture, ni la prévision.",
             "Escalade manuelle et perte de contexte."],
            ["Réponse LLM sans source", "Risque d'hallucination et absence de traçabilité.",
             "Décision non auditables, confiance limitée."],
        ],
        widths=[4.2, 6.0, 6.0],
        caption="Tableau 1 — Les cinq limites qui motivent l'architecture agentique.",
    )
    h2(doc, "1.3 L'opportunité agentique")
    para(
        doc,
        "Un agent combine un modèle de langage, des outils, de la mémoire et une capacité de critique. Il peut "
        "décomposer une question, choisir un outil, vérifier la cohérence du résultat et recommencer si la qualité "
        "est insuffisante. VOLTIS pousse cette logique plus loin en séparant les responsabilités : MCP standardise "
        "les outils, A2A standardise la collaboration entre agents, RAG apporte la connaissance et LangGraph "
        "orchestre le tout.",
    )
    callout(
        doc,
        "Principe directeur",
        "Ne pas construire un agent qui sait tout, mais un hub qui sait trouver le bon outil, le bon document "
        "et le bon spécialiste, puis vérifier sa propre réponse avant de la publier.",
        "info",
    )

    # ------------------------------------------------------------------ #
    # 2. Objectifs
    # ------------------------------------------------------------------ #
    h1(doc, "2. Objectifs, périmètre et critères de validation", page_break=False)
    h2(doc, "2.1 Objectif général")
    para(
        doc,
        "Concevoir et livrer une plateforme agentique de démonstration pour le secteur électrique, capable de "
        "répondre à des questions métier en combinant données réseau, documents internes et agents spécialisés, "
        "avec des sources citées, une auto-critique mesurée et un déploiement reproductible.",
    )
    h2(doc, "2.2 Objectifs spécifiques")
    bullets(
        doc,
        [
            "Exposer au moins 8 outils métier via un serveur MCP conforme aux schémas JSON.",
            "Faire collaborer au moins 2 agents A2A sur une même tâche, avec AgentCards et correlation_id.",
            "Mettre en œuvre un RAG agentique hybride avec citations et vérification de suffisance.",
            "Implémenter une boucle Reflexion Generate → Critic → Refine avec scores avant/après.",
            "Livrer un dashboard 8033 complet : menu, logo, formulaires, graphiques et statistiques.",
            "Conteneuriser la solution avec Docker Compose et produire la documentation et la présentation.",
        ],
    )
    h2(doc, "2.3 Périmètre")
    table(
        doc,
        ["Dans le périmètre", "Hors périmètre"],
        [
            ["Données synthétiques de 8 régions, 72 incidents, 24 clients, 12 documents.",
             "Connexion à un SCADA réel, à un ERP de facturation ou à une base clients."],
            ["Serveur MCP local, orchestrateur A2A et 4 agents spécialisés.",
             "Authentification forte, SSO et gestion fine des habilitations."],
            ["Dashboard Streamlit, visualisations Plotly, formulaires et traces.",
             "Application mobile native ou portail client public."],
            ["Déploiement Docker Compose sur une machine unique.",
             "Orchestration Kubernetes, haute disponibilité et multi-région."],
            ["Évaluation sur 5 tâches et 10 outils.",
             "Benchmark exhaustif sur des milliers de requêtes de production."],
        ],
        widths=[8.1, 8.1],
        caption="Tableau 2 — Périmètre fonctionnel et exclusions.",
    )
    h2(doc, "2.4 Critères de validation")
    table(
        doc,
        ["Critère", "Preuve apportée dans le livrable"],
        [
            ["Interopérabilité", "MCP JSON-RPC + A2A HTTP + AgentCards ; le dashboard appelle les deux."],
            ["Agentic RAG", "Planner, retrieval multi-étapes, vérification, citations et critique."],
            ["Collaboration ≥ 2 agents", "L'orchestrateur sélectionne 2 à 4 agents et agrège leurs artifacts."],
            ["Auto-réflexion", "Boucle Writer → Critic → Refiner, scores avant/après sur 5 tâches."],
            ["Architecture", "Schéma du hub, six couches, ports, flux et ADR documentés."],
            ["Documentation", "DOCX final, README, guide, 5 AgentCards complètes."],
            ["Démonstration", "Dashboard live 8033, scénario bout en bout, captures et JSON."],
        ],
        widths=[4.0, 12.2],
        caption="Tableau 3 — Correspondance entre les critères du projet et les preuves fournies.",
    )
    h2(doc, "2.5 Public cible")
    para(
        doc,
        "La plateforme s'adresse à quatre profils : le dispatcher qui prépare la pointe, l'ingénieur de maintenance "
        "qui diagnostique un incident, le conseiller client qui explique une facture et le manager qui suit les KPI. "
        "Chaque profil retrouve dans le dashboard un langage, des filtres et des actions adaptés.",
    )

    # ------------------------------------------------------------------ #
    # 3. Architecture
    # ------------------------------------------------------------------ #
    h1(doc, "3. Architecture globale")
    h2(doc, "3.1 Vue d'ensemble")
    figure(doc, ASSETS / "architecture_hub.png", "Figure 1 — Le hub agentique VOLTIS : expérience, orchestration, agents, protocoles, données et infrastructure.")
    para(
        doc,
        "L'architecture est volontairement en couches. Le dashboard ne parle jamais directement à un agent "
        "spécialisé : il passe par le hub LangGraph, qui décide d'appeler un outil MCP ou de déléguer à l'orchestrateur "
        "A2A. Cette séparation permet de remplacer un agent ou un outil sans modifier l'interface utilisateur.",
    )
    h2(doc, "3.2 Les six couches")
    table(
        doc,
        ["Couche", "Composants", "Responsabilité"],
        [
            ["Expérience", "Dashboard Streamlit 8033, formulaires, graphiques, documentation.",
             "Rendre la plateforme utilisable sans connaissance technique."],
            ["Orchestration", "LangGraph, Planner, Critic, Refiner, orchestrateur A2A 8101.",
             "Décider, déléguer, vérifier et agréger."],
            ["Agents", "Grid Analyst 8102, Outage Inspector 8103, Billing Advisor 8104, Forecast Agent 8105.",
             "Traiter une expertise métier spécialisée."],
            ["Protocoles", "MCP JSON-RPC 8100, A2A 0.3, AgentCards, correlation_id.",
             "Standardiser les échanges et la découverte."],
            ["Données", "CSV/JSON, corpus Markdown, index BM25/TF-IDF, journaux JSONL.",
             "Fournir des faits, des procédures et des traces."],
            ["Infrastructure", "Docker, Docker Compose, healthchecks, volumes, variables d'environnement.",
             "Rendre la démonstration reproductible."],
        ],
        widths=[3.2, 7.4, 5.6],
        caption="Tableau 4 — Les six couches de l'architecture VOLTIS.",
    )
    h2(doc, "3.3 Flux de bout en bout")
    bullets(
        doc,
        [
            "L'utilisateur saisit une question, une région et un profil dans le dashboard.",
            "Le Planner détecte l'intention et sélectionne les outils MCP pertinents.",
            "Le Retriever interroge le corpus avec BM25 + TF-IDF et applique un filtre métier.",
            "Le nœud Tools appelle les outils MCP et journalise arguments, latence et statut.",
            "Le Writer produit un brouillon structuré et chiffré.",
            "Le Critic note clarté, exactitude, concision et cohérence, puis liste les défauts.",
            "Si le score est inférieur au seuil, le Refiner réécrit et le Critic re-note.",
            "Le Finalize ajoute les sources, la confiance et renvoie la réponse au dashboard.",
        ],
        style="List Number",
    )
    h2(doc, "3.4 Décisions d'architecture (ADR)")
    table(
        doc,
        ["ID", "Décision", "Justification"],
        [
            ["ADR-001", "MCP pour les outils", "Découverte automatique, schémas JSON, réutilisation hors agent."],
            ["ADR-002", "A2A pour les agents", "Délégation inter-agents, AgentCards, traçabilité par correlation_id."],
            ["ADR-003", "RAG hybride sans base vectorielle", "Démo hors ligne, latence faible, aucune dépendance externe."],
            ["ADR-004", "LangGraph pour l'orchestration", "Graphe explicite, état typé, boucle conditionnelle Reflexion."],
            ["ADR-005", "Streamlit pour le dashboard", "Livraison rapide, formulaires, Plotly, mode local."],
        ],
        widths=[2.0, 5.0, 9.2],
        caption="Tableau 5 — Décisions structurantes et raisons.",
    )
    h2(doc, "3.5 Ports et services")
    table(
        doc,
        ["Service", "Port", "Protocole", "Rôle"],
        [
            ["Dashboard Streamlit", "8033", "HTTP", "Interface, formulaires, KPI, traces"],
            ["Serveur MCP", "8100", "JSON-RPC 2.0 / SSE", "10 outils, ressources, prompts"],
            ["Orchestrateur A2A", "8101", "A2A 0.3", "Discovery, sélection, délégation, agrégation"],
            ["Grid Analyst", "8102", "A2A 0.3", "KPI, consommation, mix"],
            ["Outage Inspector", "8103", "A2A 0.3", "Incidents, SAIDI/SAIFI, MTTR"],
            ["Billing Advisor", "8104", "A2A 0.3", "Factures, tarifs, économies"],
            ["Forecast Agent", "8105", "A2A 0.3", "Prévision, pointe, réserve"],
        ],
        widths=[4.5, 1.6, 4.2, 5.9],
        caption="Tableau 6 — Cartographie des services et des ports.",
    )
    callout(
        doc,
        "Pourquoi un hub plutôt qu'un agent monolithique ?",
        "Le hub isole les responsabilités : un problème de facturation ne recharge pas le modèle de prévision, "
        "et un agent peut être remplacé sans toucher au dashboard. C'est aussi ce qui rend la collaboration "
        "A2A observable : chaque délégation possède un correlation_id et un artifact.",
        "success",
    )

    # ------------------------------------------------------------------ #
    # 4. Données
    # ------------------------------------------------------------------ #
    h1(doc, "4. Données et connaissances", page_break=False)
    h2(doc, "4.1 Un jeu de données synthétique calibré")
    table(
        doc,
        ["Fichier", "Contenu", "Volume"],
        [
            ["data/regions.json", "8 régions, clients, consommation, pointe, pertes, SAIDI/SAIFI", "8 lignes"],
            ["data/load_curve.csv", "Courbe horaire sur 30 jours, 8 régions, température", "5 760 lignes"],
            ["data/monthly_consumption.csv", "Consommation et pointe mensuelles", "96 lignes"],
            ["data/outages.csv", "Incidents, départs, causes, priorités, MTTR", "72 lignes"],
            ["data/customers.json", "24 clients suivis, segments, factures, flexibilité", "24 lignes"],
            ["data/tariffs.json", "5 segments tarifaires, tranches, TVA, taxes", "5 grilles"],
            ["data/corpus.json", "12 documents, 49 chunks, métadonnées versionnées", "49 chunks"],
        ],
        widths=[4.5, 9.0, 2.7],
        caption="Tableau 7 — Fichiers de données et volumes.",
    )
    para(
        doc,
        "Les données sont générées par scripts/build_data.py avec une graine fixe (20261112), ce qui garantit la "
        "reproductibilité. Les ordres de grandeur sont réalistes : 42,3 TWh, 9,25 millions de clients, une pointe "
        "nationale de 12 830 MW et un SAIDI moyen de 224 minutes. Aucune donnée personnelle ou confidentielle "
        "n'est utilisée.",
    )
    h2(doc, "4.2 Les huit régions")
    rows = [
        [
            region["name"], fmt(region["clients"]), fmt(region["consumption_gwh"]),
            fmt(region["peak_mw"]), f"{region['renewable_share_pct']:.1f} %",
            f"{region['losses_pct']:.1f} %", fmt(region["saidi_min"]),
        ]
        for region in sorted(regions, key=lambda row: row["consumption_gwh"], reverse=True)
    ]
    table(
        doc,
        ["Région", "Clients", "GWh/an", "Pointe MW", "% renouv.", "Pertes", "SAIDI min"],
        rows,
        widths=[4.7, 2.1, 2.1, 2.2, 2.0, 1.6, 1.7],
        caption="Tableau 8 — Profil des huit régions du périmètre.",
    )
    h2(doc, "4.3 Le corpus documentaire")
    rows = [
        [document["doc_id"], document["title"], document["category"], document["version"], str(len(document["chunks"]))]
        for document in documents
    ]
    table(
        doc,
        ["ID", "Titre", "Catégorie", "Version", "Chunks"],
        rows,
        widths=[3.9, 7.4, 2.6, 1.6, 1.4],
        font_size=7.6,
        caption="Tableau 9 — Les douze documents indexés par le RAG.",
    )
    h2(doc, "4.4 Hypothèses et limites")
    bullets(
        doc,
        [
            "Données synthétiques : les valeurs sont plausibles mais ne représentent pas un opérateur réel.",
            "Pas de séries temporelles longues : la prévision est une persistance corrigée, pas un modèle ML entraîné.",
            "Tarifs simplifiés : ils reproduisent les tranches et taxes principales, pas toutes les exceptions locales.",
            "Pas de données de compteurs communicants individuelles : les clients sont agrégés.",
            "Le corpus est volontairement court (12 documents) pour rester démontrable et auditable.",
        ],
    )

    # ------------------------------------------------------------------ #
    # 5. LangGraph
    # ------------------------------------------------------------------ #
    h1(doc, "5. Orchestration LangGraph et boucle Reflexion", page_break=False)
    h2(doc, "5.1 Un état typé")
    para(
        doc,
        "Le graphe repose sur un état partagé qui transporte la question, le contexte, les sources, les résultats "
        "d'outils, le brouillon, la critique, les scores et la trace. Chaque nœud reçoit une copie de cet état et "
        "retourne uniquement les champs qu'il modifie, ce qui rend le workflow lisible et testable.",
    )
    table(
        doc,
        ["Champ", "Type", "Rôle"],
        [
            ["question", "str", "Question initiale de l'utilisateur"],
            ["region_code", "str", "Périmètre géographique détecté"],
            ["intent", "str", "billing, forecast, outage, mix, kpi ou rag"],
            ["plan", "list[str]", "Plan lisible affiché dans la trace"],
            ["sources", "list[Source]", "Extraits documentaires avec citations"],
            ["tool_results", "dict", "Résultats structurés des outils MCP"],
            ["tool_trace", "list[ToolCall]", "Outil, arguments, statut, latence"],
            ["draft", "str", "Brouillon puis réponse raffinée"],
            ["score_history", "list[Score]", "Scores initiaux et par itération"],
            ["iterations", "int", "Nombre de passages dans le Refiner"],
            ["final_answer", "str", "Réponse finale avec sources"],
        ],
        widths=[3.5, 4.0, 8.7],
        font_size=8.0,
        caption="Tableau 10 — Champs principaux de l'état LangGraph.",
    )
    h2(doc, "5.2 Les sept nœuds")
    table(
        doc,
        ["Nœud", "Entrée", "Sortie", "Rôle"],
        [
            ["Planner", "question, region", "intent, plan, tools", "Classifie l'intention et choisit les outils."],
            ["Retriever", "question, intent", "sources", "Recherche hybride + filtre métier + diversité."],
            ["Tools", "tool_names", "tool_results, trace", "Appelle les outils et journalise."],
            ["Writer", "sources, tools", "draft", "Rédige un brouillon structuré et chiffré."],
            ["Critic", "draft", "critique, scores", "Note quatre critères et liste les défauts."],
            ["Refiner", "draft, critique", "draft, iterations", "Réécrit avec sources, plan et limites."],
            ["Finalize", "draft, critique", "final_answer", "Consolide, ajoute les sources et la confiance."],
        ],
        widths=[2.3, 3.5, 3.8, 6.6],
        font_size=8.0,
        caption="Tableau 11 — Rôle des sept nœuds du graphe.",
    )
    figure(doc, ASSETS / "workflow_langgraph.png", "Figure 2 — Workflow LangGraph et boucle Reflexion avec seuil de publication.")
    h2(doc, "5.3 La boucle Reflexion")
    para(
        doc,
        "Le pattern Reflexion suit trois temps : Generate (Writer), Critic (évaluation), Refine (réécriture). "
        "Le Critic attribue une note de 0 à 10 sur quatre axes pondérés : clarté 28 %, exactitude 34 %, concision "
        "14 %, cohérence 24 %. Le score global déclenche le Refiner tant qu'il reste sous le seuil (8,2 par défaut) "
        "et que le nombre d'itérations maximum n'est pas atteint.",
    )
    callout(
        doc,
        "Condition d'arrêt",
        "Le graphe s'arrête lorsque le score global est supérieur ou égal au seuil, ou lorsque le nombre maximum "
        "d'itérations est atteint. Le benchmark force deux itérations pour mesurer le gain complet.",
        "info",
    )
    code_block(
        doc,
        """graph = StateGraph(WorkflowState)
graph.add_node("planner", planner_node)
graph.add_node("retrieve", retrieve_node)
graph.add_node("tools", tools_node)
graph.add_node("writer", writer_node)
graph.add_node("critic", critic_node)
graph.add_node("refine", refine_node)
graph.add_node("finalize", finalize_node)

graph.add_edge(START, "planner")
graph.add_edge("planner", "retrieve")
graph.add_edge("retrieve", "tools")
graph.add_edge("tools", "writer")
graph.add_edge("writer", "critic")
graph.add_conditional_edges(
    "critic", should_continue,
    {"refine": "refine", "finalize": "finalize"},
)
graph.add_edge("refine", "critic")
graph.add_edge("finalize", END)""",
        language="python",
    )
    h2(doc, "5.4 Ce que le Critic mesure réellement")
    table(
        doc,
        ["Critère", "Signaux utilisés", "Poids"],
        [
            ["Clarté", "Titres, bullets, longueur, longueur moyenne des phrases, gras.", "28 %"],
            ["Exactitude", "Nombre de valeurs chiffrées, citations, outils appelés, unités.", "34 %"],
            ["Concision", "Longueur totale, répétitions, pénalité si réponse trop courte.", "14 %"],
            ["Cohérence", "Synthèse, plan d'action, sources, recouvrement avec la question, limites.", "24 %"],
        ],
        widths=[2.6, 11.4, 2.2],
        font_size=8.2,
        caption="Tableau 12 — Signaux et pondération du Critic.",
    )
    para(
        doc,
        "Cette notation est déterministe et explicable : elle ne remplace pas un juge LLM, mais elle rend la boucle "
        "Reproducible et auditable. Elle pénalise les réponses vagues, les affirmations non chiffrées et les "
        "réponses sans sources, ce qui pousse le Refiner à produire une réponse opérationnelle.",
    )

    # ------------------------------------------------------------------ #
    # 6. RAG
    # ------------------------------------------------------------------ #
    h1(doc, "6. Agentic RAG", page_break=False)
    h2(doc, "6.1 Du RAG classique au RAG agentique")
    table(
        doc,
        ["Dimension", "RAG classique", "Agentic RAG VOLTIS"],
        [
            ["Requête", "Une seule recherche, sans reformulation.", "Planification, expansion et reformulation (max 2)."],
            ["Sources", "Top-k brut, parfois hors sujet.", "Filtre métier + diversité documentaire imposée."],
            ["Vérification", "Aucune.", "Seuil de suffisance et contrôle de couverture."],
            ["Réponse", "Génération libre.", "Synthèse structurée avec citations [n]."],
            ["Qualité", "Non mesurée.", "Critic Reflexion et score global."],
            ["Traçabilité", "Limitée.", "Chaque affirmation reliée à un document versionné."],
        ],
        widths=[3.0, 6.3, 6.9],
        caption="Tableau 13 — Comparaison RAG classique / Agentic RAG.",
    )
    figure(doc, ASSETS / "rag_pipeline.png", "Figure 3 — Pipeline Agentic RAG : planification, retrieval hybride, vérification, citation et critique.")
    h2(doc, "6.2 Retrieval hybride")
    para(
        doc,
        "Le retriever combine deux signaux. BM25 capture la correspondance lexicale exacte, utile pour les termes "
        "réglementaires (« SAIDI », « consignation », « tranche »). TF-IDF cosinus capture la proximité sémantique "
        "de surface, utile lorsque la question reformule la procédure. Les scores sont fusionnés avec les poids "
        "0,66 pour BM25 et 0,86 pour TF-IDF, puis un bonus de titre et un bonus de phrase exacte sont ajoutés.",
    )
    code_block(
        doc,
        """score = 0.66 * bm25(query, chunk)
      + 0.86 * cosine_tfidf(query, chunk)
      + 0.08 * mots_du_titre_présents
      + 0.12 * phrase_exacte

# BM25 : k1 = 1.5, b = 0.75
# TF-IDF : normalisation NFKD, stopwords français, vecteurs creux
# Filtre métier : documents autorisés par intention
# Diversité : ajout du meilleur chunk des documents obligatoires""",
        language="python",
    )
    h2(doc, "6.3 Chunking et citations")
    para(
        doc,
        "Chaque document est découpé par article (un chunk = un article), avec les métadonnées doc_id, titre, "
        "catégorie, version, date, propriétaire et numéro d'article. La citation affichée est de la forme "
        "« DOC-PREVISION · v2.9 · article 3 ». Ce format permet à un opérateur de retrouver la source exacte et "
        "de vérifier si une version plus récente existe.",
    )
    sample = core.search_documents("procédure de délestage en cas de pointe", 3)
    rows = [
        [f"[{index}]", item["doc_id"], f"v{item['version']}", f"art. {item['article']}", f"{item['relevance_pct']:.0f} %"]
        for index, item in enumerate(sample["results"], 1)
    ]
    table(
        doc,
        ["Rang", "Document", "Version", "Article", "Pertinence"],
        rows,
        widths=[1.4, 6.0, 2.0, 2.2, 2.6],
        caption="Tableau 14 — Exemple de retrieval pour « procédure de délestage en cas de pointe ».",
    )
    h2(doc, "6.4 Garde-fous")
    bullets(
        doc,
        [
            "Filtre métier : chaque intention ne peut citer que les documents autorisés.",
            "Diversité : au moins un extrait de la procédure d'incidents et de la procédure de délestage.",
            "Seuil de suffisance : 0,55 ; en dessous, l'agent reformule jusqu'à deux fois.",
            "Citations obligatoires : le Refiner ajoute la section Sources et des références [n].",
            "Versionnement : la citation inclut la version et la date du document.",
        ],
    )

    # ------------------------------------------------------------------ #
    # 7. MCP
    # ------------------------------------------------------------------ #
    h1(doc, "7. Model Context Protocol (MCP)", page_break=False)
    h2(doc, "7.1 Concept")
    para(
        doc,
        "MCP définit une manière standard pour un agent de découvrir et d'utiliser des ressources externes. "
        "Le serveur publie trois types d'objets : des outils (actions), des ressources (données consultables) et "
        "des prompts (instructions réutilisables). Le client n'a pas besoin de connaître l'implémentation : il "
        "appelle tools/list, lit les schémas JSON et exécute tools/call.",
    )
    figure(doc, ASSETS / "architecture_mcp.png", "Figure 4 — Serveur MCP et catalogue des dix outils.")
    h2(doc, "7.2 Les dix outils exposés")
    rows = [
        [tool["name"], tool["category"], tool["description"]]
        for tool in tools
    ]
    table(
        doc,
        ["Outil", "Catégorie", "Description"],
        rows,
        widths=[4.4, 2.4, 9.4],
        font_size=7.8,
        caption="Tableau 15 — Catalogue MCP.",
    )
    h2(doc, "7.3 Transports et endpoints")
    table(
        doc,
        ["Endpoint", "Méthode", "Usage"],
        [
            ["/mcp", "POST JSON-RPC", "initialize, tools/list, tools/call, resources/read, prompts/list"],
            ["/sse", "GET", "Transport SSE simplifié, événement endpoint puis ping"],
            ["/messages", "POST", "Messages JSON-RPC du transport SSE"],
            ["/api/health", "GET", "Santé, version, nombre d'outils, uptime"],
            ["/api/tools", "GET", "Catalogue REST pour le dashboard"],
            ["/api/tool", "POST", "Appel REST de secours {tool, arguments}"],
            ["/api/calls", "GET", "Derniers appels journalisés"],
        ],
        widths=[3.6, 3.0, 9.6],
        caption="Tableau 16 — Endpoints du serveur MCP.",
    )
    code_block(
        doc,
        """POST http://127.0.0.1:8100/mcp
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "forecast_load",
    "arguments": {"region_code": "CAS", "horizon_h": 24, "temperature_delta": 5}
  }
}

# Réponse (extrait)
{
  "result": {
    "content": [{"type": "text", "text": "{...}"}],
    "structuredContent": {
      "peak_mw": 2912.7,
      "reserve_margin_pct": 12.4,
      "risk": "Élevé"
    },
    "isError": false
  }
}""",
        language="json",
    )
    h2(doc, "7.4 Sécurité et limites")
    bullets(
        doc,
        [
            "Validation des arguments par schéma JSON avant exécution.",
            "Journalisation de chaque appel : outil, arguments, latence, statut.",
            "Pas d'accès fichier arbitraire : le serveur n'expose que les fonctions du socle métier.",
            "En production : jeton Bearer, liste blanche d'outils et limitation de débit.",
            "Le transport SSE est simplifié pour la démo ; un client MCP standard utilise /mcp.",
        ],
    )

    # ------------------------------------------------------------------ #
    # 8. A2A
    # ------------------------------------------------------------------ #
    h1(doc, "8. Agent-to-Agent (A2A)", page_break=False)
    h2(doc, "8.1 Les trois piliers")
    para(
        doc,
        "A2A repose sur trois mécanismes. La discovery permet à un agent de publier une AgentCard décrivant son "
        "identité, ses compétences, ses outils et son endpoint. La delegation permet à un orchestrateur d'envoyer "
        "une tâche à un agent spécialisé. L'aggregation permet de consolider plusieurs artifacts en une réponse "
        "unique, avec un correlation_id qui relie toutes les étapes.",
    )
    figure(doc, ASSETS / "architecture_a2a.png", "Figure 5 — Orchestration A2A : découverte, délégation parallèle et agrégation.")
    h2(doc, "8.2 Les AgentCards")
    cards = []
    for agent_id, info in core.AGENT_CAPABILITIES.items():
        cards.append([agent_id, info["label"], str(info["port"]), ", ".join(info["tools"]), info["description"]])
    table(
        doc,
        ["ID", "Agent", "Port", "Outils", "Mission"],
        cards,
        widths=[2.8, 3.3, 1.3, 4.2, 4.6],
        font_size=7.7,
        caption="Tableau 17 — Les quatre agents spécialisés et leurs outils.",
    )
    h2(doc, "8.3 Sélection des agents")
    para(
        doc,
        "L'orchestrateur combine deux approches. Un score lexical compare les mots-clés de la question aux "
        "capacités des AgentCards. Une règle d'intention ajoute un bonus aux agents attendus : incident → Outage "
        "Inspector + Forecast Agent + Billing Advisor ; facture → Billing Advisor + Grid Analyst ; prévision → "
        "Forecast Agent + Grid Analyst. Le hub sélectionne entre deux et quatre agents et garantit au moins deux "
        "collaborateurs.",
    )
    table(
        doc,
        ["Question", "Agents sélectionnés", "Justification"],
        [
            ["Coupure de Maârif hier soir", "Outage, Forecast, Billing", "Diagnostic, risque de pointe, compensation."],
            ["Mix national et risque demain", "Grid Analyst, Forecast", "Données de production et prévision."],
            ["Facture d'un industriel à 250 MWh", "Billing Advisor, Grid Analyst", "Tarification et contexte régional."],
            ["Pertes techniques et non techniques", "Grid Analyst, Outage Inspector", "KPI, incidents et RAG."],
        ],
        widths=[5.0, 4.8, 6.4],
        font_size=8.0,
        caption="Tableau 18 — Exemples de sélection d'agents.",
    )
    h2(doc, "8.4 correlation_id et traçabilité")
    para(
        doc,
        "Chaque orchestration génère un identifiant unique de la forme A2A-XXXXXXXX. Il est propagé dans chaque "
        "message envoyé aux agents, puis dans le journal data/a2a_delegations.jsonl. Ce journal contient "
        "l'horodatage, l'agent, le statut, la latence, la tâche et un résumé de l'artifact. Il permet de "
        "reconstruire la timeline complète d'une décision.",
    )
    sample_artifacts = [
        {"agent": "Outage Inspector", "latency": "18 ms", "status": "ok", "summary": "Incident MAARIF-01, 96 min, 2 340 clients"},
        {"agent": "Forecast Agent", "latency": "12 ms", "status": "ok", "summary": "Pointe 2 913 MW, marge 12,4 %, risque élevé"},
        {"agent": "Billing Advisor", "latency": "9 ms", "status": "ok", "summary": "Compensation estimée et plan d'économies"},
    ]
    table(
        doc,
        ["Agent", "Latence", "Statut", "Artifact"],
        [[item["agent"], item["latency"], item["status"], item["summary"]] for item in sample_artifacts],
        widths=[4.4, 2.2, 2.0, 7.2],
        caption="Tableau 19 — Exemple de délégation parallèle (correlation A2A-DEMO-0001).",
    )
    h2(doc, "8.5 Ce que A2A apporte concrètement")
    bullets(
        doc,
        [
            "Découplage : chaque agent peut évoluer sans modifier les autres.",
            "Parallélisme : trois agents répondent en moins de 50 ms sur la démo locale.",
            "Traçabilité : un correlation_id unique relie discovery, délégations et agrégation.",
            "Extensibilité : ajouter un agent consiste à publier une AgentCard et un endpoint /message.",
            "Résilience : si un agent est hors ligne, l'orchestrateur bascule en repli local.",
        ],
    )

    # ------------------------------------------------------------------ #
    # 9. Dashboard
    # ------------------------------------------------------------------ #
    h1(doc, "9. Dashboard et expérience utilisateur", page_break=False)
    h2(doc, "9.1 Navigation")
    table(
        doc,
        ["Menu", "Contenu", "Action principale"],
        [
            ["Vue d'ensemble", "KPI, courbe de charge, mix, régions, incidents récents.", "Comprendre la situation en 30 secondes."],
            ["Assistant agentique", "Formulaire, réponse, scores, trace, sources, export JSON.", "Poser une question métier complète."],
            ["MCP Playground", "Catalogue des 10 outils, formulaire d'appel, résultat JSON.", "Tester un outil et voir la latence."],
            ["Orchestration A2A", "AgentCards, formulaire, timeline, artifacts, logs.", "Lancer une collaboration multi-agents."],
            ["Statistiques", "Filtres, graphiques, tableau régional, benchmark Reflexion.", "Explorer les données et les scores."],
            ["Architecture", "Six schémas, ports, critères, manifests téléchargeables.", "Comprendre et auditer la solution."],
            ["Documentation", "DOCX, PDF, PPTX, captures, commandes.", "Récupérer les livrables."],
        ],
        widths=[3.3, 7.3, 5.6],
        font_size=7.9,
        caption="Tableau 20 — Structure du menu du dashboard.",
    )
    h2(doc, "9.2 Assistant agentique")
    para(
        doc,
        "Le formulaire demande une question, une région, un profil, un top-k, un seuil de qualité et un nombre "
        "d'itérations. Le résultat s'affiche en quatre onglets : réponse mise en forme, qualité et trace, sources, "
        "JSON brut. L'utilisateur voit immédiatement le score initial, le score final, le gain, le nombre d'outils "
        "appelés et la latence. C'est la preuve visible de la boucle Reflexion.",
    )
    h2(doc, "9.3 MCP Playground")
    para(
        doc,
        "Le playground présente les dix outils sous forme de cartes, puis un formulaire qui adapte les arguments "
        "à l'outil sélectionné. Le résultat brut est affiché en JSON, avec la source (MCP HTTP ou repli local), "
        "la latence et l'horodatage. Les derniers appels du serveur sont consultables dans un tableau.",
    )
    h2(doc, "9.4 Orchestration A2A")
    para(
        doc,
        "La page A2A montre les quatre AgentCards, leur port et leur statut. L'utilisateur saisit une tâche, "
        "choisit une région et un nombre maximum d'agents. Le résultat affiche le correlation_id, les agents "
        "mobilisés, la timeline, les artifacts et le journal des délégations.",
    )
    h2(doc, "9.5 Statistiques")
    para(
        doc,
        "La page statistiques propose un filtre par région et par fenêtre temporelle, six KPI, cinq graphiques "
        "(consommation mensuelle, mix, profil horaire, causes d'incidents, pertes vs SAIDI) et un tableau "
        "téléchargeable. Le benchmark Reflexion y est également visualisé.",
    )
    for path, caption in [
        (ROOT / "screenshots" / "home.png", "Figure 6 — Vue d'ensemble du dashboard."),
        (ROOT / "screenshots" / "assistant.png", "Figure 7 — Assistant agentique et scores Reflexion."),
        (ROOT / "screenshots" / "a2a.png", "Figure 8 — Orchestration A2A et timeline."),
        (ROOT / "screenshots" / "stats.png", "Figure 9 — Statistiques et benchmark."),
    ]:
        if path.exists():
            figure(doc, path, caption)
    h2(doc, "9.6 Design system")
    bullets(
        doc,
        [
            "Palette : navy #0A1F3C, ambre #F5B301, teal #16A6A1, bleu #3B82C4.",
            "Typographie : Inter pour l'interface, Aptos pour les documents.",
            "Logo : éclair dans un hexagone, symbole du réseau et de l'énergie.",
            "Composants : cartes KPI, badges de statut, timelines, tableaux zébrés.",
            "Accessibilité : contrastes élevés, libellés explicites, unités systématiques.",
            "Vidéo : videos/VOLTIS_Demo.mp4, 1 min 50, narration française, 8 séquences.",
        ],
    )

    # ------------------------------------------------------------------ #
    # 10. Docker
    # ------------------------------------------------------------------ #
    h1(doc, "10. Déploiement Docker", page_break=False)
    h2(doc, "10.1 Une image, trois services")
    para(
        doc,
        "Le Dockerfile unique construit une image Python 3.12 slim qui contient le dashboard, le serveur MCP, "
        "l'orchestrateur A2A et les agents. Docker Compose lance trois services : mcp (8100), a2a (8101-8105) et "
        "dashboard (8033). Le dashboard dépend des deux autres et attend leurs healthchecks.",
    )
    figure(doc, ASSETS / "docker_topology.png", "Figure 10 — Topologie Docker Compose et volume partagé.")
    table(
        doc,
        ["Service", "Commande", "Ports", "Healthcheck"],
        [
            ["mcp", "python main.py mcp", "8100", "/api/health"],
            ["a2a", "python main.py a2a", "8101-8105", "/health"],
            ["dashboard", "python main.py dashboard", "8033", "/_stcore/health"],
        ],
        widths=[3.0, 5.8, 3.4, 4.0],
        caption="Tableau 21 — Services Docker Compose.",
    )
    code_block(
        doc,
        """# Construction et démarrage
docker compose up --build

# Vérification
curl http://localhost:8033/_stcore/health
curl http://localhost:8100/api/health
curl http://localhost:8101/health

# Arrêt
docker compose down""",
        language="bash",
    )
    h2(doc, "10.2 Variables et volumes")
    bullets(
        doc,
        [
            "VOLTIS_MCP_URL et VOLTIS_A2A_URL pointent vers les services Docker.",
            "Le volume ./data est partagé en lecture/écriture pour les journaux et en lecture pour le dashboard.",
            "Les dossiers json/, docs/, presentation/, screenshots/ et assets/ sont montés en lecture seule.",
            "Le redémarrage est configuré en unless-stopped et les healthchecks protègent l'ordre de démarrage.",
        ],
    )
    h2(doc, "10.3 Mode local vs Docker")
    table(
        doc,
        ["Critère", "Local", "Docker"],
        [
            ["Démarrage", "python main.py", "docker compose up --build"],
            ["Python requis", "Oui (3.12+)", "Non, image fournie"],
            ["Services", "Trois processus locaux", "Trois conteneurs"],
            ["Données", "Dossiers du projet", "Volumes montés"],
            ["Usage", "Développement, démonstration", "Livraison, reproduction"],
        ],
        widths=[3.4, 6.2, 6.6],
        caption="Tableau 22 — Comparaison des deux modes de déploiement.",
    )

    # ------------------------------------------------------------------ #
    # 11. Tests
    # ------------------------------------------------------------------ #
    h1(doc, "11. Tests, évaluation et résultats", page_break=False)
    h2(doc, "11.1 Protocole")
    para(
        doc,
        "Cinq tâches représentatives couvrent les intentions du système : incident, mix, facturation, prévision et "
        "pertes. Chaque tâche est exécutée dans le graphe complet avec deux itérations forcées. Le Critic note le "
        "brouillon initial puis chaque réécriture. Les scores, la latence, le nombre de citations et les outils "
        "appelés sont enregistrés dans data/benchmarks.json.",
    )
    rows = [
        [
            task["id"], task["question"][:72] + "…",
            f"{task['initial']['overall']}", f"{task['final']['overall']}",
            f"+{task['gain']}", f"{task['elapsed_ms']:.0f}", str(task["citations"]),
        ]
        for task in bench["tasks"]
    ]
    table(
        doc,
        ["ID", "Tâche", "Initial", "Final", "Gain", "ms", "Cit."],
        rows,
        widths=[1.2, 9.4, 1.5, 1.5, 1.2, 1.4, 1.1],
        font_size=7.8,
        caption="Tableau 23 — Résultats du benchmark Reflexion sur cinq tâches.",
    )
    kpi_row(
        doc,
        [
            (f"{avg['initial']}/10", "score initial", "brouillon"),
            (f"{avg['final']}/10", "score final", "après 2 itérations"),
            (f"+{avg['gain']}", "gain moyen", "par tâche"),
            (f"{avg['latency_ms']:.0f} ms", "latence moyenne", "workflow complet"),
            (f"{avg['citations']}", "citations", "par réponse"),
        ],
    )
    h2(doc, "11.2 Gain par critère")
    criteria = ["clarity", "accuracy", "concision", "coherence"]
    labels = {"clarity": "Clarté", "accuracy": "Exactitude", "concision": "Concision", "coherence": "Cohérence"}
    criteria_rows = []
    for criterion in criteria:
        initial = statistics.mean(task["initial"]["scores"][criterion] for task in bench["tasks"])
        final = statistics.mean(task["final"]["scores"][criterion] for task in bench["tasks"])
        criteria_rows.append([labels[criterion], f"{initial:.1f}", f"{final:.1f}", f"+{final - initial:.1f}"])
    table(
        doc,
        ["Critère", "Initial", "Final", "Gain"],
        criteria_rows,
        widths=[5.0, 3.6, 3.6, 3.6],
        caption="Tableau 24 — Gain moyen par critère du Critic.",
    )
    para(
        doc,
        "Le gain le plus fort concerne l'exactitude : le brouillon initial cite peu de valeurs et de sources, "
        "tandis que la version raffinée ajoute les chiffres des outils et les références documentaires. La "
        "cohérence progresse grâce à la structure Synthèse / Analyse / Plan d'action / Limites / Sources. La "
        "concision reste stable car le Refiner évite les répétitions.",
    )
    h2(doc, "11.3 Tests d'interopérabilité")
    table(
        doc,
        ["Test", "Résultat", "Preuve"],
        [
            ["MCP tools/list", "10 outils retournés", "JSON-RPC /mcp"],
            ["MCP tools/call forecast_load", "Pointe et risque calculés", "structuredContent"],
            ["A2A discovery", "4 AgentCards en ligne", "GET /agents"],
            ["A2A orchestration", "2 à 4 agents, corrélation unique", "POST /orchestrate"],
            ["Dashboard → MCP", "Appel HTTP + latence", "MCP Playground"],
            ["Dashboard → A2A", "Timeline et artifacts", "Page Orchestration"],
            ["Repli local", "Fonctionne sans MCP/A2A", "Mode hors ligne"],
        ],
        widths=[5.0, 5.6, 5.6],
        font_size=8.0,
        caption="Tableau 25 — Tests d'interopérabilité et de robustesse.",
    )
    h2(doc, "11.4 Limites de l'évaluation")
    bullets(
        doc,
        [
            "Le Critic est déterministe et basé sur des règles : il ne remplace pas un juge LLM.",
            "Les cinq tâches sont représentatives mais ne couvrent pas toutes les intentions possibles.",
            "La latence mesurée est locale (quelques dizaines de ms) et n'inclut pas un appel LLM réel.",
            "Les données synthétiques limitent la portée des conclusions métier.",
            "Le benchmark force deux itérations ; en production, le seuil peut arrêter dès la première.",
        ],
    )

    # ------------------------------------------------------------------ #
    # 12. Sécurité & perspectives
    # ------------------------------------------------------------------ #
    h1(doc, "12. Sécurité, éthique, limites et perspectives", page_break=False)
    h2(doc, "12.1 Sécurité")
    table(
        doc,
        ["Risque", "Mesure dans VOLTIS", "Évolution production"],
        [
            ["Injection de prompt", "Périmètre d'outils limité, pas d'exécution arbitraire.", "Filtrage et garde-fous LLM."],
            ["Fuite de données", "Aucune donnée réelle, clients synthétiques.", "Chiffrement, masquage, RBAC."],
            ["Appel non autorisé", "Validation JSON Schema, liste d'outils.", "Bearer token, mTLS, rate limiting."],
            ["Hallucination", "Sources citées, score d'exactitude, limites explicites.", "Juge LLM et vérification factuelle."],
            ["Indisponibilité", "Repli local, healthchecks, redémarrage.", "Réplication et circuit breaker."],
        ],
        widths=[4.0, 7.4, 4.8],
        font_size=8.0,
        caption="Tableau 26 — Risques et mesures de maîtrise.",
    )
    h2(doc, "12.2 Données personnelles et éthique")
    para(
        doc,
        "Le projet n'utilise aucune donnée personnelle réelle. Les clients, les incidents et les consommations sont "
        "synthétiques. Les réponses indiquent explicitement leurs limites et ne se substituent pas à une décision "
        "d'exploitation. Un opérateur reste dans la boucle pour toute manœuvre, consignation ou décision client.",
    )
    h2(doc, "12.3 Limites")
    bullets(
        doc,
        [
            "Pas de connexion temps réel au SCADA ni aux compteurs communicants.",
            "Pas de modèle de prévision entraîné sur plusieurs années.",
            "Pas de base vectorielle : le retrieval TF-IDF reste lexical.",
            "Pas d'authentification ni de gestion multi-utilisateurs.",
            "Pas de haute disponibilité : la démo tourne sur une seule machine.",
        ],
    )
    h2(doc, "12.4 Perspectives")
    bullets(
        doc,
        [
            "Connecter MCP à un vrai référentiel de données et à un SCADA de test.",
            "Remplacer TF-IDF par des embeddings et une base vectorielle, en conservant BM25 en hybride.",
            "Ajouter un juge LLM et des tests de non-régression sur les réponses.",
            "Industrialiser l'observabilité : OpenTelemetry, traces distribuées, tableau de bord de qualité.",
            "Déployer sur Kubernetes avec authentification, quotas et isolation réseau.",
            "Étendre le hub à de nouveaux agents : marchés, efficacité énergétique, mobilité électrique.",
        ],
    )
    h2(doc, "12.5 Conclusion")
    para(
        doc,
        "VOLTIS démontre qu'une plateforme agentique peut être à la fois utile, traçable et démontrable. MCP "
        "standardise les outils, A2A organise la collaboration, le RAG apporte la connaissance et LangGraph "
        "orchestre la réflexion. Le dashboard 8033 rend le tout accessible, et Docker garantit la reproductibilité. "
        "Les cinq tâches de benchmark montrent un gain moyen de +2,92 points, avec des réponses plus précises, "
        "mieux structurées et systématiquement sourcées.",
    )

    # ------------------------------------------------------------------ #
    # Annexes
    # ------------------------------------------------------------------ #
    h1(doc, "Annexe A — Arborescence du projet", page_break=False)
    code_block(
        doc,
        """Agentic_AI_Electricity_FINAL/
├── main.py                     # lanceur unique (all, dashboard, mcp, a2a, demo, check)
├── dashboard/app.py            # dashboard Streamlit 8033
├── mcp_server/server.py        # serveur MCP 8100 (JSON-RPC + REST)
├── a2a/
│   ├── server.py               # orchestrateur 8101 + agents 8102-8105
│   ├── agents.py               # logique des 4 agents
│   └── agent_cards/            # 5 AgentCards JSON
├── langgraph_workflow/
│   └── workflow.py             # graphe Planner → Critic → Refiner
├── shared/electricity_core.py  # RAG, KPI, outils, simulations
├── data/                       # CSV, JSON, corpus Markdown
├── json/                       # manifests MCP, A2A, RAG, LangGraph, architecture
├── docs/                       # DOCX + PDF
├── presentation/               # PPTX + PDF
├── assets/                     # logo et 6 schémas
├── screenshots/                # captures du dashboard
├── scripts/                    # build_data, build_json, build_docs, build_deck…
├── Dockerfile
├── docker-compose.yml
└── requirements.txt""",
        language="text",
        font_size=7.2,
    )
    h1(doc, "Annexe B — Commandes", page_break=False)
    code_block(
        doc,
        """# Installation
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt

# Lancement complet
python main.py

# Services séparés
python main.py dashboard      # 8033
python main.py mcp            # 8100
python main.py a2a            # 8101-8105

# Démonstration et validation
python main.py demo
python main.py check

# Régénération des livrables
python main.py build

# Docker
docker compose up --build""",
        language="bash",
    )
    h1(doc, "Annexe C — Manifests JSON", page_break=False)
    table(
        doc,
        ["Fichier", "Contenu"],
        [
            ["mcp_manifest.json", "Serveur, 10 outils, ressources, prompts, exemples JSON-RPC."],
            ["a2a_manifest.json", "Protocole, orchestrateur, 4 agents, flux, observabilité, sécurité."],
            ["rag_manifest.json", "Corpus, chunking, retriever, boucle agentique, évaluation."],
            ["langgraph_manifest.json", "Nœuds, arêtes, état, pondérations, commandes."],
            ["architecture_manifest.json", "Couches, services, flux, ADR, critères de validation."],
            ["agentic_ai_electricity_full.json", "Vue consolidée de tous les manifests et benchmarks."],
        ],
        widths=[5.6, 10.6],
        caption="Tableau 27 — Livrables JSON.",
    )
    h1(doc, "Annexe D — Glossaire", page_break=False)
    table(
        doc,
        ["Terme", "Définition"],
        [
            ["MCP", "Model Context Protocol : standard de découverte et d'appel d'outils par un agent."],
            ["A2A", "Agent-to-Agent : protocole de découverte, délégation et collaboration entre agents."],
            ["AgentCard", "Carte d'identité d'un agent : nom, description, compétences, endpoint."],
            ["RAG", "Retrieval-Augmented Generation : ancrer la génération dans des documents."],
            ["Reflexion", "Pattern Generate → Critic → Refine avec mesure du gain."],
            ["LangGraph", "Bibliothèque de graphes d'états pour orchestrer des agents."],
            ["SAIDI", "Durée moyenne de coupure par client sur une période."],
            ["SAIFI", "Nombre moyen de coupures par client sur une période."],
            ["MTTR", "Durée moyenne de réparation d'un incident."],
            ["correlation_id", "Identifiant unique qui relie toutes les étapes d'une même tâche."],
        ],
        widths=[3.4, 12.8],
        caption="Tableau 28 — Glossaire.",
    )
    h1(doc, "Annexe E — Références", page_break=False)
    bullets(
        doc,
        [
            "Model Context Protocol, spécification 2025-06-18 — modelcontextprotocol.io.",
            "Agent-to-Agent Protocol 0.3 — a2a-protocol.org.",
            "LangGraph, documentation officielle — langchain-ai.github.io/langgraph.",
            "Streamlit, documentation officielle — docs.streamlit.io.",
            "Docker Compose, documentation officielle — docs.docker.com/compose.",
            "Plotly, documentation officielle — plotly.com/python.",
        ],
    )
    para(
        doc,
        "Fin du document. VOLTIS v1.0.0 — 12 novembre 2026.",
        size=8,
        italic=True,
    )

    doc.save(OUT)
    return OUT


def export_pdf(docx_path: Path) -> None:
    try:
        import shutil
        import uuid

        import win32com.client  # type: ignore

        temp = docx_path.with_name(f"_export_{uuid.uuid4().hex[:6]}.docx")
        shutil.copy2(docx_path, temp)
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        document = word.Documents.Open(str(temp))
        document.Fields.Update()
        for index in range(1, document.TablesOfContents.Count + 1):
            document.TablesOfContents(index).Update()
        document.Repaginate()
        document.ExportAsFixedFormat(str(PDF), 17)  # wdExportFormatPDF
        document.Close(False)
        word.Quit()
        temp.unlink(missing_ok=True)
        print("PDF généré :", PDF)
    except Exception as error:
        print("Export PDF indisponible :", error)


if __name__ == "__main__":
    path = build()
    print("Documentation générée :", path)
    print("Taille :", round(path.stat().st_size / 1024, 1), "Ko")
    export_pdf(path)
