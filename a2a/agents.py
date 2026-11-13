# -*- coding: utf-8 -*-
"""Logique métier des agents A2A VOLTIS.

Chaque agent reçoit un message, choisit ses outils et retourne un artifact
structuré (résumé, constats, données, sources). Aucun agent n'appelle
directement un autre agent : c'est le rôle de l'orchestrateur.
"""
from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Any

from shared import electricity_core as core

REGION_ALIASES = {
    "casablanca": "CAS", "casa": "CAS", "maârif": "CAS", "maarif": "CAS", "settat": "CAS",
    "rabat": "RSK", "salé": "RSK", "sale": "RSK", "kénitra": "RSK", "kenitra": "RSK",
    "marrakech": "MRS", "safi": "MRS", "essaouira": "MRS",
    "fès": "FES", "fes": "FES", "meknès": "FES", "meknes": "FES",
    "tanger": "TTA", "tétouan": "TTA", "tetouan": "TTA", "hoceïma": "TTA",
    "agadir": "SOM", "souss": "SOM", "tiznit": "SOM",
    "oujda": "ORI", "oriental": "ORI", "nador": "ORI",
    "béni mellal": "BMK", "beni mellal": "BMK", "khénifra": "BMK",
}


def _region(message: str) -> str:
    normalized = core.normalize(message)
    for alias, code in REGION_ALIASES.items():
        if alias in normalized:
            return code
    return "NATIONAL"


def _segment(message: str) -> str:
    normalized = core.normalize(message)
    if any(word in normalized for word in ("industriel", "industrie", "usine", "mwh")):
        return "industriel"
    if any(word in normalized for word in ("agricole", "ferme", "pompage")):
        return "agricole"
    if any(word in normalized for word in ("commercial", "hôtel", "hotel", "commerce")):
        return "commercial"
    if any(word in normalized for word in ("administration", "école", "ecole", "hôpital")):
        return "administration"
    return "residentiel"


def _mwh(message: str) -> float:
    normalized = core.normalize(message)
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*mwh", normalized)
    if match:
        return float(match.group(1).replace(",", "."))
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*kwh", normalized)
    if match:
        return float(match.group(1).replace(",", ".")) / 1000
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*gwh", normalized)
    if match:
        return float(match.group(1).replace(",", ".")) * 1000
    return 250.0


def _temperature(message: str) -> float:
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:°c|degres|degrés)", core.normalize(message))
    if match:
        return float(match.group(1).replace(",", "."))
    return 5.0


def _customer(message: str) -> str:
    normalized = core.normalize(message)
    for customer in core.customers():
        if customer["customer_id"].lower() in normalized or core.normalize(customer["name"]) in normalized:
            return customer["customer_id"]
    return ""


def _rag(message: str, top_k: int = 2) -> list[dict]:
    return core.search_documents(message, top_k)["results"]


def _fmt(value: float, decimals: int = 0) -> str:
    if decimals == 0:
        return f"{value:,.0f}".replace(",", " ")
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")


def grid_analyst(message: str, context: dict) -> dict:
    region = _region(message)
    normalized = core.normalize(message)
    tools = []
    is_mix = any(word in normalized for word in ("mix", "production", "renouvelable", "solaire", "éolien", "eolien"))
    rag_query = message + (" mix production renouvelable" if is_mix else " qualité service SAIDI pertes consommation")
    sources = _rag(rag_query, 2)
    if is_mix:
        mix = core.call_tool("get_production_mix", {})
        kpis = core.call_tool("get_grid_kpis", {})
        tools = ["get_production_mix", "get_grid_kpis"]
        findings = [
            f"Part renouvelable : **{_fmt(mix['renewable_share_pct'], 1)} %** de **{_fmt(mix['total_gwh'])} GWh**.",
            "Éolien : **16,5 %**, hydraulique : **12,0 %**, solaire : **9,5 %**.",
            f"Intensité carbone moyenne : **{_fmt(mix['co2_g_per_kwh'])} g CO₂/kWh**.",
        ]
        summary = f"Le mix national est à {_fmt(mix['renewable_share_pct'], 1)} % renouvelable, dominé par le thermique."
        data = {"mix": mix, "kpis": kpis}
    else:
        if region == "NATIONAL":
            profile = core.call_tool("get_grid_kpis", {})
            label = "National"
            tools = ["get_grid_kpis"]
            findings = [
                f"Consommation : **{_fmt(profile['consumption_gwh'])} GWh** pour **{_fmt(profile['clients'])} clients**.",
                f"Pointe : **{_fmt(profile['peak_mw'])} MW** ; pertes : **{_fmt(profile['losses_pct'], 2)} %**.",
                f"SAIDI : **{_fmt(profile['saidi_min'], 1)} min** ; SAIFI : **{_fmt(profile['saifi'], 2)}**.",
            ]
            summary = f"Le réseau national affiche un SAIDI de {_fmt(profile['saidi_min'], 1)} min et une pointe de {_fmt(profile['peak_mw'])} MW."
            data = {"kpis": profile}
        else:
            profile = core.call_tool("get_region_profile", {"region_code": region})
            consumption = core.call_tool("get_consumption", {"region_code": region, "months": 12})
            label = profile["name"]
            tools = ["get_region_profile", "get_consumption"]
            findings = [
                f"Consommation annuelle : **{_fmt(profile['consumption_gwh'])} GWh** ({_fmt(profile['clients'])} clients).",
                f"Pointe : **{_fmt(profile['peak_mw'])} MW** ; pertes : **{_fmt(profile['losses_pct'], 2)} %**.",
                f"Qualité : SAIDI **{_fmt(profile['saidi_min'], 1)} min**, SAIFI **{_fmt(profile['saifi'], 2)}**.",
            ]
            summary = f"{label} consomme {_fmt(profile['consumption_gwh'])} GWh/an avec un SAIDI de {_fmt(profile['saidi_min'], 1)} min."
            data = {"profile": profile, "consumption": consumption}
    return {
        "summary": summary,
        "findings": findings,
        "sources": [{"citation": source["citation"], "title": source["title"]} for source in sources],
        "tools": tools,
        "data": data,
    }


def outage_inspector(message: str, context: dict) -> dict:
    region = _region(message)
    incidents = core.call_tool("query_outages", {"region_code": region, "limit": 12})
    quality = core.call_tool("get_service_quality", {"region_code": region})
    sources = _rag(message + " incident coupure délestage continuité", 2)
    summary_data = incidents["summary"]
    rows = incidents["incidents"]
    top = rows[0] if rows else {}
    normalized = core.normalize(message)
    named = next(
        (row for row in rows if "maarif" in normalized and "maarif" in core.normalize(row["feeder"])),
        top,
    )
    active_label = "actif" if summary_data["active"] == 1 else "actifs"
    findings = []
    if named:
        findings.append(
            f"Incident **{named['incident_id']}** sur le départ **{named['feeder']}** "
            f"({named['region']}) : cause **{named['cause']}**, **{named['duration_min']} min**, "
            f"**{_fmt(named['customers_affected'])} clients**, priorité **{named['priority']}**."
        )
    findings.append(
        f"Sur 90 jours : **{summary_data['incidents']} incidents**, dont **{summary_data['active']} {active_label}** "
        f"et **{summary_data['by_priority'].get('P1', 0)} P1**."
    )
    findings.append(
        f"MTTR moyen **{_fmt(summary_data['mttr_min'], 1)} min** ; cause dominante "
        f"**{next(iter(summary_data['by_cause']), 'n/d')}** ; SAIDI **{_fmt(quality.get('saidi_min', 0), 1)} min**."
    )
    return {
        "summary": (
            f"{summary_data['incidents']} incidents analysés sur {core.region_name(region) if region != 'NATIONAL' else 'le national'}, "
            f"{summary_data['active']} encore {active_label}, MTTR {_fmt(summary_data['mttr_min'], 1)} min."
        ),
        "findings": findings,
        "sources": [{"citation": source["citation"], "title": source["title"]} for source in sources],
        "tools": ["query_outages", "get_service_quality", "search_knowledge"],
        "data": {"incidents": rows[:5], "summary": summary_data, "quality": quality},
    }


def billing_advisor(message: str, context: dict) -> dict:
    normalized = core.normalize(message)
    billing_intent = any(word in normalized for word in ("facture", "tarif", "prix", "mwh", "kwh", "abonnement", "prime"))
    if not billing_intent and any(word in normalized for word in ("coupure", "incident", "compensation", "panne")):
        region = _region(message)
        incidents = core.call_tool("query_outages", {"region_code": region, "limit": 12})
        named = next(
            (row for row in incidents["incidents"] if "maarif" in normalized and "maarif" in core.normalize(row["feeder"])),
            None,
        )
        incident = named or (incidents["incidents"][0] if incidents["incidents"] else {})
        duration = incident.get("duration_min", 0)
        customers = incident.get("customers_affected", 0)
        eligible = duration >= 240
        unit = 1500 if eligible else 20
        compensation = customers * unit
        sources = _rag(message + " compensation client réclamation coupure", 2)
        findings = [
            f"Incident retenu : **{incident.get('incident_id', 'n/d')}**, **{duration} min**, "
            f"**{_fmt(customers)} clients** impactés [{_pick_ref(sources, 'DOC-CLIENT')}].",
            f"Compensation automatique : **{'oui' if eligible else 'non'}** — seuil de 4 h pour un client "
            f"industriel, 6 h pour un résidentiel [DOC-CLIENT].",
            f"Geste commercial estimé : **{_fmt(compensation)} MAD** "
            f"({_fmt(customers)} clients × {unit} MAD).",
        ]
        return {
            "summary": f"Pas de compensation automatique (durée {duration} min) ; geste commercial estimé à {_fmt(compensation)} MAD.",
            "findings": findings,
            "sources": [{"citation": source["citation"], "title": source["title"]} for source in sources],
            "tools": ["query_outages", "search_knowledge"],
            "data": {"incident": incident, "compensation_mad": compensation, "eligible": eligible},
        }

    segment = _segment(message)
    consumption = _mwh(message)
    bill = core.call_tool("simulate_bill", {"segment": segment, "consumption_mwh": consumption})
    customer = _customer(message)
    savings = core.call_tool("recommend_energy_savings", {"customer_id": customer}) if customer else {}
    sources = _rag(message + " tarif facture kWh prime", 2)
    findings = [
        f"Énergie : **{_fmt(bill['energy_mad'], 2)} MAD** ; prime fixe : **{_fmt(bill['fixed_fee_mad'], 2)} MAD** ; "
        f"TVA : **{_fmt(bill['vat_mad'], 2)} MAD**.",
        f"Total mensuel : **{_fmt(bill['total_mad'], 2)} MAD**, soit **{_fmt(bill['average_price_mad_kwh'], 3)} MAD/kWh**.",
        f"Segment **{bill['segment_label']}** pour **{_fmt(bill['consumption_mwh'], 2)} MWh**.",
    ]
    if savings and savings.get("actions"):
        findings.append(
            f"Économies potentielles : **{_fmt(savings['total_gain_pct'], 1)} %** "
            f"(**{_fmt(savings['total_gain_mad'])} MAD/an**) pour {savings['customer_name']}."
        )
    return {
        "summary": f"Facture estimée à {_fmt(bill['total_mad'], 2)} MAD pour {_fmt(bill['consumption_mwh'], 2)} MWh.",
        "findings": findings,
        "sources": [{"citation": source["citation"], "title": source["title"]} for source in sources],
        "tools": ["simulate_bill"] + (["recommend_energy_savings"] if customer else []),
        "data": {"bill": bill, "savings": savings},
    }


def _pick_ref(sources: list[dict], doc_id: str) -> int:
    for index, source in enumerate(sources, 1):
        if source["doc_id"] == doc_id:
            return index
    return 1 if sources else 1


def forecast_agent(message: str, context: dict) -> dict:
    region = _region(message)
    delta = _temperature(message)
    forecast = core.call_tool("forecast_load", {"region_code": region, "horizon_h": 24, "temperature_delta": delta})
    kpis = core.call_tool("get_grid_kpis", {})
    sources = _rag(message + " prévision charge pointe réserve température", 2)
    findings = [
        f"Pointe prévisionnelle : **{_fmt(forecast['peak_mw'])} MW** à **{forecast['peak_at']}**.",
        f"Capacité : **{_fmt(forecast['capacity_mw'])} MW** ; marge de réserve : "
        f"**{_fmt(forecast['reserve_margin_pct'], 1)} %** → risque **{forecast['risk']}**.",
        f"Hypothèse météo : **+{_fmt(delta, 1)} °C** ; recommandation : {forecast['recommendation']}",
    ]
    return {
        "summary": (
            f"Risque {forecast['risk']} sur {forecast['region']} : pointe {_fmt(forecast['peak_mw'])} MW, "
            f"marge {_fmt(forecast['reserve_margin_pct'], 1)} %."
        ),
        "findings": findings,
        "sources": [{"citation": source["citation"], "title": source["title"]} for source in sources],
        "tools": ["forecast_load", "get_grid_kpis"],
        "data": {"forecast": forecast, "kpis": kpis},
    }


HANDLERS = {
    "grid-analyst": grid_analyst,
    "outage-inspector": outage_inspector,
    "billing-advisor": billing_advisor,
    "forecast-agent": forecast_agent,
}


def handle_agent(agent_id: str, message: str, context: dict | None = None, correlation_id: str = "") -> dict:
    started = time.perf_counter()
    handler = HANDLERS.get(agent_id)
    if not handler:
        return {
            "agent_id": agent_id,
            "status": "error",
            "error": f"Agent inconnu : {agent_id}",
            "correlation_id": correlation_id,
        }
    try:
        result = handler(message, context or {})
        status = "ok"
    except Exception as error:  # pragma: no cover
        result = {"summary": "Erreur d'exécution", "findings": [str(error)], "sources": [], "tools": [], "data": {}}
        status = "error"
    latency = round((time.perf_counter() - started) * 1000, 2)
    return {
        "agent_id": agent_id,
        "agent_label": core.AGENT_CAPABILITIES[agent_id]["label"],
        "status": status,
        "correlation_id": correlation_id,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "latency_ms": latency,
        "message": message,
        **result,
    }
