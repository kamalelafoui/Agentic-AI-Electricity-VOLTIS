# -*- coding: utf-8 -*-
"""Génère le workflow Langflow final Agentic_AI_Electricity_VOLTIS.json.

Le fichier est basé sur un export Langflow réel (ChatInput → Agent → MCP Tools →
ChatOutput) et enrichi avec les métadonnées MCP / A2A / RAG / LangGraph du projet.
"""
from __future__ import annotations

import copy
import json
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path(r"C:\Users\HP\Downloads\Semaine 7\Projet_jour33\j33_MCP.json")
OUT_JSON = ROOT / "json" / "Agentic_AI_Electricity_VOLTIS.json"
OUT_ROOT = ROOT / "Agentic_AI_Electricity_VOLTIS.json"

SYSTEM_PROMPT = """Tu es l'agent VOLTIS, expert du réseau électrique marocain.
Tu disposes de dix outils MCP : KPI réseau, profil régional, consommation, mix de production,
incidents, prévision de charge, simulation de facture, recherche documentaire, économies
d'énergie et qualité de service.

Règles de réponse :
1. Analyse la question et choisis le ou les outils MCP pertinents.
2. Pour toute règle, procédure ou référence, utilise search_knowledge et cite la source
   sous la forme [DOC-XX · vX.Y · article N].
3. Donne toujours les chiffres avec leur unité (GWh, MW, MAD, min, %).
4. Structure la réponse : Synthèse, Analyse, Plan d'action, Limites, Sources.
5. Applique la boucle Reflexion : génère un brouillon, critique-le sur la clarté,
   l'exactitude, la concision et la cohérence, puis raffine avant de répondre.
6. Si la question concerne plusieurs expertises (incident + prévision + facture),
   explique que l'orchestrateur A2A peut déléguer aux agents Grid Analyst,
   Outage Inspector, Billing Advisor et Forecast Agent.
7. Ne jamais inventer une donnée absente des outils ou du corpus.
8. Termine par un niveau de confiance : Haute, Moyenne ou À vérifier.
"""

ARCH_NOTE = """# ⚡ VOLTIS — Agentic AI for the Electricity Sector

## Objectif
Répondre à des questions métier sur le réseau électrique en combinant **données structurées**,
**procédures internes** et **outils MCP**, avec des réponses chiffrées, sourcées et critiquées.

## Architecture du workflow
**Chat Input** → **Agent VOLTIS** → **MCP Tools** (10 outils) → **Chat Output**

### Les 10 outils MCP
1. `get_grid_kpis` — KPI nationaux
2. `get_region_profile` — profil d'une région
3. `get_consumption` — série mensuelle
4. `get_production_mix` — mix et CO₂
5. `query_outages` — incidents et continuité
6. `forecast_load` — pointe, marge, risque
7. `simulate_bill` — facture et tranches
8. `search_knowledge` — RAG hybride BM25 + TF-IDF
9. `recommend_energy_savings` — plan d'économies
10. `get_service_quality` — SAIDI / SAIFI

## Serveur MCP
- **Nom :** `volt-is-grid-mcp`
- **Transport :** SSE
- **URL locale :** `http://127.0.0.1:8100/sse`
- **Health :** `http://127.0.0.1:8100/api/health`
- **JSON-RPC :** `http://127.0.0.1:8100/mcp`

## Lancement
```bash
python main.py mcp        # serveur MCP 8100
python main.py dashboard  # dashboard 8033
python main.py a2a        # orchestrateur 8101 + agents 8102-8105
```

## Données
8 régions · 42,3 TWh · 9,25 M clients · 72 incidents · 12 documents / 49 chunks.
Données **100 % synthétiques**, aucun client réel.
"""

A2A_NOTE = """# 🤝 A2A — Orchestrateur et agents spécialisés

Le hub A2A complète MCP : MCP expose les **outils**, A2A fait collaborer les **agents**.

## Orchestrateur
- **URL :** `http://127.0.0.1:8101`
- **Discovery :** `GET /agents`
- **Délégation :** `POST /orchestrate`
- **Corrélation :** `correlation_id` propagé dans `data/a2a_delegations.jsonl`

## Agents
| Agent | Port | Expertise |
|---|---|---|
| Grid Analyst | 8102 | KPI, consommation, mix |
| Outage Inspector | 8103 | incidents, SAIDI/SAIFI, MTTR |
| Billing Advisor | 8104 | factures, tarifs, compensation |
| Forecast Agent | 8105 | prévision, pointe, réserve |

Chaque agent publie une **AgentCard** sur `/.well-known/agent.json` et accepte
`POST /message`. L'orchestrateur sélectionne **2 à 4 agents** selon l'intention.
"""

REFLEXION_NOTE = """# 🔁 Reflexion — Generate → Critic → Refine

Le workflow applique une boucle d'auto-amélioration mesurée :

1. **Generate** : l'agent produit un brouillon à partir des outils et des sources.
2. **Critic** : notation sur 10 — clarté 28 %, exactitude 34 %, concision 14 %, cohérence 24 %.
3. **Refine** : réécriture avec sources, plan d'action, limites et indicateurs.

**Seuil de publication :** 8,2/10 · **max 2 itérations**.
**Benchmark :** 6,48/10 → 9,40/10 (+2,92 pts) sur 5 tâches.
"""


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:5]}"


def main() -> None:
    if not TEMPLATE.exists():
        print("Template Langflow introuvable ; le JSON existant est conservé.")
        print("Fichier attendu :", TEMPLATE)
        return
    data = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    flow = copy.deepcopy(data)

    flow_id = str(uuid.uuid4())
    flow["name"] = "Agentic_AI_Electricity_VOLTIS"
    flow["description"] = (
        "VOLTIS — hub agentique pour le secteur électrique : MCP (10 outils), RAG hybride, "
        "A2A (4 agents), LangGraph Reflexion, dashboard Streamlit 8033 et Docker."
    )
    flow["endpoint_name"] = "volt-is-electricity"
    flow["id"] = flow_id
    flow["is_component"] = False
    flow["last_tested_version"] = "1.7.0"
    flow["tags"] = ["agentic-ai", "electricity", "mcp", "a2a", "rag", "reflexion", "langflow"]

    nodes = {node["data"]["id"]: node for node in flow["data"]["nodes"]}
    chat_input = nodes["ChatInput-SKkmF"]
    agent = nodes["Agent-OK5xe"]
    mcp_tools = nodes["MCPTools-bjGIY"]
    chat_output = nodes["ChatOutput-KyMDv"]
    note = nodes["note-P2cYM"]

    # Identifiants lisibles
    chat_input["data"]["id"] = "ChatInput-VOLTIS"
    chat_input["id"] = "ChatInput-VOLTIS"
    agent["data"]["id"] = "Agent-VOLTIS"
    agent["id"] = "Agent-VOLTIS"
    mcp_tools["data"]["id"] = "MCPTools-VOLTIS"
    mcp_tools["id"] = "MCPTools-VOLTIS"
    chat_output["data"]["id"] = "ChatOutput-VOLTIS"
    chat_output["id"] = "ChatOutput-VOLTIS"
    note["data"]["id"] = "note-ARCH"
    note["id"] = "note-ARCH"

    # Positions
    chat_input["position"] = {"x": 900, "y": 300}
    mcp_tools["position"] = {"x": 900, "y": 90}
    agent["position"] = {"x": 1220, "y": 300}
    chat_output["position"] = {"x": 1560, "y": 300}
    note["position"] = {"x": 80, "y": 40}
    note["measured"] = {"height": 1000, "width": 640}

    # Chat Input
    chat_input["data"]["node"]["display_name"] = "Question · VOLTIS"
    chat_input["data"]["node"]["description"] = "Question métier sur le réseau électrique."
    chat_input["data"]["node"]["template"]["input_value"]["value"] = (
        "Analyse la coupure du quartier Maârif hier soir et propose un plan d'action priorisé."
    )
    chat_input["data"]["node"]["template"]["sender_name"]["value"] = "Utilisateur VOLTIS"

    # Agent
    agent_node = agent["data"]["node"]
    agent_node["display_name"] = "Agent VOLTIS · MCP + RAG + Reflexion"
    agent_node["description"] = (
        "Agent expert du réseau électrique, connecté aux 10 outils MCP, avec citations, "
        "calculs et boucle Reflexion avant publication."
    )
    template = agent_node["template"]
    template["agent_llm"]["value"] = "Google Generative AI"
    template["model_name"]["value"] = "gemini-3.5-flash"
    template["api_key"]["value"] = ""
    template["temperature"]["value"] = 0.1
    template["max_iterations"]["value"] = 15
    template["system_prompt"]["value"] = SYSTEM_PROMPT
    template["agent_description"]["value"] = "Agent VOLTIS avec accès aux outils MCP du réseau électrique."
    template["input_value"]["value"] = ""
    template["verbose"]["value"] = True

    # MCP Tools
    mcp_node = mcp_tools["data"]["node"]
    mcp_node["display_name"] = "VOLTIS · Serveur MCP 8100"
    mcp_node["description"] = "10 outils MCP : KPI, incidents, prévision, facturation, RAG."
    mcp_node["template"]["mcp_server"]["value"] = {
        "name": "volt-is-grid-mcp",
        "config": {
            "url": "http://127.0.0.1:8100/sse",
            "transport": "sse",
        },
    }
    mcp_node["template"]["tool"]["value"] = ""
    mcp_node["template"]["tools_metadata"]["value"] = []

    # Chat Output
    output_node = chat_output["data"]["node"]
    output_node["display_name"] = "Réponse sourcée · VOLTIS"
    output_node["description"] = "Réponse finale avec synthèse, plan d'action, limites et sources."
    output_node["template"]["sender_name"]["value"] = "VOLTIS"

    # Notes
    note["data"]["node"]["description"] = ARCH_NOTE

    a2a_note = copy.deepcopy(note)
    a2a_note["data"]["id"] = "note-A2A"
    a2a_note["id"] = "note-A2A"
    a2a_note["data"]["node"]["description"] = A2A_NOTE
    a2a_note["position"] = {"x": 80, "y": 1060}
    a2a_note["measured"] = {"height": 780, "width": 640}

    reflexion_note = copy.deepcopy(note)
    reflexion_note["data"]["id"] = "note-REFLEXION"
    reflexion_note["id"] = "note-REFLEXION"
    reflexion_note["data"]["node"]["description"] = REFLEXION_NOTE
    reflexion_note["position"] = {"x": 1560, "y": 580}
    reflexion_note["measured"] = {"height": 560, "width": 560}

    flow["data"]["nodes"] = [note, a2a_note, reflexion_note, chat_input, mcp_tools, agent, chat_output]

    # Edges
    edges = []
    edges.append({
        "animated": False,
        "className": "",
        "data": {
            "sourceHandle": {"dataType": "ChatInput", "id": "ChatInput-VOLTIS", "name": "message", "output_types": ["Message"]},
            "targetHandle": {"fieldName": "input_value", "id": "Agent-VOLTIS", "inputTypes": ["Message"], "type": "str"},
        },
        "id": "xy-edge__ChatInput-VOLTIS-message-Agent-VOLTIS-input_value",
        "selected": False,
        "source": "ChatInput-VOLTIS",
        "sourceHandle": '{"dataType": "ChatInput", "id": "ChatInput-VOLTIS", "name": "message", "output_types": ["Message"]}',
        "target": "Agent-VOLTIS",
        "targetHandle": '{"fieldName": "input_value", "id": "Agent-VOLTIS", "inputTypes": ["Message"], "type": "str"}',
    })
    edges.append({
        "animated": False,
        "className": "",
        "data": {
            "sourceHandle": {"dataType": "MCPTools", "id": "MCPTools-VOLTIS", "name": "component_as_tool", "output_types": ["Tool"]},
            "targetHandle": {"fieldName": "tools", "id": "Agent-VOLTIS", "inputTypes": ["Tool"], "type": "other"},
        },
        "id": "xy-edge__MCPTools-VOLTIS-component_as_tool-Agent-VOLTIS-tools",
        "selected": False,
        "source": "MCPTools-VOLTIS",
        "sourceHandle": '{"dataType": "MCPTools", "id": "MCPTools-VOLTIS", "name": "component_as_tool", "output_types": ["Tool"]}',
        "target": "Agent-VOLTIS",
        "targetHandle": '{"fieldName": "tools", "id": "Agent-VOLTIS", "inputTypes": ["Tool"], "type": "other"}',
    })
    edges.append({
        "animated": False,
        "className": "",
        "data": {
            "sourceHandle": {"dataType": "Agent", "id": "Agent-VOLTIS", "name": "response", "output_types": ["Message"]},
            "targetHandle": {"fieldName": "input_value", "id": "ChatOutput-VOLTIS", "inputTypes": ["Data", "DataFrame", "Message"], "type": "other"},
        },
        "id": "xy-edge__Agent-VOLTIS-response-ChatOutput-VOLTIS-input_value",
        "selected": False,
        "source": "Agent-VOLTIS",
        "sourceHandle": '{"dataType": "Agent", "id": "Agent-VOLTIS", "name": "response", "output_types": ["Message"]}',
        "target": "ChatOutput-VOLTIS",
        "targetHandle": '{"fieldName": "input_value", "id": "ChatOutput-VOLTIS", "inputTypes": ["Data", "DataFrame", "Message"], "type": "other"}',
    })
    flow["data"]["edges"] = edges

    # Métadonnées agentiques consolidées
    flow["volt_is"] = {
        "project": "VOLTIS — Agentic AI for the Electricity Sector",
        "version": "1.0.0",
        "date": "12 novembre 2026",
        "dashboard": "http://localhost:8033",
        "mcp": {
            "server": "volt-is-grid-mcp",
            "url": "http://127.0.0.1:8100/sse",
            "jsonrpc": "http://127.0.0.1:8100/mcp",
            "tools": [
                "get_grid_kpis", "get_region_profile", "get_consumption", "get_production_mix",
                "query_outages", "forecast_load", "simulate_bill", "search_knowledge",
                "recommend_energy_savings", "get_service_quality",
            ],
        },
        "a2a": {
            "orchestrator": "http://127.0.0.1:8101",
            "agents": {
                "grid-analyst": 8102,
                "outage-inspector": 8103,
                "billing-advisor": 8104,
                "forecast-agent": 8105,
            },
            "discovery": "http://127.0.0.1:8101/agents",
            "orchestrate": "http://127.0.0.1:8101/orchestrate",
        },
        "rag": {
            "retriever": "BM25 + TF-IDF",
            "documents": 12,
            "chunks": 49,
            "citations": "DOC-XX · vX.Y · article N",
        },
        "langgraph": {
            "nodes": ["planner", "retrieve", "tools", "writer", "critic", "refine", "finalize"],
            "pattern": "Generate → Critic → Refine",
            "threshold": 8.2,
            "max_iterations": 2,
        },
        "benchmark": {
            "tasks": 5,
            "initial": 6.48,
            "final": 9.40,
            "gain": 2.92,
            "citations_per_answer": 8.6,
            "latency_ms": 35.7,
        },
        "links": {
            "github": "https://github.com/kamalelafoui/Agentic-AI-Electricity-VOLTIS",
            "documentation": "docs/Documentation_Finale_VOLTIS.pdf",
            "presentation": "presentation/Presentation_Finale_VOLTIS.pdf",
            "video": "videos/VOLTIS_Demo.mp4",
        },
    }

    # Viewport
    flow.setdefault("data", {})["viewport"] = {"x": 0, "y": 0, "zoom": 0.55}

    # Propage le nouvel identifiant de flow dans les composants frontend
    for node in flow["data"]["nodes"]:
        node_template = node.get("data", {}).get("node", {}).get("template", {})
        if isinstance(node_template, dict) and "_frontend_node_flow_id" in node_template:
            node_template["_frontend_node_flow_id"]["value"] = flow_id

    for path in (OUT_JSON, OUT_ROOT):
        path.write_text(json.dumps(flow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("JSON Langflow généré :", OUT_JSON)
    print("Copie racine :", OUT_ROOT)
    print("Nœuds :", len(flow["data"]["nodes"]), "· Arêtes :", len(flow["data"]["edges"]))
    print("Nom :", flow["name"], "· ID :", flow["id"])


if __name__ == "__main__":
    main()
