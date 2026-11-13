# -*- coding: utf-8 -*-
"""Serveur A2A VOLTIS — orchestrateur 8101 + 4 agents spécialisés 8102-8105.

Chaque agent publie une AgentCard sur /.well-known/agent.json et accepte des
messages sur /message. L'orchestrateur découvre les cartes, sélectionne les
agents, délègue en parallèle avec un correlation_id et agrège les artifacts.

Lancement : python main.py a2a   (ou python -m a2a.server)
"""
from __future__ import annotations

import json
import multiprocessing as mp
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from a2a.agents import handle_agent  # noqa: E402
from shared import electricity_core as core  # noqa: E402

ORCHESTRATOR_PORT = 8101
AGENT_PORTS = core.AGENT_CAPABILITIES
CARDS = ROOT / "a2a" / "agent_cards"
LOG_DIR = ROOT / "a2a" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
DELEGATION_LOG = ROOT / "data" / "a2a_delegations.jsonl"
LOG_LOCK = threading.Lock()

DELEGATIONS: list[dict] = []


def load_card(agent_id: str) -> dict:
    path = CARDS / f"{agent_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _log_delegation(event: dict) -> None:
    event["timestamp"] = datetime.now().isoformat(timespec="seconds")
    with LOG_LOCK:
        DELEGATIONS.append(event)
        del DELEGATIONS[:-200]
        with DELEGATION_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        with (LOG_DIR / "orchestrateur.log").open("a", encoding="utf-8") as handle:
            handle.write(
                f"{event['timestamp']} {event.get('correlation_id', '')} "
                f"{event.get('agent_id', event.get('event', ''))} {event.get('status', '')} "
                f"{event.get('latency_ms', '')}ms\n"
            )


# --------------------------------------------------------------------------- #
# Applications agents
# --------------------------------------------------------------------------- #
class MessageRequest(BaseModel):
    message: str
    context: dict = {}
    correlation_id: str = ""


def make_agent_app(agent_id: str) -> FastAPI:
    info = AGENT_PORTS[agent_id]
    application = FastAPI(title=f"VOLTIS Agent — {info['label']}", version="1.0.0")
    application.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
    )
    card = load_card(agent_id)

    @application.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "agent_id": agent_id,
            "label": info["label"],
            "port": info["port"],
            "card": f"http://127.0.0.1:{info['port']}/.well-known/agent.json",
            "tools": info["tools"],
        }

    @application.get("/.well-known/agent.json")
    def agent_card() -> dict:
        return card

    @application.get("/agent.json")
    def agent_card_alias() -> dict:
        return card

    @application.post("/message")
    def message(request: MessageRequest) -> dict:
        return handle_agent(agent_id, request.message, request.context, request.correlation_id)

    return application


# --------------------------------------------------------------------------- #
# Orchestrateur
# --------------------------------------------------------------------------- #
orchestrator = FastAPI(title="VOLTIS A2A Orchestrator", version="1.0.0")
orchestrator.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class DiscoverRequest(BaseModel):
    query: str = ""
    capability: str = ""


class OrchestrateRequest(BaseModel):
    question: str
    region_code: str = "NATIONAL"
    max_agents: int = 3
    context: dict = {}


def _discover_live() -> list[dict]:
    cards = []
    for agent_id, info in AGENT_PORTS.items():
        local = load_card(agent_id)
        try:
            response = requests.get(f"http://127.0.0.1:{info['port']}/.well-known/agent.json", timeout=0.8)
            response.raise_for_status()
            cards.append({"agent_id": agent_id, "status": "en ligne", "card": response.json()})
        except Exception:
            cards.append({"agent_id": agent_id, "status": "carte locale", "card": local})
    return cards


def _score_agents(question: str) -> list[tuple[float, str]]:
    normalized = core.normalize(question)
    scores = []
    for agent_id, info in AGENT_PORTS.items():
        score = sum(2.0 for keyword in info["keywords"] if core.normalize(keyword) in normalized)
        if agent_id == "outage-inspector" and any(word in normalized for word in ("coupure", "incident", "panne")):
            score += 3.0
        if agent_id == "billing-advisor" and any(word in normalized for word in ("facture", "tarif", "économie", "economie")):
            score += 3.0
        if agent_id == "forecast-agent" and any(word in normalized for word in ("demain", "risque", "pointe", "prévision", "prevision")):
            score += 3.0
        if agent_id == "grid-analyst" and any(word in normalized for word in ("mix", "production", "consommation", "kpi", "région")):
            score += 2.5
        scores.append((score, agent_id))
    return sorted(scores, reverse=True)


def _select_agents(question: str, max_agents: int = 3) -> list[str]:
    normalized = core.normalize(question)
    if any(word in normalized for word in ("coupure", "incident", "panne", "délestage", "delestage", "maârif", "maarif")):
        preferred = ["outage-inspector", "forecast-agent", "billing-advisor", "grid-analyst"]
    elif any(word in normalized for word in ("facture", "tarif", "prix", "économie", "economie", "kwh")):
        preferred = ["billing-advisor", "grid-analyst", "forecast-agent", "outage-inspector"]
    elif any(word in normalized for word in ("mix", "production", "renouvelable", "solaire", "éolien", "eolien")):
        preferred = ["grid-analyst", "forecast-agent", "outage-inspector", "billing-advisor"]
    elif any(word in normalized for word in ("demain", "risque", "pointe", "prévision", "prevision", "surcharge")):
        preferred = ["forecast-agent", "grid-analyst", "outage-inspector", "billing-advisor"]
    else:
        ranked = _score_agents(question)
        preferred = [agent_id for score, agent_id in ranked if score > 0]
        for _, agent_id in ranked:
            if agent_id not in preferred:
                preferred.append(agent_id)
    selected = preferred[:max_agents]
    for agent_id in preferred:
        if len(selected) >= 2:
            break
        if agent_id not in selected:
            selected.append(agent_id)
    return selected[:max_agents]


def _call_agent(agent_id: str, question: str, context: dict, correlation_id: str) -> dict:
    info = AGENT_PORTS[agent_id]
    started = time.perf_counter()
    try:
        response = requests.post(
            f"http://127.0.0.1:{info['port']}/message",
            json={"message": question, "context": context, "correlation_id": correlation_id},
            timeout=8,
        )
        response.raise_for_status()
        artifact = response.json()
        artifact["mode"] = "A2A HTTP"
    except Exception as error:
        artifact = handle_agent(agent_id, question, context, correlation_id)
        artifact["mode"] = "repli local"
        artifact["fallback_reason"] = str(error)[:120]
    artifact["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
    return artifact


@orchestrator.get("/health")
def health() -> dict:
    cards = _discover_live()
    online = sum(1 for card in cards if card["status"] == "en ligne")
    return {
        "status": "ok",
        "service": "volt-is-a2a-orchestrator",
        "version": "1.0.0",
        "port": ORCHESTRATOR_PORT,
        "agents_total": len(cards),
        "agents_online": online,
        "agents": [{"agent_id": card["agent_id"], "status": card["status"]} for card in cards],
        "delegations": len(DELEGATIONS),
    }


@orchestrator.get("/.well-known/agent.json")
def orchestrator_card() -> dict:
    return load_card("orchestrator")


@orchestrator.get("/agents")
def agents() -> dict:
    cards = _discover_live()
    return {"agents": cards, "count": len(cards), "hub": "VOLTIS Agentic Hub"}


@orchestrator.post("/discover")
def discover(request: DiscoverRequest) -> dict:
    query = request.query or request.capability
    ranked = _score_agents(query)
    cards = {item["agent_id"]: item for item in _discover_live()}
    return {
        "query": query,
        "selected": [
            {
                "agent_id": agent_id,
                "score": round(score, 1),
                "status": cards.get(agent_id, {}).get("status", "inconnu"),
                "card": cards.get(agent_id, {}).get("card", load_card(agent_id)),
            }
            for score, agent_id in ranked
        ],
        "discovery": "AgentCards via /.well-known/agent.json",
    }


@orchestrator.post("/orchestrate")
def orchestrate(request: OrchestrateRequest) -> dict:
    started = time.perf_counter()
    correlation_id = f"A2A-{uuid.uuid4().hex[:8].upper()}"
    question = request.question
    selected = _select_agents(question, max(2, min(request.max_agents, 4)))
    timeline = [
        {
            "step": "discovery",
            "label": "Découverte des AgentCards",
            "detail": f"{len(AGENT_PORTS)} agents interrogés",
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "status": "ok",
        },
        {
            "step": "selection",
            "label": "Sélection du hub",
            "detail": ", ".join(selected),
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "status": "ok",
        },
    ]
    context = {
        "region_code": request.region_code,
        "hub": "VOLTIS",
        "correlation_id": correlation_id,
        **request.context,
    }
    artifacts: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(selected)) as executor:
        futures = {
            executor.submit(_call_agent, agent_id, question, context, correlation_id): agent_id
            for agent_id in selected
        }
        for future in as_completed(futures):
            agent_id = futures[future]
            artifact = future.result()
            artifacts.append(artifact)
            _log_delegation(
                {
                    "event": "delegation",
                    "correlation_id": correlation_id,
                    "agent_id": agent_id,
                    "status": artifact.get("status", "ok"),
                    "latency_ms": artifact.get("latency_ms", 0),
                    "task": question,
                    "mode": artifact.get("mode"),
                    "summary": artifact.get("summary", "")[:160],
                }
            )
            timeline.append(
                {
                    "step": "delegation",
                    "label": f"{core.AGENT_CAPABILITIES[agent_id]['label']}",
                    "detail": artifact.get("summary", "")[:120],
                    "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                    "status": artifact.get("status", "ok"),
                    "latency_ms": artifact.get("latency_ms", 0),
                    "mode": artifact.get("mode"),
                }
            )
    artifacts.sort(key=lambda item: selected.index(item["agent_id"]))
    aggregated = _aggregate(question, correlation_id, artifacts)
    latency = round((time.perf_counter() - started) * 1000, 1)
    timeline.append(
        {
            "step": "aggregation",
            "label": "Agrégation du hub",
            "detail": f"{len(artifacts)} artifacts consolidés",
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "status": "ok",
            "latency_ms": latency,
        }
    )
    _log_delegation(
        {
            "event": "orchestration",
            "correlation_id": correlation_id,
            "status": "ok",
            "latency_ms": latency,
            "task": question,
            "agents": selected,
            "agent_count": len(selected),
        }
    )
    return {
        "correlation_id": correlation_id,
        "question": question,
        "region_code": request.region_code,
        "selected_agents": selected,
        "artifacts": artifacts,
        "aggregated_answer": aggregated,
        "timeline": timeline,
        "latency_ms": latency,
        "hub": "VOLTIS Agentic Hub",
        "protocol": "A2A 0.3 · AgentCard + message/send",
    }


def _aggregate(question: str, correlation_id: str, artifacts: list[dict]) -> str:
    lines = [
        "## Réponse consolidée du hub A2A",
        f"**Corrélation :** `{correlation_id}` · **Agents mobilisés :** {len(artifacts)} · "
        f"**Question :** {question}",
        "",
    ]
    for artifact in artifacts:
        lines.append(f"### {artifact.get('agent_label', artifact['agent_id'])}")
        lines.append(artifact.get("summary", ""))
        for finding in artifact.get("findings", [])[:4]:
            lines.append(f"- {finding}")
        if artifact.get("sources"):
            lines.append(
                "*Sources :* " + ", ".join(
                    f"{source['citation']}" for source in artifact["sources"][:2]
                )
            )
        lines.append("")
    lines.append("## Synthèse du hub")
    lines.append(
        f"- **{len(artifacts)} agents** ont collaboré en parallèle sur la même tâche ; "
        f"chaque artifact est traçable par `{correlation_id}`."
    )
    lines.append("- Les chiffres proviennent des outils MCP et des données synthétiques VOLTIS.")
    lines.append("- Les recommandations sont priorisées : sécurité, continuité, puis optimisation économique.")
    return "\n".join(lines)


@orchestrator.get("/delegations")
def delegations(limit: int = 20) -> dict:
    return {"delegations": DELEGATIONS[-limit:][::-1], "count": len(DELEGATIONS)}


# --------------------------------------------------------------------------- #
# Lancement
# --------------------------------------------------------------------------- #
def _serve(agent_id: str) -> None:
    port = AGENT_PORTS[agent_id]["port"]
    uvicorn.run(make_agent_app(agent_id), host="0.0.0.0", port=port, log_level="warning")


def _serve_orchestrator() -> None:
    uvicorn.run(orchestrator, host="0.0.0.0", port=ORCHESTRATOR_PORT, log_level="info")


def run_all() -> None:
    processes = []
    for agent_id in AGENT_PORTS:
        process = mp.Process(target=_serve, args=(agent_id,), daemon=True, name=f"volt-is-{agent_id}")
        process.start()
        processes.append(process)
        print(f"  · Agent {agent_id:<18} http://127.0.0.1:{AGENT_PORTS[agent_id]['port']}")
    time.sleep(1.2)
    print(f"  · Orchestrateur       http://127.0.0.1:{ORCHESTRATOR_PORT}")
    try:
        _serve_orchestrator()
    finally:
        for process in processes:
            process.terminate()


if __name__ == "__main__":
    run_all()
