# -*- coding: utf-8 -*-
"""Génère les livrables JSON : manifests MCP, A2A, RAG, LangGraph, architecture,
AgentCards et rapport de benchmark Reflexion."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langgraph_workflow import graph_spec, run_workflow  # noqa: E402
from shared import electricity_core as core  # noqa: E402

JSON_DIR = ROOT / "json"
CARDS_DIR = JSON_DIR / "agent_cards"
A2A_CARDS = ROOT / "a2a" / "agent_cards"
DATA = ROOT / "data"


def write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def agent_card(agent_id: str) -> dict:
    info = core.AGENT_CAPABILITIES[agent_id]
    port = info["port"]
    return {
        "name": info["label"],
        "description": info["description"],
        "url": f"http://127.0.0.1:{port}",
        "version": "1.0.0",
        "protocolVersion": "0.3.0",
        "provider": {"organization": "VOLTIS", "url": "http://localhost:8033"},
        "documentationUrl": f"http://localhost:8033/?page=a2a&agent={agent_id}",
        "capabilities": {"streaming": False, "pushNotifications": False, "stateTransitionHistory": True},
        "defaultInputModes": ["text/plain", "application/json"],
        "defaultOutputModes": ["text/markdown", "application/json"],
        "skills": [
            {
                "id": f"{agent_id}.main",
                "name": info["label"],
                "description": info["description"],
                "tags": info["keywords"][:6],
                "examples": _examples(agent_id),
                "inputModes": ["text/plain"],
                "outputModes": ["text/markdown", "application/json"],
            }
        ],
        "metadata": {
            "agent_id": agent_id,
            "tools": info["tools"],
            "keywords": info["keywords"],
            "port": port,
            "hub": "VOLTIS Agentic Hub",
            "owner": "Direction Digitale & Exploitation",
        },
    }


def _examples(agent_id: str) -> list[str]:
    return {
        "grid-analyst": [
            "Quel est le mix de production national ?",
            "Donne-moi le profil de la région Casablanca-Settat.",
            "Quelle est la consommation mensuelle du réseau ?",
        ],
        "outage-inspector": [
            "Pourquoi Maârif a subi une coupure hier soir ?",
            "Combien d'incidents P1 sur les 90 derniers jours ?",
            "Quel est le SAIDI de la région Oriental ?",
        ],
        "billing-advisor": [
            "Simule la facture d'un industriel à 250 MWh.",
            "Comment réduire la facture du client CLI-001 ?",
            "Explique les tranches du tarif résidentiel.",
        ],
        "forecast-agent": [
            "Quel est le risque de surcharge demain à 19 h ?",
            "Prévois la pointe de Casablanca avec +5 °C.",
            "Quelle réserve faut-il mobiliser demain ?",
        ],
    }[agent_id]


def build_agent_cards() -> list[dict]:
    cards = []
    for agent_id in core.AGENT_CAPABILITIES:
        card = agent_card(agent_id)
        cards.append(card)
        write(CARDS_DIR / f"{agent_id}.json", card)
        write(A2A_CARDS / f"{agent_id}.json", card)
    orchestrator = {
        "name": "VOLTIS Orchestrator",
        "description": "Hub agentique : découvre les AgentCards, sélectionne les spécialistes, délègue en parallèle et agrège les résultats.",
        "url": "http://127.0.0.1:8101",
        "version": "1.0.0",
        "protocolVersion": "0.3.0",
        "provider": {"organization": "VOLTIS"},
        "capabilities": {"streaming": False, "pushNotifications": False, "stateTransitionHistory": True},
        "defaultInputModes": ["text/plain", "application/json"],
        "defaultOutputModes": ["text/markdown", "application/json"],
        "skills": [
            {
                "id": "orchestrator.discover",
                "name": "Découverte A2A",
                "description": "Interroge les AgentCards et sélectionne les agents selon la capacité demandée.",
                "tags": ["discovery", "agent-card", "routing"],
                "examples": ["Trouve les agents capables de diagnostiquer une coupure."],
                "inputModes": ["text/plain"],
                "outputModes": ["application/json"],
            },
            {
                "id": "orchestrator.delegate",
                "name": "Délégation parallèle",
                "description": "Envoie une tâche à plusieurs agents avec un correlation_id unique et agrège les artefacts.",
                "tags": ["delegation", "correlation-id", "aggregation"],
                "examples": ["Analyse la coupure de Maârif et propose un plan d'action."],
                "inputModes": ["text/plain", "application/json"],
                "outputModes": ["application/json"],
            },
        ],
        "metadata": {
            "agent_id": "orchestrator",
            "port": 8101,
            "card_url": "http://127.0.0.1:8101/.well-known/agent.json",
            "discovery": "http://127.0.0.1:8101/agents",
            "orchestrate": "http://127.0.0.1:8101/orchestrate",
        },
    }
    write(CARDS_DIR / "orchestrator.json", orchestrator)
    write(A2A_CARDS / "orchestrator.json", orchestrator)
    return cards


def build_mcp_manifest() -> dict:
    manifest = core.mcp_manifest()
    manifest["project"] = {
        "name": "VOLTIS",
        "tagline": "Agentic AI for the Electricity Sector",
        "version": "1.0.0",
        "owner": "Direction Digitale & Exploitation",
        "date": "2026-11-12",
    }
    manifest["usage"] = {
        "start": "python main.py mcp",
        "docker": "docker compose up mcp",
        "health": "curl http://127.0.0.1:8100/api/health",
        "tools_list": "curl http://127.0.0.1:8100/api/tools",
        "call_example": {
            "method": "POST",
            "url": "http://127.0.0.1:8100/api/tool",
            "body": {"tool": "forecast_load", "arguments": {"region_code": "CAS", "horizon_h": 24, "temperature_delta": 5}},
        },
        "jsonrpc_example": {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "get_grid_kpis", "arguments": {}},
        },
    }
    manifest["examples"] = [
        {"question": "Quel est le mix national ?", "tool": "get_production_mix", "arguments": {}},
        {"question": "Incidents à Casablanca ?", "tool": "query_outages", "arguments": {"region_code": "CAS", "limit": 5}},
        {"question": "Facture d'un industriel à 250 MWh ?", "tool": "simulate_bill", "arguments": {"segment": "industriel", "consumption_mwh": 250}},
        {"question": "Risque demain à 19 h avec +5 °C ?", "tool": "forecast_load", "arguments": {"region_code": "CAS", "temperature_delta": 5}},
    ]
    write(JSON_DIR / "mcp_manifest.json", manifest)
    return manifest


def build_a2a_manifest(cards: list[dict]) -> dict:
    manifest = {
        "schema": "volt-is.a2a/1.0",
        "protocol": {
            "name": "Agent-to-Agent (A2A)",
            "version": "0.3.0",
            "transport": "HTTP + JSON",
            "message_format": "JSON-RPC 2.0 compatible",
            "discovery": "AgentCard sur /.well-known/agent.json",
            "correlation": "correlation_id UUID v4 propagé à chaque délégation",
            "endpoints": {
                "orchestrator": "http://127.0.0.1:8101",
                "discover": "http://127.0.0.1:8101/discover",
                "agents": "http://127.0.0.1:8101/agents",
                "orchestrate": "http://127.0.0.1:8101/orchestrate",
            },
        },
        "orchestrator": {
            "agent_id": "orchestrator",
            "label": "VOLTIS Orchestrator",
            "port": 8101,
            "role": "Découverte, sélection, délégation parallèle, agrégation et traçabilité.",
            "strategy": "Score de correspondance entre la question et les mots-clés/capacités des AgentCards ; 1 à 3 agents selon l'intention.",
        },
        "agents": [
            {
                "agent_id": card["metadata"]["agent_id"],
                "label": card["name"],
                "port": card["metadata"]["port"],
                "url": card["url"],
                "card_url": f"{card['url']}/.well-known/agent.json",
                "message_url": f"{card['url']}/message",
                "skills": [skill["id"] for skill in card["skills"]],
                "tools": card["metadata"]["tools"],
                "keywords": card["metadata"]["keywords"],
                "card": card,
            }
            for card in cards
        ],
        "flows": [
            {
                "name": "Découverte",
                "steps": ["GET /.well-known/agent.json (orchestrateur)", "GET /agents", "Filtrer par capacité", "Retourner les cartes"],
            },
            {
                "name": "Délégation",
                "steps": [
                    "POST /orchestrate {question, region_code}",
                    "Générer correlation_id",
                    "POST /message sur chaque agent retenu",
                    "Recevoir les artifacts",
                    "AgrégER et journaliser",
                ],
            },
            {
                "name": "Agrégation",
                "steps": ["Fusionner les artifacts", "Dédupliquer les sources", "Produire la réponse finale", "Exposer la timeline"],
            },
        ],
        "observability": {
            "log_file": "data/a2a_delegations.jsonl",
            "fields": ["correlation_id", "timestamp", "orchestrator", "agent_id", "status", "latency_ms", "task", "artifact_summary"],
            "metrics": ["taux de succès", "latence P50/P95", "nombre de délégations par agent", "taux d'escalade"],
        },
        "security": {
            "authentication": "jeton Bearer en production (désactivé en démo locale)",
            "authorization": "liste blanche des agents par capability",
            "pii": "aucune donnée personnelle réelle ; clients synthétiques",
            "audit": "chaque message conserve correlation_id et horodatage",
        },
        "examples": [
            {
                "question": "Analyse la coupure de Maârif et propose un plan d'action.",
                "selected_agents": ["outage-inspector", "forecast-agent", "billing-advisor"],
                "correlation_id": "a2a-demo-0001",
            },
            {
                "question": "Quel est le mix national et le risque de pointe demain ?",
                "selected_agents": ["grid-analyst", "forecast-agent"],
                "correlation_id": "a2a-demo-0002",
            },
        ],
    }
    write(JSON_DIR / "a2a_manifest.json", manifest)
    return manifest


def build_rag_manifest() -> dict:
    documents = core.corpus()
    chunks = sum(len(document["chunks"]) for document in documents)
    sample = core.search_documents("procédure de délestage en cas de pointe", 3)
    manifest = {
        "schema": "volt-is.rag/1.0",
        "name": "Agentic RAG VOLTIS",
        "description": "RAG hybride agentique : planification de requête, retrieval multi-étapes, vérification de suffisance, synthèse sourcée et auto-critique.",
        "corpus": {
            "documents": len(documents),
            "chunks": chunks,
            "languages": ["fr"],
            "domains": ["exploitation", "maintenance", "commercial", "réglementation", "cybersécurité", "sécurité"],
            "source": "data/corpus/*.md + data/corpus.json",
            "documents_index": [
                {
                    "doc_id": document["doc_id"],
                    "title": document["title"],
                    "category": document["category"],
                    "version": document["version"],
                    "date": document["date"],
                    "chunks": len(document["chunks"]),
                    "keywords": document["keywords"],
                }
                for document in documents
            ],
        },
        "chunking": {
            "strategy": "article-based",
            "chunk_size_tokens": [60, 120],
            "overlap_tokens": 0,
            "metadata": ["doc_id", "title", "category", "version", "date", "owner", "article"],
        },
        "retriever": {
            "type": "hybride",
            "lexical": {"algorithm": "BM25", "k1": 1.5, "b": 0.75},
            "semantic": {"algorithm": "TF-IDF cosinus", "vocabulary": "corpus", "normalization": "NFKD + stopwords FR"},
            "fusion": {"bm25_weight": 0.66, "tfidf_weight": 0.86, "title_bonus": 0.08, "phrase_bonus": 0.12},
            "top_k_default": 4,
            "query_expansion": "synonymes métier (coupure → incident, facture → tarif, …)",
        },
        "agentic_loop": {
            "steps": ["Analyser la question", "Planifier les recherches", "Retriever", "Vérifier la suffisance", "Reformuler si besoin", "Synthétiser", "Citer", "Critiquer"],
            "max_reformulations": 2,
            "sufficiency_threshold": 0.55,
            "citation_policy": "Chaque affirmation chiffrée ou normative est associée à une référence [n] et à un document versionné.",
        },
        "evaluation": {
            "metrics": ["precision@k", "recall@k", "taux de citation", "faithfulness", "latence"],
            "sample_query": sample["query"],
            "sample_results": sample["results"],
        },
        "examples": [
            "Quelle est la procédure de délestage ?",
            "Quelles sont les tolérances de tension en BT ?",
            "Comment réduire les pertes non techniques ?",
        ],
    }
    write(JSON_DIR / "rag_manifest.json", manifest)
    return manifest


def build_langgraph_manifest() -> dict:
    spec = graph_spec()
    spec["project"] = "VOLTIS"
    spec["nodes_detail"] = [
        {"id": "planner", "inputs": ["question", "region_code"], "outputs": ["intent", "plan", "tool_names"], "latency_ms": 2},
        {"id": "retrieve", "inputs": ["question", "intent", "top_k"], "outputs": ["sources"], "latency_ms": 4},
        {"id": "tools", "inputs": ["tool_names", "region_code"], "outputs": ["tool_results", "tool_trace"], "latency_ms": 6},
        {"id": "writer", "inputs": ["sources", "tool_results", "intent"], "outputs": ["draft"], "latency_ms": 3},
        {"id": "critic", "inputs": ["draft"], "outputs": ["critique", "score_history"], "latency_ms": 2},
        {"id": "refine", "inputs": ["draft", "critique", "sources"], "outputs": ["draft", "iterations"], "latency_ms": 3},
        {"id": "finalize", "inputs": ["draft", "critique"], "outputs": ["final_answer", "confidence", "elapsed_ms"], "latency_ms": 1},
    ]
    spec["state_schema"] = {
        "question": "str",
        "region_code": "str",
        "audience": "str",
        "top_k": "int",
        "threshold": "float",
        "max_iterations": "int",
        "intent": "str",
        "plan": "list[str]",
        "tool_names": "list[str]",
        "sources": "list[Source]",
        "tool_results": "dict[str, Any]",
        "tool_trace": "list[ToolCall]",
        "draft": "str",
        "critique": "dict",
        "score_history": "list[Score]",
        "iterations": "int",
        "trace": "list[TraceStep]",
        "final_answer": "str",
        "confidence": "str",
    }
    spec["commands"] = {
        "run": "python main.py demo",
        "single": "python -m langgraph_workflow.workflow",
        "test": "python -m pytest tests/ -q",
    }
    write(JSON_DIR / "langgraph_manifest.json", spec)
    return spec


def build_architecture_manifest() -> dict:
    manifest = {
        "schema": "volt-is.architecture/1.0",
        "project": "VOLTIS — Agentic AI for the Electricity Sector",
        "style": "Hub agentique interopérable (MCP + A2A + RAG + LangGraph)",
        "principles": [
            "Séparer les protocoles (MCP pour les outils, A2A pour les agents)",
            "Un hub central qui découvre les capacités sans couplage fort",
            "Toute réponse chiffrée est sourcée et traçable",
            "Boucle Reflexion avant toute réponse finale",
            "Repli local si un service est indisponible",
            "Aucune donnée personnelle réelle",
        ],
        "layers": [
            {
                "id": "experience",
                "label": "Expérience",
                "components": ["Dashboard Streamlit 8033", "Formulaire de requête", "Graphiques & KPI", "Documentation"],
            },
            {
                "id": "orchestration",
                "label": "Orchestration",
                "components": ["LangGraph StateGraph", "Planner", "Critic / Refiner", "A2A Orchestrator 8101"],
            },
            {
                "id": "agents",
                "label": "Agents spécialisés",
                "components": ["Grid Analyst 8102", "Outage Inspector 8103", "Billing Advisor 8104", "Forecast Agent 8105"],
            },
            {
                "id": "protocols",
                "label": "Protocoles",
                "components": ["MCP JSON-RPC 2.0 8100", "A2A 0.3 8101-8105", "AgentCards", "correlation_id"],
            },
            {
                "id": "data",
                "label": "Données & connaissances",
                "components": ["12 documents / 58 chunks", "RAG hybride BM25 + TF-IDF", "CSV/JSON synthétiques", "Journal A2A JSONL"],
            },
            {
                "id": "infrastructure",
                "label": "Infrastructure",
                "components": ["Docker", "docker-compose", "Healthchecks", "Variables d'environnement"],
            },
        ],
        "services": [
            {"name": "dashboard", "port": 8033, "image": "volt-is:1.0", "command": "python main.py dashboard", "depends_on": ["mcp", "a2a"]},
            {"name": "mcp", "port": 8100, "image": "volt-is:1.0", "command": "python main.py mcp", "health": "/api/health"},
            {"name": "a2a", "ports": [8101, 8102, 8103, 8104, 8105], "image": "volt-is:1.0", "command": "python main.py a2a", "health": "/health"},
        ],
        "data_flows": [
            {"from": "dashboard", "to": "langgraph", "payload": "question + contexte", "protocol": "in-process"},
            {"from": "langgraph", "to": "mcp", "payload": "tool_name + arguments", "protocol": "HTTP/JSON-RPC"},
            {"from": "langgraph", "to": "a2a", "payload": "tâche + correlation_id", "protocol": "HTTP/JSON"},
            {"from": "a2a", "to": "agents", "payload": "message/send", "protocol": "A2A 0.3"},
            {"from": "agents", "to": "data", "payload": "lecture KPI/corpus", "protocol": "Python"},
            {"from": "dashboard", "to": "user", "payload": "réponse + sources + scores", "protocol": "HTTPS/SSE"},
        ],
        "adr": [
            {"id": "ADR-001", "decision": "MCP pour les outils", "why": "Découverte automatique et schémas JSON standardisés."},
            {"id": "ADR-002", "decision": "A2A pour les agents", "why": "Délégation inter-agents, AgentCards, traçabilité par correlation_id."},
            {"id": "ADR-003", "decision": "RAG hybride sans vector DB", "why": "Démo reproductible hors ligne, latence faible, pas de dépendance externe."},
            {"id": "ADR-004", "decision": "LangGraph pour l'orchestration", "why": "Graphe explicite, état typé, boucle conditionnelle Reflexion."},
            {"id": "ADR-005", "decision": "Streamlit pour le dashboard", "why": "Livraison rapide, formulaires, graphiques Plotly, mode local."},
        ],
        "validation_criteria": [
            {"criterion": "Interopérabilité", "proof": "MCP JSON-RPC + A2A HTTP + AgentCards ; dashboard appelle les deux."},
            {"criterion": "Agentic RAG", "proof": "Planner + retriever multi-étapes + vérification + citations + critique."},
            {"criterion": "Collaboration ≥ 2 agents", "proof": "Orchestrateur A2A délègue à 2-3 agents en parallèle."},
            {"criterion": "Auto-réflexion", "proof": "Boucle Writer → Critic → Refiner avec scores avant/après."},
            {"criterion": "Architecture", "proof": "Schéma du hub, 3 couches, ports et flux documentés."},
            {"criterion": "Documentation", "proof": "DOCX final, README, guide, 5 AgentCards complètes."},
            {"criterion": "Démonstration", "proof": "Dashboard live 8033 + scénario de bout en bout + captures."},
        ],
        "ports": {"dashboard": 8033, "mcp": 8100, "a2a_orchestrator": 8101, "grid-analyst": 8102, "outage-inspector": 8103, "billing-advisor": 8104, "forecast-agent": 8105},
    }
    write(JSON_DIR / "architecture_manifest.json", manifest)
    return manifest


def build_benchmarks() -> dict:
    rows = []
    for task in core.benchmark_tasks():
        started = time.perf_counter()
        result = run_workflow(task["question"], task["region_code"], max_iterations=2, threshold=9.9)
        elapsed = round((time.perf_counter() - started) * 1000, 1)
        history = result["score_history"]
        initial = history[0]
        final = history[-1]
        rows.append(
            {
                "id": task["id"],
                "question": task["question"],
                "region_code": task["region_code"],
                "intent": result["intent"],
                "tools": [row["tool"] for row in result["tool_trace"]],
                "sources": [source["citation"] for source in result["sources"]],
                "initial": {
                    "overall": initial["overall"],
                    "scores": initial["scores"],
                    "issues": initial["issues"],
                },
                "iterations": [
                    {"label": item["label"], "overall": item["overall"], "scores": item["scores"]}
                    for item in history
                ],
                "final": {
                    "overall": final["overall"],
                    "scores": final["scores"],
                    "confidence": result.get("confidence", "Haute"),
                },
                "gain": round(final["overall"] - initial["overall"], 1),
                "elapsed_ms": elapsed,
                "words": final["words"],
                "citations": final["citations"],
            }
        )
    averages = {
        "initial": round(sum(row["initial"]["overall"] for row in rows) / len(rows), 2),
        "final": round(sum(row["final"]["overall"] for row in rows) / len(rows), 2),
        "gain": round(sum(row["gain"] for row in rows) / len(rows), 2),
        "latency_ms": round(sum(row["elapsed_ms"] for row in rows) / len(rows), 1),
        "citations": round(sum(row["citations"] for row in rows) / len(rows), 1),
    }
    payload = {
        "schema": "volt-is.benchmark/1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "protocol": {
            "tasks": 5,
            "iterations": 2,
            "threshold": 9.9,
            "method": "Chaque tâche est exécutée dans le graphe LangGraph complet ; le Critic note le brouillon initial puis chaque réécriture.",
            "criteria": ["clarté", "exactitude", "concision", "cohérence"],
            "scale": "0-10",
        },
        "tasks": rows,
        "averages": averages,
    }
    write(DATA / "benchmarks.json", payload)
    write(JSON_DIR / "benchmarks.json", payload)
    return payload


def build_full_manifest(mcp, a2a, rag, graph, arch, cards, benchmark) -> None:
    payload = {
        "schema": "volt-is.agentic-ai/1.0",
        "project": {
            "name": "VOLTIS",
            "tagline": "Agentic AI for the Electricity Sector",
            "version": "1.0.0",
            "date": "2026-11-12",
            "author": "Direction Digitale & Exploitation — VOLTIS",
            "dashboard": "http://localhost:8033",
        },
        "data": {
            "mode": "synthetic",
            "real_api": False,
            "generator": "scripts/build_data.py",
            "seed": 20261112,
            "note": "Aucune API réelle ONEE / ANRE / SCADA / AMI ; aucun client réel.",
        },
        "mcp": mcp,
        "a2a": a2a,
        "rag": rag,
        "langgraph": graph,
        "architecture": arch,
        "agent_cards": cards,
        "benchmarks": benchmark,
    }
    write(JSON_DIR / "agentic_ai_electricity_full.json", payload)


def main() -> None:
    print("Construction des manifests JSON…")
    cards = build_agent_cards()
    mcp = build_mcp_manifest()
    a2a = build_a2a_manifest(cards)
    rag = build_rag_manifest()
    graph = build_langgraph_manifest()
    arch = build_architecture_manifest()
    benchmark = build_benchmarks()
    build_full_manifest(mcp, a2a, rag, graph, arch, cards, benchmark)
    print(f"  - {len(cards) + 1} AgentCards")
    print(f"  - {len(mcp['tools'])} outils MCP")
    print(f"  - {len(a2a['agents'])} agents A2A")
    print(f"  - {rag['corpus']['documents']} documents / {rag['corpus']['chunks']} chunks")
    print(f"  - benchmark moyen : {benchmark['averages']['initial']} → {benchmark['averages']['final']} "
          f"(+{benchmark['averages']['gain']}) en {benchmark['averages']['latency_ms']} ms")
    print("JSON générés dans", JSON_DIR)


if __name__ == "__main__":
    main()
