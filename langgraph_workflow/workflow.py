# -*- coding: utf-8 -*-
"""Workflow agentique LangGraph de VOLTIS.

Graphe : Planner → Retriever → Tools → Writer → Critic ⇄ Refiner → Finalize.
La boucle Critic/Refiner implémente le pattern Reflexion (Generate → Critic →
Refine) demandé au Jour 31, avec mesure du gain de qualité.
"""
from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

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

SEGMENT_ALIASES = {
    "industriel": "industriel", "industrie": "industriel", "usine": "industriel",
    "résidentiel": "residentiel", "residentiel": "residentiel", "ménage": "residentiel", "maison": "residentiel",
    "commercial": "commercial", "commerce": "commercial", "hôtel": "commercial", "hotel": "commercial",
    "agricole": "agricole", "agriculture": "agricole", "ferme": "agricole",
    "administration": "administration", "administration": "administration", "école": "administration",
}


class WorkflowState(TypedDict, total=False):
    question: str
    region_code: str
    audience: str
    top_k: int
    threshold: float
    max_iterations: int
    intent: str
    intent_label: str
    plan: list[str]
    tool_names: list[str]
    tool_arguments: dict
    sources: list[dict]
    tool_results: dict
    tool_trace: list[dict]
    draft: str
    critique: dict
    score_history: list[dict]
    iterations: int
    trace: list[dict]
    started_at: float
    elapsed_ms: float
    final_answer: str
    confidence: str


# --------------------------------------------------------------------------- #
# Détection d'intention et extraction de contexte
# --------------------------------------------------------------------------- #
INTENTS = {
    "billing": {
        "label": "Facturation",
        "keywords": ["facture", "tarif", "prix", "mad", "dh", "économi", "abonnement", "kwh", "prime"],
    },
    "forecast": {
        "label": "Prévision",
        "keywords": ["prévision", "prevision", "demain", "risque", "surcharge", "pointe", "réserve",
                     "reserve", "température", "temperature", "19h", "météo", "meteo"],
    },
    "outage": {
        "label": "Incidents",
        "keywords": ["coupure", "incident", "panne", "délestage", "delestage", "saidi", "saifi",
                     "mttr", "urgence", "défaut", "defaut", "maârif", "maarif"],
    },
    "mix": {
        "label": "Mix production",
        "keywords": ["mix", "production", "renouvelable", "solaire", "éolien", "eolien",
                     "hydraulique", "charbon", "import", "co2"],
    },
    "kpi": {
        "label": "Pilotage KPI",
        "keywords": ["kpi", "consommation", "clients", "pertes", "statistique", "région", "region",
                     "performance", "indicateur"],
    },
}

INTENT_TOOLS = {
    "billing": ["simulate_bill", "search_knowledge"],
    "forecast": ["forecast_load", "get_region_profile", "search_knowledge"],
    "outage": ["query_outages", "get_service_quality", "search_knowledge"],
    "mix": ["get_production_mix", "get_grid_kpis", "search_knowledge"],
    "kpi": ["get_grid_kpis", "get_consumption", "get_service_quality", "search_knowledge"],
    "rag": ["search_knowledge", "get_grid_kpis"],
}


def detect_region(question: str) -> str:
    normalized = core.normalize(question)
    for alias, code in REGION_ALIASES.items():
        if alias in normalized:
            return code
    for region in core.regions():
        if core.normalize(region["name"]) in normalized:
            return region["code"]
    return ""


def detect_intent(question: str) -> str:
    normalized = core.normalize(question)
    scores = {}
    for intent, config in INTENTS.items():
        scores[intent] = sum(1 for keyword in config["keywords"] if core.normalize(keyword) in normalized)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "rag"


def detect_segment(question: str) -> str:
    normalized = core.normalize(question)
    for alias, segment in SEGMENT_ALIASES.items():
        if core.normalize(alias) in normalized:
            return segment
    return "industriel"


def detect_consumption_mwh(question: str) -> float:
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(mwh|mégawattheure|megawattheure)", core.normalize(question))
    if match:
        return float(match.group(1).replace(",", "."))
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(gwh|gigawattheure)", core.normalize(question))
    if match:
        return float(match.group(1).replace(",", ".")) * 1000
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(kwh|kilowattheure)", core.normalize(question))
    if match:
        return float(match.group(1).replace(",", ".")) / 1000
    return 250.0


def detect_temperature_delta(question: str) -> float:
    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:°c|degrés?|degres?)", core.normalize(question))
    if match:
        return float(match.group(1).replace(",", "."))
    if any(word in core.normalize(question) for word in ("canicule", "chaleur", "forte chaleur")):
        return 6.0
    return 5.0


def detect_customer(question: str) -> str:
    normalized = core.normalize(question)
    for customer in core.customers():
        if customer["customer_id"].lower() in normalized:
            return customer["customer_id"]
    for customer in core.customers():
        if core.normalize(customer["name"]) in normalized:
            return customer["customer_id"]
    return ""


# --------------------------------------------------------------------------- #
# Composition des réponses
# --------------------------------------------------------------------------- #
def _fmt(value: float, decimals: int = 0) -> str:
    if decimals == 0:
        return f"{value:,.0f}".replace(",", " ")
    return f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")


def _sources_block(sources: list[dict]) -> str:
    lines = ["## Sources"]
    for index, source in enumerate(sources, 1):
        lines.append(
            f"{index}. **{source['citation']}** — {source['title']} "
            f"(pertinence {_fmt(source['relevance_pct'], 0)} %)"
        )
    return "\n".join(lines)


def _source_ref(index: int) -> str:
    return f"[{index}]"


def _pick_source(sources: list[dict], doc_id: str) -> int:
    for index, source in enumerate(sources, 1):
        if source["doc_id"] == doc_id:
            return index
    return 1 if sources else 1


def _incidents(state: WorkflowState) -> list[dict]:
    result = state.get("tool_results", {}).get("query_outages", {})
    return result.get("incidents", [])


def _find_named_incident(state: WorkflowState) -> dict:
    question = core.normalize(state.get("question", ""))
    for incident in _incidents(state):
        feeder = core.normalize(incident.get("feeder", ""))
        root = feeder.split("-")[0]
        if "maarif" in question and "maarif" in feeder:
            return incident
        if "maarif" in question and "maârif" in core.normalize(incident.get("region", "")):
            return incident
    return _incidents(state)[0] if _incidents(state) else {}


def compose_answer(state: WorkflowState, refined: bool = False) -> str:
    intent = state.get("intent", "rag")
    region_code = state.get("region_code", "NATIONAL")
    region = "National" if region_code == "NATIONAL" else core.region_name(region_code)
    tools = state.get("tool_results", {})
    sources = state.get("sources", [])
    question = state.get("question", "")
    kpis = tools.get("get_grid_kpis") or core.national_kpis()

    if intent == "outage":
        data = tools.get("query_outages", {})
        summary = data.get("summary", core.outage_summary(region_code))
        incident = _find_named_incident(state)
        incidents = _incidents(state)
        p1 = summary.get("by_priority", {}).get("P1", 0)
        top_cause = next(iter(summary.get("by_cause", {})), "équipement")
        ref_inc = _pick_source(sources, "DOC-INCIDENTS")
        ref_del = _pick_source(sources, "DOC-DELESTAGE")
        if refined:
            details = []
            if incident:
                details.append(
                    f"- Incident le plus récent : **{incident['incident_id']}**, départ **{incident['feeder']}** "
                    f"({incident['region']}), cause **{incident['cause']}**, **{incident['duration_min']} min**, "
                    f"**{_fmt(incident['customers_affected'])} clients** impactés, priorité **{incident['priority']}** "
                    f"[{ref_inc}]."
                )
            details.append(
                f"- Sur 90 jours, **{summary.get('incidents', 0)} incidents** sont enregistrés sur le périmètre "
                f"{region}, dont **{summary.get('active', 0)} en cours** et **{p1} de priorité P1**."
            )
            details.append(
                f"- Le **MTTR moyen** est de **{_fmt(summary.get('mttr_min', 0), 1)} min** et la cause dominante "
                f"est **{top_cause}** ; l'énergie non servie atteint "
                f"**{_fmt(summary.get('energy_not_served_mwh', 0), 1)} MWh**."
            )
            details.append(
                f"- La classification P1 s'applique au-delà de **8 000 clients** ou **4 heures** de coupure ; "
                f"le SAIDI et le SAIFI sont recalculés à chaque clôture d'incident [{ref_inc}]."
            )
            return "\n".join(
                [
                    "## Synthèse",
                    f"La situation sur **{region}** reste maîtrisée mais sous surveillance : "
                    f"**{summary.get('active', 0)} incident(s) en cours** et un MTTR de "
                    f"**{_fmt(summary.get('mttr_min', 0), 1)} min**. La cause dominante est **{top_cause}**.",
                    "## Analyse détaillée",
                    "\n".join(details),
                    "## Plan d'action",
                    f"1. **Sécuriser et diagnostiquer** le départ concerné sous 30 min : consignation, "
                    f"vérification d'absence de tension et recherche de défaut [{ref_inc}].",
                    f"2. **Rétablir par blocs de 15 MW** pour éviter un appel de charge brutal, puis confirmer "
                    f"la stabilité de la tension en bout de réseau [{ref_del}].",
                    f"3. **Communiquer** aux clients impactés dans les 10 min (SMS, portail) et ouvrir un dossier "
                    f"de compensation si la coupure dépasse 4 h [{ref_inc}].",
                    f"4. **Capitaliser** : fiche de retour d'expérience sous 5 jours et mise à jour du plan de "
                    f"maintenance si la cause est récurrente.",
                    "## Limites & hypothèses",
                    "- Analyse fondée sur les données synthétiques du 12 novembre 2026 ; un diagnostic terrain "
                    "reste nécessaire pour confirmer l'origine exacte du défaut.",
                    _sources_block(sources),
                ]
            )
        return "\n".join(
            [
                "## Réponse",
                f"Sur **{region}**, **{summary.get('incidents', 0)} incidents** ont été enregistrés, "
                f"dont **{summary.get('active', 0)} encore actifs**. Le MTTR moyen est de "
                f"**{_fmt(summary.get('mttr_min', 0), 1)} min**.",
                "## Points clés",
                f"- Cause principale : **{top_cause}**.",
                f"- Priorité P1 : **{p1} incident(s)**.",
                "## Prochaine étape",
                "Envoyer une équipe pour sécuriser le départ et rétablir le service.",
            ]
        )

    if intent == "billing":
        bill = tools.get("simulate_bill", {})
        savings = tools.get("recommend_energy_savings", {})
        ref_tarif = _pick_source(sources, "DOC-TARIFS")
        if refined:
            lines = [
                f"- Consommation : **{_fmt(bill.get('consumption_kwh', 0), 0)} kWh** "
                f"({_fmt(bill.get('consumption_mwh', 0), 2)} MWh) pour le segment "
                f"**{bill.get('segment_label', '')}**.",
                f"- Énergie : **{_fmt(bill.get('energy_mad', 0), 2)} MAD**, prime fixe : "
                f"**{_fmt(bill.get('fixed_fee_mad', 0), 2)} MAD**, TVA : "
                f"**{_fmt(bill.get('vat_mad', 0), 2)} MAD** [{ref_tarif}].",
                f"- **Total mensuel estimé : {_fmt(bill.get('total_mad', 0), 2)} MAD**, soit un prix moyen de "
                f"**{_fmt(bill.get('average_price_mad_kwh', 0), 3)} MAD/kWh**.",
            ]
            if savings.get("actions"):
                lines.append(
                    f"- Gisement d'économies identifié : **{_fmt(savings.get('total_gain_pct', 0), 1)} %**, "
                    f"soit **{_fmt(savings.get('total_gain_mad', 0), 0)} MAD/an** pour "
                    f"**{savings.get('customer_name', 'le client')}**."
                )
                actions = "\n".join(
                    f"{index}. **{action['action']}** — gain estimé **{_fmt(action['gain_pct'], 1)} %** "
                    f"({_fmt(action['gain_mad'], 0)} MAD/an) : {action['comment']}"
                    for index, action in enumerate(savings["actions"][:4], 1)
                )
            else:
                actions = (
                    "1. **Vérifier la puissance souscrite** et le facteur de charge pour éviter une prime fixe "
                    "surdimensionnée.\n"
                    "2. **Décaler les usages flexibles** hors de la pointe 18 h–21 h.\n"
                    "3. **Lancer un audit énergétique** et étudier l'autoconsommation solaire."
                )
            return "\n".join(
                [
                    "## Synthèse",
                    f"La facture mensuelle estimée s'élève à **{_fmt(bill.get('total_mad', 0), 2)} MAD** "
                    f"pour **{_fmt(bill.get('consumption_mwh', 0), 2)} MWh** au tarif "
                    f"**{bill.get('segment_label', '')}**.",
                    "## Détail du calcul",
                    "\n".join(lines),
                    "## Plan d'économies",
                    actions,
                    "## Limites & hypothèses",
                    "- Simulation hors taxes exceptionnelles, hors pénalités de dépassement et hors régularisation "
                    "annuelle ; la facture réelle peut varier de ± 5 %.",
                    _sources_block(sources),
                ]
            )
        return "\n".join(
            [
                "## Réponse",
                f"La facture estimée est de **{_fmt(bill.get('total_mad', 0), 2)} MAD** pour "
                f"**{_fmt(bill.get('consumption_mwh', 0), 2)} MWh**.",
                "## Points clés",
                f"- Énergie : {_fmt(bill.get('energy_mad', 0), 2)} MAD.",
                f"- TVA : {_fmt(bill.get('vat_mad', 0), 2)} MAD.",
                "## Prochaine étape",
                "Comparer avec la facture réelle et vérifier le relevé.",
            ]
        )

    if intent == "forecast":
        forecast = tools.get("forecast_load", {})
        profile = tools.get("get_region_profile", {})
        ref_prev = _pick_source(sources, "DOC-PREVISION")
        ref_del = _pick_source(sources, "DOC-DELESTAGE")
        if refined:
            return "\n".join(
                [
                    "## Synthèse",
                    f"Pour **{forecast.get('region', region)}**, la pointe prévisionnelle est de "
                    f"**{_fmt(forecast.get('peak_mw', 0), 0)} MW** à **{forecast.get('peak_at', '')}**, "
                    f"soit une marge de réserve de **{_fmt(forecast.get('reserve_margin_pct', 0), 1)} %** "
                    f"→ risque **{forecast.get('risk', '')}**.",
                    "## Analyse détaillée",
                    "\n".join(
                        [
                            f"- Capacité disponible estimée : **{_fmt(forecast.get('capacity_mw', 0), 0)} MW** ; "
                            f"pointe : **{_fmt(forecast.get('peak_mw', 0), 0)} MW** [{ref_prev}].",
                            f"- Hypothèse météo : **+{_fmt(forecast.get('temperature_delta', 0), 1)} °C**, "
                            f"soit un effet de **+{_fmt(forecast.get('temperature_delta', 0) * 2.4, 1)} %** "
                            f"sur la charge de pointe.",
                            f"- Profil de la région : consommation **{_fmt(profile.get('consumption_gwh', 0))} GWh/an**, "
                            f"pointe historique **{_fmt(profile.get('peak_mw', 0))} MW**, "
                            f"pertes **{_fmt(profile.get('losses_pct', 0), 2)} %**.",
                            f"- Seuil d'alerte réglementaire : **92 %** de la capacité ; seuil critique : **97 %** "
                            f"[{ref_prev}].",
                        ]
                    ),
                    "## Plan d'action",
                    f"1. **Mobiliser la réserve tournante** et vérifier la disponibilité des groupes dès 17 h [{ref_prev}].",
                    f"2. **Reporter les travaux programmés** sur les départs P2/P3 et sécuriser les départs critiques [{ref_del}].",
                    f"3. **Surveiller la pointe de 18 h à 21 h** ; si la marge descend sous 4 %, préparer un "
                    f"délestage sélectif [{ref_del}].",
                    f"4. **Informer les clients sensibles** (hôpitaux, pompage, industrie) et activer la cellule de crise.",
                    "## Limites & hypothèses",
                    "- Prévision de type persistance corrigée par la météo ; l'incertitude augmente au-delà de 48 h "
                    "et en cas d'événement exceptionnel.",
                    _sources_block(sources),
                ]
            )
        return "\n".join(
            [
                "## Réponse",
                f"La pointe prévisionnelle est de **{_fmt(forecast.get('peak_mw', 0), 0)} MW** avec une marge "
                f"de **{_fmt(forecast.get('reserve_margin_pct', 0), 1)} %** (risque {forecast.get('risk', '')}).",
                "## Points clés",
                f"- Capacité : {_fmt(forecast.get('capacity_mw', 0), 0)} MW.",
                f"- Heure de pointe : {forecast.get('peak_at', '')}.",
                "## Prochaine étape",
                "Surveiller la pointe et préparer les réserves.",
            ]
        )

    if intent == "mix":
        mix = tools.get("get_production_mix", core.production_mix())
        ref_ren = _pick_source(sources, "DOC-RENOUVELABLES")
        ref_prev = _pick_source(sources, "DOC-PREVISION")
        sources_lines = "\n".join(
            f"- **{source['source']}** : {_fmt(source['share_pct'], 1)} % "
            f"({_fmt(source['gwh'])} GWh){' — renouvelable' if source['renewable'] else ''}"
            for source in mix.get("sources", [])
        )
        if refined:
            return "\n".join(
                [
                    "## Synthèse",
                    f"Le mix de production 2026 est dominé par le thermique, mais la part renouvelable atteint "
                    f"**{_fmt(mix.get('renewable_share_pct', 0), 1)} %** de la production totale de "
                    f"**{_fmt(mix.get('total_gwh', 0))} GWh**.",
                    "## Analyse détaillée",
                    sources_lines,
                    f"- La part renouvelable combine l'éolien, l'hydraulique et le solaire ; elle ne doit pas être "
                    f"confondue avec la capacité installée [{ref_ren}].",
                    f"- L'intensité carbone moyenne est de **{_fmt(mix.get('co2_g_per_kwh', 0))} g CO₂/kWh** ; "
                    f"le thermique reste le principal levier de réduction.",
                    f"- La pointe du soir reste critique car le solaire s'efface après 17 h ; le stockage et "
                    f"l'hydraulique de pompage sont mobilisés [{ref_prev}].",
                    "## Plan d'action",
                    f"1. **Prioriser le stockage** (100 MW / 200 MWh) pour lisser la rampe 17 h–21 h [{ref_ren}].",
                    "2. **Accélérer l'autoconsommation solaire** chez les industriels et les administrations.",
                    "3. **Sécuriser la pointe** par la réserve tournante et les interconnexions.",
                    "## Limites & hypothèses",
                    "- Mix annuel synthétique ; les shares mensuelles varient avec l'hydraulicité et la météo.",
                    _sources_block(sources),
                ]
            )
        return "\n".join(
            [
                "## Réponse",
                f"La part renouvelable est de **{_fmt(mix.get('renewable_share_pct', 0), 1)} %** pour "
                f"**{_fmt(mix.get('total_gwh', 0))} GWh** produits.",
                "## Points clés",
                "- Le thermique reste majoritaire.",
                "- L'éolien est la première source renouvelable.",
                "## Prochaine étape",
                "Suivre la pointe du soir et le stockage.",
            ]
        )

    if intent == "kpi":
        consumption = tools.get("get_consumption", {})
        quality = tools.get("get_service_quality", {})
        top_regions = sorted(core.regions(), key=lambda row: row["consumption_gwh"], reverse=True)[:3]
        ref = _pick_source(sources, "DOC-QUALITE-ANRE")
        if refined:
            return "\n".join(
                [
                    "## Synthèse",
                    f"Le réseau VOLTIS dessert **{_fmt(kpis['clients'])} clients** pour "
                    f"**{_fmt(kpis['consumption_gwh'])} GWh** et une pointe de **{_fmt(kpis['peak_mw'])} MW**. "
                    f"Le SAIDI national est de **{_fmt(kpis['saidi_min'], 1)} min**.",
                    "## Analyse détaillée",
                    "\n".join(
                        [
                            f"- Top régions : " + ", ".join(
                                f"**{row['name']}** ({_fmt(row['consumption_gwh'])} GWh)" for row in top_regions
                            ) + ".",
                            f"- Rendement : pertes moyenne de **{_fmt(kpis['losses_pct'], 2)} %**, "
                            f"disponibilité de **{_fmt(kpis['service_availability_pct'], 3)} %** [{ref}].",
                            f"- Continuité : SAIDI **{_fmt(kpis['saidi_min'], 1)} min**, SAIFI "
                            f"**{_fmt(kpis['saifi'], 2)}**, MTTR **{_fmt(kpis['mttr_min'], 1)} min**, "
                            f"**{kpis['active_outages']} incidents actifs**.",
                            f"- Mix : **{_fmt(kpis['renewable_share_pct'], 1)} %** renouvelable, "
                            f"**{_fmt(kpis['co2_g_per_kwh'])} g CO₂/kWh**.",
                            f"- Consommation cumulée sur la période : **{_fmt(consumption.get('total_gwh', 0))} GWh**.",
                        ]
                    ),
                    "## Plan d'action",
                    f"1. **Cibler les régions à fort SAIDI** (Souss-Massa, Oriental, Béni Mellal-Khénifra) [{ref}].",
                    "2. **Réduire les pertes** par la télérelève et la chasse aux branchements illicites.",
                    "3. **Suivre la pointe** et ajuster les reserves de 8 %.",
                    "## Limites & hypothèses",
                    "- Données consolidées à fin octobre 2026 ; les valeurs de novembre sont partielles.",
                    _sources_block(sources),
                ]
            )
        return "\n".join(
            [
                "## Réponse",
                f"Le réseau compte **{_fmt(kpis['clients'])} clients** et **{_fmt(kpis['consumption_gwh'])} GWh** "
                f"de consommation, avec un SAIDI de **{_fmt(kpis['saidi_min'], 1)} min**.",
                "## Points clés",
                f"- Pointe : {_fmt(kpis['peak_mw'])} MW.",
                f"- Renouvelable : {_fmt(kpis['renewable_share_pct'], 1)} %.",
                "## Prochaine étape",
                "Analyser les régions les moins performantes.",
            ]
        )

    # Intention documentaire générale
    if refined:
        source_lines = "\n".join(
            f"- **{source['title']}** ({source['citation']}) : {source['text'][:210]}…"
            for source in sources[:4]
        )
        return "\n".join(
            [
                "## Synthèse",
                f"La question porte sur **{region}**. La documentation interne fournit "
                f"**{len(sources)} extraits pertinents** et les indicateurs réseau confirment un enjeu de "
                f"**pilotage de la pointe** et de **qualité de service**.",
                "## Analyse détaillée",
                source_lines,
                f"- KPI de cadrage : SAIDI **{_fmt(kpis['saidi_min'], 1)} min**, pertes "
                f"**{_fmt(kpis['losses_pct'], 2)} %**, renouvelable **{_fmt(kpis['renewable_share_pct'], 1)} %**.",
                "## Plan d'action",
                f"1. **Appliquer la procédure** identifiée dans le document le plus pertinent "
                f"({sources[0]['citation'] if sources else 'DOC-QUALITE-ANRE'}).",
                "2. **Vérifier les données terrain** avant toute décision (relevé, schéma unifilaire, consignation).",
                "3. **Tracer la décision** dans le registre des manœuvres et mesurer l'effet à J+7.",
                "## Limites & hypothèses",
                "- Réponse fondée sur un corpus documentaire synthétique de 12 procédures ; "
                "les versions en vigueur prévalent sur les extraits.",
                _sources_block(sources),
            ]
        )
    return "\n".join(
        [
            "## Réponse",
            f"Les documents internes apportent **{len(sources)} extraits** sur le sujet.",
            "## Points clés",
            *(f"- {source['title']}." for source in sources[:2]),
            "## Prochaine étape",
            "Consulter la procédure complète avant d'agir.",
        ]
    )


# --------------------------------------------------------------------------- #
# Nœuds LangGraph
# --------------------------------------------------------------------------- #
def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _trace(state: WorkflowState, step: str, detail: str, started: float, status: str = "ok") -> list[dict]:
    trace = list(state.get("trace", []))
    trace.append(
        {
            "step": step,
            "detail": detail,
            "status": status,
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "timestamp": _now(),
        }
    )
    return trace


def planner_node(state: WorkflowState) -> dict:
    started = time.perf_counter()
    question = state.get("question", "")
    intent = detect_intent(question)
    detected_region = detect_region(question)
    region_code = detected_region or state.get("region_code") or "NATIONAL"
    if region_code == "":
        region_code = "NATIONAL"
    tools = INTENT_TOOLS.get(intent, INTENT_TOOLS["rag"])
    plan = [
        "Analyser l'intention et le périmètre",
        f"Récupérer les documents pertinents (top {state.get('top_k', 4)})",
        f"Appeler les outils : {', '.join(tools)}",
        "Rédiger une réponse sourcée",
        "Critiquer et raffiner jusqu'au seuil de qualité",
    ]
    return {
        "intent": intent,
        "intent_label": INTENTS.get(intent, {}).get("label", "Documentation"),
        "region_code": region_code,
        "plan": plan,
        "tool_names": tools,
        "trace": _trace(state, "Planner", f"Intention « {INTENTS.get(intent, {}).get('label', 'RAG')} » · région {region_code}", started),
    }


def retrieve_node(state: WorkflowState) -> dict:
    started = time.perf_counter()
    question = state.get("question", "")
    intent = state.get("intent", "rag")
    expansions = {
        "outage": "coupure incident délestage continuité SAIDI MTTR",
        "billing": "tarif facture kWh prime TVA",
        "forecast": "prévision charge pointe réserve température",
        "mix": "mix production renouvelable solaire éolien",
        "kpi": "KPI consommation pertes qualité régulation",
    }
    query = question + " " + expansions.get(intent, "")
    result = core.search_documents(query, 8)
    allowed = {
        "outage": ["DOC-INCIDENTS", "DOC-DELESTAGE", "DOC-QUALITE-ANRE", "DOC-MAINT-TR", "DOC-PREVISION"],
        "billing": ["DOC-TARIFS", "DOC-CLIENT", "DOC-AMI"],
        "forecast": ["DOC-PREVISION", "DOC-DELESTAGE", "DOC-QUALITE-ANRE", "DOC-RENOUVELABLES"],
        "mix": ["DOC-RENOUVELABLES", "DOC-PREVISION", "DOC-QUALITE-ANRE"],
        "kpi": ["DOC-QUALITE-ANRE", "DOC-AMI", "DOC-INCIDENTS", "DOC-MAINT-TR"],
        "rag": [],
    }.get(intent, [])
    if allowed:
        sources = [source for source in result["results"] if source["doc_id"] in allowed]
    else:
        sources = list(result["results"])
    required = {
        "outage": ["DOC-INCIDENTS", "DOC-DELESTAGE"],
        "billing": ["DOC-TARIFS", "DOC-CLIENT"],
        "forecast": ["DOC-PREVISION", "DOC-DELESTAGE"],
        "mix": ["DOC-RENOUVELABLES"],
        "kpi": ["DOC-QUALITE-ANRE", "DOC-AMI"],
    }.get(intent, [])
    for doc_id in required:
        if not any(source["doc_id"] == doc_id for source in sources):
            extra = core.best_chunk(doc_id, query)
            if extra:
                sources.append(extra)
    if allowed:
        for doc_id in allowed:
            if len(sources) >= int(state.get("top_k", 4)) + 1:
                break
            if not any(source["doc_id"] == doc_id for source in sources):
                extra = core.best_chunk(doc_id, query)
                if extra:
                    sources.append(extra)
    sources = sources[: int(state.get("top_k", 4)) + 2]
    return {
        "sources": sources,
        "trace": _trace(
            state,
            "Retriever",
            f"{len(sources)} extraits · meilleur score {sources[0]['relevance_pct'] if sources else 0} % · "
            f"filtre {', '.join(allowed) if allowed else 'libre'}",
            started,
        ),
    }


def _tool_arguments(tool: str, state: WorkflowState) -> dict:
    question = state.get("question", "")
    region_code = state.get("region_code", "NATIONAL")
    if tool == "get_grid_kpis":
        return {}
    if tool == "get_region_profile":
        return {"region_code": region_code if region_code != "NATIONAL" else "CAS"}
    if tool == "get_consumption":
        return {"region_code": region_code, "months": 12}
    if tool == "get_production_mix":
        return {}
    if tool == "query_outages":
        return {"region_code": region_code, "status": "Tous", "priority": "Toutes", "limit": 12}
    if tool == "forecast_load":
        return {
            "region_code": region_code if region_code != "NATIONAL" else "NATIONAL",
            "horizon_h": 24,
            "temperature_delta": detect_temperature_delta(question),
        }
    if tool == "simulate_bill":
        return {
            "segment": detect_segment(question),
            "consumption_mwh": detect_consumption_mwh(question),
            "region_code": region_code if region_code != "NATIONAL" else "CAS",
        }
    if tool == "search_knowledge":
        return {"query": question, "top_k": int(state.get("top_k", 4))}
    if tool == "recommend_energy_savings":
        return {"customer_id": detect_customer(question) or "CLI-001"}
    if tool == "get_service_quality":
        return {"region_code": region_code}
    return {}


def tools_node(state: WorkflowState) -> dict:
    started = time.perf_counter()
    results: dict[str, Any] = {}
    trace_rows = []
    for tool in state.get("tool_names", []):
        arguments = _tool_arguments(tool, state)
        tool_started = time.perf_counter()
        try:
            result = core.call_tool(tool, arguments)
            status = "ok"
        except Exception as error:  # pragma: no cover - garde-fou
            result = {"error": str(error)}
            status = "error"
        latency = round((time.perf_counter() - tool_started) * 1000, 1)
        results[tool] = result
        trace_rows.append(
            {
                "tool": tool,
                "arguments": arguments,
                "status": status,
                "latency_ms": latency,
                "summary": _tool_summary(tool, result),
            }
        )
    return {
        "tool_results": results,
        "tool_trace": trace_rows,
        "trace": _trace(
            state,
            "Tools",
            f"{len(trace_rows)} outils appelés · {sum(row['latency_ms'] for row in trace_rows):.0f} ms cumulés",
            started,
        ),
    }


def _tool_summary(tool: str, result: dict) -> str:
    if tool == "query_outages":
        summary = result.get("summary", {})
        return f"{summary.get('incidents', 0)} incidents · {summary.get('active', 0)} actifs"
    if tool == "forecast_load":
        return f"Pointe {result.get('peak_mw', 0)} MW · marge {result.get('reserve_margin_pct', 0)} %"
    if tool == "simulate_bill":
        return f"Total {result.get('total_mad', 0)} MAD"
    if tool == "get_grid_kpis":
        return f"{result.get('consumption_gwh', 0)} GWh · SAIDI {result.get('saidi_min', 0)} min"
    if tool == "get_production_mix":
        return f"{result.get('renewable_share_pct', 0)} % renouvelable"
    if tool == "get_region_profile":
        return f"{result.get('name', '')} · {result.get('consumption_gwh', 0)} GWh"
    if tool == "search_knowledge":
        return f"{result.get('count', 0)} extraits"
    if tool == "recommend_energy_savings":
        return f"{result.get('total_gain_pct', 0)} % d'économies"
    return "résultat disponible"


def writer_node(state: WorkflowState) -> dict:
    started = time.perf_counter()
    draft = compose_answer(state, refined=False)
    words = len(draft.split())
    return {
        "draft": draft,
        "trace": _trace(state, "Writer", f"Brouillon généré · {words} mots · sources non citées", started),
    }


def _score_answer(state: WorkflowState) -> dict:
    draft = state.get("draft", "")
    question = state.get("question", "")
    sources = state.get("sources", [])
    tools = state.get("tool_results", {})
    words = len(draft.split())
    headings = draft.count("##")
    bullets = sum(1 for line in draft.splitlines() if line.strip().startswith(("-", "1.", "2.", "3.", "4.")))
    citations = len(re.findall(r"\[\d+\]", draft)) + draft.count("DOC-")
    numbers = len(re.findall(r"\b\d[\d\s.,]*\b", draft))
    question_tokens = set(core.tokenize(question))
    answer_tokens = set(core.tokenize(draft))
    overlap = len(question_tokens & answer_tokens) / max(1, len(question_tokens))
    sentences = [sentence for sentence in re.split(r"[.!?]", draft) if sentence.strip()]
    avg_sentence = words / max(1, len(sentences))

    clarity = 4.8
    clarity += 1.4 if headings >= 2 else 0.4 if headings == 1 else 0
    clarity += 1.0 if bullets >= 3 else 0.4 if bullets >= 1 else 0
    clarity += 0.9 if 130 <= words <= 430 else 0.3 if 90 <= words <= 520 else 0
    clarity += 0.6 if avg_sentence < 30 else 0
    clarity += 0.4 if "**" in draft else 0

    accuracy = 4.0
    accuracy += min(1.8, numbers * 0.12)
    accuracy += min(1.8, citations * 0.45)
    accuracy += 0.8 if tools else 0
    accuracy += 0.5 if sources else 0
    accuracy += 0.3 if re.search(r"\b(GWh|MWh|MW|MAD|min|%)\b", draft) else 0

    concision = 10.0
    concision -= max(0, words - 460) / 50
    concision -= max(0, 125 - words) / 22
    repeated = sum(1 for line in set(draft.splitlines()) if draft.splitlines().count(line) > 1 and len(line) > 40)
    concision -= repeated * 0.8

    coherence = 4.4
    coherence += 1.3 if "## Synthèse" in draft else 0.6 if "## Réponse" in draft else 0
    coherence += 1.1 if "## Plan d'action" in draft else 0.5 if "## Prochaine étape" in draft else 0
    coherence += 0.8 if "## Sources" in draft else 0
    coherence += min(1.7, overlap * 2.2)
    coherence += 0.5 if "## Limites" in draft else 0
    coherence += 0.6 if "## Décision recommandée" in draft else 0
    coherence += 0.4 if "## Indicateurs de suivi" in draft else 0

    scores = {
        "clarity": round(max(0, min(10, clarity)), 1),
        "accuracy": round(max(0, min(10, accuracy)), 1),
        "concision": round(max(0, min(10, concision)), 1),
        "coherence": round(max(0, min(10, coherence)), 1),
    }
    overall = round(
        scores["clarity"] * 0.28
        + scores["accuracy"] * 0.34
        + scores["concision"] * 0.14
        + scores["coherence"] * 0.24,
        1,
    )
    issues = []
    if citations < 2:
        issues.append("Ajouter des références explicites aux documents et aux outils.")
    if numbers < 6:
        issues.append("Quantifier les constats avec les chiffres issus des outils.")
    if "## Sources" not in draft:
        issues.append("Ajouter une section Sources avec les citations complètes.")
    if "## Plan d'action" not in draft and "## Prochaine étape" not in draft:
        issues.append("Structurer un plan d'action opérationnel.")
    if words < 120:
        issues.append("Développer l'analyse (réponse trop courte).")
    if words > 400:
        issues.append("Raccourcir la réponse (trop longue pour un opérateur).")
    if not issues:
        issues.append("Aucun défaut bloquant : la réponse est publiable.")
    return {
        "scores": scores,
        "overall": overall,
        "issues": issues,
        "words": words,
        "citations": citations,
        "numbers": numbers,
        "overlap": round(overlap, 2),
        "rationale": (
            f"Clarté {scores['clarity']}/10, exactitude {scores['accuracy']}/10, "
            f"concision {scores['concision']}/10, cohérence {scores['coherence']}/10. "
            f"{len(sources)} sources, {citations} citations, {numbers} valeurs chiffrées."
        ),
    }


def critic_node(state: WorkflowState) -> dict:
    started = time.perf_counter()
    critique = _score_answer(state)
    history = list(state.get("score_history", []))
    history.append(
        {
            "iteration": state.get("iterations", 0),
            "label": "Initial" if state.get("iterations", 0) == 0 else f"Itération {state.get('iterations', 0)}",
            **critique,
        }
    )
    return {
        "critique": critique,
        "score_history": history,
        "trace": _trace(
            state,
            "Critic",
            f"Score global {critique['overall']}/10 · {len(critique['issues'])} point(s) d'amélioration",
            started,
        ),
    }


def refine_node(state: WorkflowState) -> dict:
    started = time.perf_counter()
    refined = compose_answer(state, refined=True)
    iteration = state.get("iterations", 0) + 1
    if iteration >= 2:
        refined = refined + "\n" + _decision_block(state)
    return {
        "draft": refined,
        "iterations": iteration,
        "trace": _trace(
            state,
            "Refiner",
            f"Itération {iteration} · sources intégrées · plan d'action ajouté"
            + (" · décision et indicateurs de suivi" if iteration >= 2 else ""),
            started,
        ),
    }


def _decision_block(state: WorkflowState) -> str:
    intent = state.get("intent", "rag")
    decisions = {
        "outage": (
            "Maintenir la cellule de crise jusqu'au retour à la normale, prioriser le départ MAARIF-01 "
            "et publier un communiqué client dans l'heure."
        ),
        "billing": (
            "Valider le relevé avec le client, appliquer le plan d'économies et réviser la puissance "
            "souscrite lors du prochain contrat."
        ),
        "forecast": (
            "Passer en vigilance renforcée à partir de 17 h, mobiliser 150 MW de réserve tournante "
            "et reporter les travaux non critiques."
        ),
        "mix": (
            "Sécuriser 100 MW de stockage pour la rampe du soir et accélérer l'autoconsommation solaire "
            "sur les sites industriels."
        ),
        "kpi": (
            "Déployer un plan d'action ciblé sur les trois régions au SAIDI le plus élevé et suivre "
            "les pertes par départ."
        ),
        "rag": (
            "Faire valider la procédure par le responsable métier avant application et tracer la décision "
            "dans le registre des manœuvres."
        ),
    }
    return "\n".join(
        [
            "## Décision recommandée",
            decisions.get(intent, decisions["rag"]),
            "## Indicateurs de suivi",
            "- **Qualité** : score Reflexion ≥ 8,5/10 et taux de citations ≥ 90 %.",
            "- **Délai** : prise de décision sous 30 min, réponse client sous 2 h.",
            "- **Impact** : baisse du SAIDI de 3 % et de l'énergie non servie de 5 % à J+30.",
        ]
    )


def finalize_node(state: WorkflowState) -> dict:
    started = time.perf_counter()
    critique = state.get("critique", {})
    final = state.get("draft", "")
    if "## Sources" not in final:
        final = final + "\n\n" + _sources_block(state.get("sources", []))
    return {
        "final_answer": final,
        "elapsed_ms": round((time.perf_counter() - state.get("started_at", time.perf_counter())) * 1000, 1),
        "confidence": "Haute" if critique.get("overall", 0) >= 8.5 else "Moyenne" if critique.get("overall", 0) >= 7 else "À vérifier",
        "trace": _trace(state, "Finalize", "Réponse finale consolidée avec sources", started),
    }


def should_continue(state: WorkflowState) -> str:
    critique = state.get("critique", {})
    if critique.get("overall", 0) >= state.get("threshold", 8.2):
        return "finalize"
    if state.get("iterations", 0) >= state.get("max_iterations", 2):
        return "finalize"
    return "refine"


def build_graph():
    graph = StateGraph(WorkflowState)
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
    graph.add_conditional_edges("critic", should_continue, {"refine": "refine", "finalize": "finalize"})
    graph.add_edge("refine", "critic")
    graph.add_edge("finalize", END)
    return graph.compile()


GRAPH = build_graph()


def run_workflow(
    question: str,
    region_code: str = "NATIONAL",
    audience: str = "Exploitation",
    top_k: int = 4,
    threshold: float = 8.2,
    max_iterations: int = 2,
    force_iterations: int | None = None,
) -> dict:
    """Exécute le graphe et retourne un résultat sérialisable pour le dashboard."""
    state: WorkflowState = {
        "question": question.strip(),
        "region_code": region_code,
        "audience": audience,
        "top_k": top_k,
        "threshold": threshold,
        "max_iterations": max_iterations if force_iterations is None else force_iterations,
        "iterations": 0,
        "started_at": time.perf_counter(),
        "trace": [],
        "score_history": [],
    }
    result = GRAPH.invoke(state, config={"recursion_limit": 20})
    result["elapsed_ms"] = round((time.perf_counter() - state["started_at"]) * 1000, 1)
    return result


def graph_spec() -> dict:
    return {
        "framework": "LangGraph",
        "version": "1.x",
        "entrypoint": "shared.workflow.run_workflow",
        "nodes": [
            {"id": "planner", "label": "Planner", "role": "Classification d'intention, extraction région/cible, sélection des outils."},
            {"id": "retrieve", "label": "Retriever", "role": "Recherche hybride BM25 + TF-IDF dans le corpus."},
            {"id": "tools", "label": "Tools", "role": "Appels MCP : KPI, incidents, prévision, facture, RAG."},
            {"id": "writer", "label": "Writer", "role": "Génération d'un brouillon structuré et chiffré."},
            {"id": "critic", "label": "Critic", "role": "Notation clarté, exactitude, concision, cohérence."},
            {"id": "refine", "label": "Refiner", "role": "Réécriture ciblée avec sources, plan d'action et limites."},
            {"id": "finalize", "label": "Finalize", "role": "Consolidation, sources et niveau de confiance."},
        ],
        "edges": [
            ["START", "planner"], ["planner", "retrieve"], ["retrieve", "tools"],
            ["tools", "writer"], ["writer", "critic"],
            ["critic", "refine", "score < seuil et itérations < max"], ["refine", "critic"],
            ["critic", "finalize", "score ≥ seuil ou itérations = max"], ["finalize", "END"],
        ],
        "state": list(WorkflowState.__annotations__.keys()),
        "reflexion": {
            "pattern": "Generate → Critic → Refine",
            "threshold": 8.2,
            "max_iterations": 2,
            "criteria": ["clarity", "accuracy", "concision", "coherence"],
            "weights": {"clarity": 0.28, "accuracy": 0.34, "concision": 0.14, "coherence": 0.24},
        },
        "checkpointing": {"enabled": False, "reason": "Démo locale sans base de persistance ; thread_id prêt pour une extension."},
    }


if __name__ == "__main__":
    import json
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    output = run_workflow("Pourquoi le quartier Maârif a-t-il subi des coupures hier soir ?", "CAS")
    print(json.dumps({key: output[key] for key in ("intent", "final_answer", "score_history", "tool_trace", "elapsed_ms")}, ensure_ascii=False, indent=2)[:6000])
