# -*- coding: utf-8 -*-
"""Socle métier VOLTIS — données, RAG hybride, outils MCP et simulations.

Le module ne dépend que de la bibliothèque standard (hors CSV/JSON) afin de
pouvoir être exécuté dans le dashboard, le serveur MCP, les agents A2A et les
tests sans infrastructure externe.
"""
from __future__ import annotations

import csv
import json
import math
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "de", "du", "au", "aux", "et", "ou",
    "a", "à", "en", "dans", "sur", "pour", "par", "avec", "sans", "ce", "cet",
    "cette", "ces", "il", "elle", "ils", "elles", "je", "tu", "nous", "vous",
    "on", "est", "sont", "etre", "être", "avoir", "a", "ai", "as", "ont",
    "que", "qui", "quoi", "dont", "ou", "où", "quand", "comment", "pourquoi",
    "quel", "quelle", "quels", "quelles", "mon", "ma", "mes", "notre", "nos",
    "votre", "vos", "son", "sa", "ses", "leur", "leurs", "plus", "moins", "tres",
    "très", "tout", "tous", "toute", "toutes", "aussi", "comme", "mais", "donc",
    "si", "ne", "pas", "y", "d", "l", "s", "n", "c", "j", "m", "t", "qu",
}

SYNONYMS = {
    "coupure": ["incident", "coupure", "délestage", "continuité", "saidi"],
    "coupures": ["incident", "coupure", "délestage", "continuité", "saidi"],
    "panne": ["incident", "équipement", "maintenance", "mttr"],
    "facture": ["tarif", "facturation", "kwh", "prime", "tva"],
    "facturation": ["tarif", "facture", "kwh", "prime", "tva"],
    "solaire": ["solaire", "photovoltaïque", "renouvelable", "injection"],
    "éolien": ["éolien", "renouvelable", "intermittence"],
    "renouvelable": ["renouvelable", "solaire", "éolien", "hydraulique", "stockage"],
    "renouvelables": ["renouvelable", "solaire", "éolien", "hydraulique", "stockage"],
    "pointe": ["pointe", "charge", "délestage", "réserve", "prévision"],
    "pertes": ["pertes", "techniques", "non techniques", "télérelève", "fraude"],
    "sécurité": ["sécurité", "consignation", "habilitation", "epi"],
    "cyber": ["cybersécurité", "scada", "ot", "segmentation", "mfa"],
    "compteur": ["compteur", "ami", "télérelève", "concentrateur"],
    "prévision": ["prévision", "charge", "météo", "j+1", "réserve"],
    "qualité": ["qualité", "tension", "fréquence", "harmonique", "onde"],
    "client": ["client", "réclamation", "compensation", "satisfaction"],
    "réglementation": ["anre", "régulation", "saidi", "saifi", "pénalité"],
}


# --------------------------------------------------------------------------- #
# Chargement
# --------------------------------------------------------------------------- #
def _read_json(name: str) -> Any:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _read_csv(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@lru_cache(maxsize=1)
def regions() -> list[dict]:
    return _read_json("regions.json")["regions"]


@lru_cache(maxsize=1)
def production_mix() -> dict:
    return _read_json("production_mix.json")


@lru_cache(maxsize=1)
def customers() -> list[dict]:
    return _read_json("customers.json")["customers"]


@lru_cache(maxsize=1)
def tariffs() -> dict:
    return _read_json("tariffs.json")


@lru_cache(maxsize=1)
def outages() -> list[dict]:
    rows = _read_csv("outages.csv")
    for row in rows:
        row["duration_min"] = int(row["duration_min"])
        row["customers_affected"] = int(row["customers_affected"])
        row["energy_not_served_mwh"] = float(row["energy_not_served_mwh"])
        row["mttr_min"] = int(row["mttr_min"]) if row.get("mttr_min") else None
    return rows


@lru_cache(maxsize=1)
def load_curve() -> list[dict]:
    rows = _read_csv("load_curve.csv")
    for row in rows:
        row["hour"] = int(row["hour"])
        row["load_mw"] = float(row["load_mw"])
        row["temperature_c"] = float(row["temperature_c"])
        row["is_peak"] = int(row["is_peak"])
    return rows


@lru_cache(maxsize=1)
def monthly_consumption() -> list[dict]:
    rows = _read_csv("monthly_consumption.csv")
    for row in rows:
        row["consumption_gwh"] = float(row["consumption_gwh"])
        row["peak_mw"] = float(row["peak_mw"])
        row["clients"] = int(row["clients"])
    return rows


@lru_cache(maxsize=1)
def corpus() -> list[dict]:
    return _read_json("corpus.json")["documents"]


@lru_cache(maxsize=1)
def site() -> dict:
    return _read_json("site.json")


def region_by_code(code: str) -> dict:
    code = (code or "").upper()
    for region in regions():
        if region["code"] == code:
            return region
    return {}


def region_name(code: str) -> str:
    return region_by_code(code).get("name", code)


def customer_by_id(customer_id: str) -> dict:
    for customer in customers():
        if customer["customer_id"].lower() == str(customer_id).lower():
            return customer
    return {}


# --------------------------------------------------------------------------- #
# KPI et statistiques
# --------------------------------------------------------------------------- #
def national_kpis() -> dict:
    total_consumption = sum(region["consumption_gwh"] for region in regions())
    total_clients = sum(region["clients"] for region in regions())
    total_peak = sum(region["peak_mw"] for region in regions())
    saidi = sum(region["saidi_min"] * region["clients"] for region in regions()) / total_clients
    saifi = sum(region["saifi"] * region["clients"] for region in regions()) / total_clients
    losses = sum(region["losses_pct"] * region["consumption_gwh"] for region in regions()) / total_consumption
    active = [row for row in outages() if row["status"] == "En cours"]
    resolved = [row for row in outages() if row["status"] == "Résolu" and row["mttr_min"]]
    mttr = statistics.mean(row["mttr_min"] for row in resolved) if resolved else 0
    return {
        "regions": len(regions()),
        "consumption_gwh": round(total_consumption, 1),
        "clients": total_clients,
        "peak_mw": round(total_peak, 1),
        "renewable_share_pct": production_mix()["renewable_share_pct"],
        "losses_pct": round(losses, 2),
        "saidi_min": round(saidi, 1),
        "saifi": round(saifi, 2),
        "active_outages": len(active),
        "mttr_min": round(mttr, 1),
        "outages_90d": len(outages()),
        "co2_g_per_kwh": production_mix()["co2_g_per_kwh"],
        "customers_tracked": len(customers()),
        "service_availability_pct": round(100 - (saidi / (365 * 24 * 60)) * 100, 3),
    }


def region_table() -> list[dict]:
    enriched = []
    for region in regions():
        enriched.append(
            {
                **region,
                "consumption_twh": round(region["consumption_gwh"] / 1000, 2),
                "clients_m": round(region["clients"] / 1_000_000, 2),
                "load_factor": round(region["consumption_gwh"] * 1000 / (region["peak_mw"] * 8760), 2),
            }
        )
    return sorted(enriched, key=lambda row: row["consumption_gwh"], reverse=True)


def consumption_series(region_code: str | None = None) -> list[dict]:
    rows = monthly_consumption()
    if region_code and region_code != "NATIONAL":
        return [row for row in rows if row["region_code"] == region_code]
    aggregated: dict[str, dict] = {}
    for row in rows:
        bucket = aggregated.setdefault(
            row["month"], {"month": row["month"], "consumption_gwh": 0.0, "clients": 0, "peak_mw": 0.0, "region": "National"}
        )
        bucket["consumption_gwh"] += row["consumption_gwh"]
        bucket["clients"] += row["clients"]
        bucket["peak_mw"] += row["peak_mw"]
    for bucket in aggregated.values():
        bucket["consumption_gwh"] = round(bucket["consumption_gwh"], 1)
        bucket["peak_mw"] = round(bucket["peak_mw"], 1)
    return [aggregated[key] for key in sorted(aggregated)]


def outage_summary(region_code: str | None = None) -> dict:
    rows = outages()
    if region_code and region_code != "NATIONAL":
        rows = [row for row in rows if row["region_code"] == region_code]
    resolved = [row for row in rows if row["status"] == "Résolu" and row["mttr_min"]]
    causes = Counter(row["cause"] for row in rows)
    priorities = Counter(row["priority"] for row in rows)
    return {
        "incidents": len(rows),
        "resolved": sum(1 for row in rows if row["status"] == "Résolu"),
        "active": sum(1 for row in rows if row["status"] == "En cours"),
        "planned": sum(1 for row in rows if row["status"] == "Planifié"),
        "mttr_min": round(statistics.mean(row["mttr_min"] for row in resolved), 1) if resolved else 0,
        "customers_affected": sum(row["customers_affected"] for row in rows),
        "energy_not_served_mwh": round(sum(row["energy_not_served_mwh"] for row in rows), 1),
        "by_cause": dict(causes.most_common()),
        "by_priority": dict(priorities),
    }


def service_quality(region_code: str | None = None) -> dict:
    if region_code and region_code != "NATIONAL":
        region = region_by_code(region_code)
        if not region:
            return {}
        return {
            "region": region["name"],
            "saidi_min": region["saidi_min"],
            "saifi": region["saifi"],
            "losses_pct": region["losses_pct"],
            "availability_pct": round(100 - (region["saidi_min"] / (365 * 24 * 60)) * 100, 3),
            "regulatory_target_saidi": 300,
            "status": "Conforme" if region["saidi_min"] <= 300 else "À surveiller",
        }
    kpis = national_kpis()
    return {
        "region": "National",
        "saidi_min": kpis["saidi_min"],
        "saifi": kpis["saifi"],
        "losses_pct": kpis["losses_pct"],
        "availability_pct": kpis["service_availability_pct"],
        "regulatory_target_saidi": 300,
        "status": "Conforme" if kpis["saidi_min"] <= 300 else "À surveiller",
    }


# --------------------------------------------------------------------------- #
# Prévision de charge
# --------------------------------------------------------------------------- #
def forecast_load(region_code: str = "NATIONAL", horizon_h: int = 24, temperature_delta: float = 0.0) -> dict:
    horizon_h = max(1, min(int(horizon_h), 72))
    rows = load_curve()
    dates = sorted({row["date"] for row in rows})
    last_date = dates[-1]
    baseline = [row for row in rows if row["date"] == last_date]
    if region_code and region_code != "NATIONAL":
        baseline = [row for row in baseline if row["region_code"] == region_code]
    by_hour: dict[int, list[float]] = defaultdict(list)
    for row in baseline:
        by_hour[row["hour"]].append(row["load_mw"])
    capacity = (
        region_by_code(region_code)["peak_mw"] * 1.02
        if region_code and region_code != "NATIONAL"
        else sum(region["peak_mw"] for region in regions()) * 1.02
    )
    tomorrow = datetime.fromisoformat(dates[-1]) + timedelta(days=1)
    temperature_factor = 1 + (0.024 if temperature_delta >= 0 else 0.028) * abs(temperature_delta)
    series = []
    for step in range(horizon_h):
        moment = tomorrow + timedelta(hours=step)
        values = by_hour.get(moment.hour, [0])
        base_value = sum(values) if region_code == "NATIONAL" else statistics.mean(values)
        value = base_value * 1.015 * temperature_factor
        value *= 1 + 0.015 * math.sin((step / max(horizon_h, 1)) * 2 * math.pi)
        series.append(
            {
                "timestamp": moment.strftime("%Y-%m-%d %H:%M"),
                "hour": moment.hour,
                "load_mw": round(value, 1),
            }
        )
    peak = max(series, key=lambda row: row["load_mw"])
    reserve_pct = round((capacity - peak["load_mw"]) / capacity * 100, 1)
    risk = "Critique" if reserve_pct < 4 else "Élevé" if reserve_pct < 14 else "Modéré" if reserve_pct < 22 else "Faible"
    return {
        "region": region_name(region_code) if region_code != "NATIONAL" else "National",
        "region_code": region_code or "NATIONAL",
        "horizon_h": horizon_h,
        "temperature_delta": temperature_delta,
        "capacity_mw": round(capacity, 1),
        "peak_mw": peak["load_mw"],
        "peak_at": peak["timestamp"],
        "reserve_margin_pct": reserve_pct,
        "risk": risk,
        "series": series,
        "recommendation": _forecast_recommendation(risk),
    }


def _forecast_recommendation(risk: str) -> str:
    return {
        "Critique": "Activer la réserve tournante, préparer un délestage sélectif et alerter le dispatching national.",
        "Élevé": "Mobiliser les moyens de pointe, reporter les travaux programmés et surveiller les départs P3.",
        "Modéré": "Maintenir la surveillance renforcée de 18 h à 21 h et vérifier la disponibilité des groupes.",
        "Faible": "Aucune action exceptionnelle : poursuivre le plan de conduite normal.",
    }[risk]


# --------------------------------------------------------------------------- #
# Facturation
# --------------------------------------------------------------------------- #
def simulate_bill(segment: str, consumption_mwh: float, region_code: str = "CAS") -> dict:
    segment = (segment or "residentiel").lower()
    if segment not in tariffs():
        segment = "residentiel"
    tariff = tariffs()[segment]
    consumption_kwh = max(0.0, float(consumption_mwh) * 1000)
    remaining = consumption_kwh
    lines = []
    for tier in tariff["tiers"]:
        if remaining <= 0:
            break
        capacity = math.inf if tier["max_kwh"] is None else tier["max_kwh"] - tier["min_kwh"]
        used = min(remaining, capacity)
        amount = used * tier["price_kwh"]
        if used > 0:
            lines.append(
                {
                    "label": f"Tranche {tier['min_kwh']}-{tier['max_kwh'] or '∞'} kWh",
                    "kwh": round(used, 1),
                    "price_kwh": tier["price_kwh"],
                    "amount_mad": round(amount, 2),
                }
            )
        remaining -= used
    energy = sum(line["amount_mad"] for line in lines)
    vat = energy * tariff["vat_pct"] / 100
    municipal = energy * tariff["municipal_tax_pct"] / 100
    total = energy + tariff["fixed_fee"] + vat + municipal
    return {
        "segment": segment,
        "segment_label": tariff["label"],
        "region": region_name(region_code),
        "consumption_kwh": round(consumption_kwh, 1),
        "consumption_mwh": round(consumption_kwh / 1000, 3),
        "lines": lines,
        "energy_mad": round(energy, 2),
        "fixed_fee_mad": tariff["fixed_fee"],
        "vat_pct": tariff["vat_pct"],
        "vat_mad": round(vat, 2),
        "municipal_tax_pct": tariff["municipal_tax_pct"],
        "municipal_tax_mad": round(municipal, 2),
        "total_mad": round(total, 2),
        "average_price_mad_kwh": round(total / consumption_kwh, 4) if consumption_kwh else 0,
        "currency": "MAD",
    }


def recommend_energy_savings(customer_id: str) -> dict:
    customer = customer_by_id(customer_id)
    if not customer:
        return {"error": f"Client inconnu : {customer_id}"}
    segment = customer["segment"]
    annual = customer["annual_mwh"]
    bill = customer["bill_mad_month"] * 12
    actions = []
    if segment == "industriel":
        actions = [
            ("Audit énergétique des procédés", 0.07, "Identifier les moteurs et fours surdimensionnés."),
            ("Décalage de la charge vers les heures creuses", 0.05, "Lisser la pointe de 18 h à 21 h."),
            ("Compensation de l'énergie réactive", 0.03, "Relever le facteur de puissance au-delà de 0,95."),
            ("Récupération de chaleur fatale", 0.04, "Préchauffer les process ou l'eau chaude."),
        ]
    elif segment == "agricole":
        actions = [
            ("Programmation du pompage solaire", 0.12, "Pomper entre 10 h et 15 h au lieu de la pointe du soir."),
            ("Variation de fréquence des pompes", 0.06, "Réduire la consommation de 6 à 10 %."),
            ("Remplacement des pompes anciennes", 0.08, "Gain moyen de 8 % sur le poste pompage."),
        ]
    elif segment == "administration":
        actions = [
            ("Relamping LED et détection de présence", 0.10, "Éclairage : 25 à 35 % de la facture."),
            ("Programmation CVC", 0.06, "Consignes 24 °C été / 20 °C hiver."),
            ("Solaire en autoconsommation", 0.09, "Couverture de 20 % des besoins diurnes."),
        ]
    elif segment == "commercial":
        actions = [
            ("Pilotage du froid commercial", 0.08, "Décaler le froid hors pointe."),
            ("Éclairage LED et vitrines", 0.07, "Réduction de 30 % du poste éclairage."),
            ("Solaire en autoconsommation", 0.10, "Toiture ou ombrière de parking."),
        ]
    else:
        actions = [
            ("Passage aux LED", 0.06, "Éclairage : 15 à 20 % de la facture résidentielle."),
            ("Programmation du chauffe-eau", 0.05, "Chauffer l'eau en heures creuses."),
            ("Entretien des climatiseurs", 0.04, "Nettoyage des filtres et réglage à 26 °C."),
        ]
    flexibility = customer["flexibility_score"]
    rows = []
    for label, gain, comment in actions:
        adjusted = gain * (0.75 + flexibility * 0.5)
        rows.append(
            {
                "action": label,
                "gain_pct": round(adjusted * 100, 1),
                "gain_mwh": round(annual * adjusted, 1),
                "gain_mad": round(bill * adjusted, 0),
                "comment": comment,
            }
        )
    total_gain = sum(row["gain_pct"] for row in rows)
    return {
        "customer_id": customer["customer_id"],
        "customer_name": customer["name"],
        "segment": segment,
        "annual_mwh": annual,
        "annual_bill_mad": round(bill, 0),
        "actions": rows,
        "total_gain_pct": round(total_gain, 1),
        "total_gain_mad": round(sum(row["gain_mad"] for row in rows), 0),
        "total_gain_mwh": round(sum(row["gain_mwh"] for row in rows), 1),
        "priority": "Haute" if flexibility > 0.7 else "Moyenne",
    }


# --------------------------------------------------------------------------- #
# Recherche documentaire hybride (BM25 + TF-IDF cosinus)
# --------------------------------------------------------------------------- #
def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.lower()


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+(?:[+#][a-z0-9]+)?", normalize(text))
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


@lru_cache(maxsize=1)
def _chunks() -> list[dict]:
    rows = []
    for document in corpus():
        doc_tokens = tokenize(
            document["title"] + " " + document["summary"] + " " + " ".join(document["keywords"])
        )
        for index, chunk in enumerate(document["chunks"]):
            tokens = tokenize(chunk["text"])
            rows.append(
                {
                    "doc_id": document["doc_id"],
                    "title": document["title"],
                    "category": document["category"],
                    "version": document["version"],
                    "date": document["date"],
                    "owner": document["owner"],
                    "article": index + 1,
                    "text": chunk["text"],
                    "tokens": tokens,
                    "doc_tokens": doc_tokens,
                    "citation": f"{document['doc_id']} · v{document['version']} · article {index + 1}",
                }
            )
    return rows


@lru_cache(maxsize=1)
def _bm25_stats() -> dict:
    chunks = _chunks()
    document_frequency = Counter()
    for chunk in chunks:
        for token in set(chunk["tokens"]):
            document_frequency[token] += 1
    return {
        "df": document_frequency,
        "avgdl": statistics.mean(len(chunk["tokens"]) for chunk in chunks),
        "n": len(chunks),
    }


def _bm25(query_tokens: list[str], chunk: dict, k1: float = 1.5, b: float = 0.75) -> float:
    stats = _bm25_stats()
    frequencies = Counter(chunk["tokens"])
    length = len(chunk["tokens"]) or 1
    score = 0.0
    for token in query_tokens:
        if token not in frequencies:
            continue
        df = stats["df"].get(token, 0)
        idf = math.log(1 + (stats["n"] - df + 0.5) / (df + 0.5))
        tf = frequencies[token]
        score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * length / stats["avgdl"]))
    return score


def _tfidf_cosine(query_tokens: list[str], chunk: dict) -> float:
    query = Counter(query_tokens)
    document = Counter(chunk["tokens"])
    vocabulary = set(query) | set(document)
    if not vocabulary:
        return 0.0
    dot = sum(query[token] * document[token] for token in vocabulary)
    qnorm = math.sqrt(sum(value * value for value in query.values()))
    dnorm = math.sqrt(sum(value * value for value in document.values()))
    return dot / (qnorm * dnorm) if qnorm and dnorm else 0.0


def _expand(query_tokens: list[str]) -> list[str]:
    expanded = list(query_tokens)
    for token in query_tokens:
        expanded.extend(tokenize(" ".join(SYNONYMS.get(token, []))))
    return list(dict.fromkeys(expanded))


def search_documents(query: str, top_k: int = 4) -> dict:
    query_tokens = _expand(tokenize(query))
    if not query_tokens:
        return {"query": query, "results": [], "count": 0}
    chunks = _chunks()
    scores = []
    for chunk in chunks:
        bm25 = _bm25(query_tokens, chunk)
        cosine = _tfidf_cosine(query_tokens, chunk)
        keyword_hits = sum(1 for keyword in chunk["doc_tokens"] if keyword in query_tokens)
        title_bonus = 0.08 * keyword_hits
        phrase_bonus = 0.12 if normalize(query).strip() in normalize(chunk["text"]) else 0.0
        scores.append((0.66 * bm25 + 0.86 * cosine + title_bonus + phrase_bonus, chunk))
    maximum = max(score for score, _ in scores) or 1.0
    results = []
    for score, chunk in sorted(scores, key=lambda item: item[0], reverse=True)[: max(1, min(int(top_k), 8))]:
        results.append(
            {
                "doc_id": chunk["doc_id"],
                "title": chunk["title"],
                "category": chunk["category"],
                "version": chunk["version"],
                "date": chunk["date"],
                "owner": chunk["owner"],
                "article": chunk["article"],
                "text": chunk["text"],
                "citation": chunk["citation"],
                "score": round(score / maximum, 4),
                "relevance_pct": round(min(99, (score / maximum) * 100), 1),
            }
        )
    return {"query": query, "results": results, "count": len(results), "retriever": "BM25 + TF-IDF (hybride)"}


def best_chunk(doc_id: str, query: str) -> dict | None:
    """Meilleur extrait d'un document imposé (diversité du retrieval)."""
    chunks = [chunk for chunk in _chunks() if chunk["doc_id"] == doc_id]
    if not chunks:
        return None
    query_tokens = _expand(tokenize(query))
    chunk = max(chunks, key=lambda item: _tfidf_cosine(query_tokens, item))
    return {
        "doc_id": chunk["doc_id"],
        "title": chunk["title"],
        "category": chunk["category"],
        "version": chunk["version"],
        "date": chunk["date"],
        "owner": chunk["owner"],
        "article": chunk["article"],
        "text": chunk["text"],
        "citation": chunk["citation"],
        "score": 0.75,
        "relevance_pct": 75.0,
    }


# --------------------------------------------------------------------------- #
# Catalogue d'outils MCP
# --------------------------------------------------------------------------- #
TOOL_SPECS = [
    {
        "name": "get_grid_kpis",
        "description": "KPI nationaux du réseau : consommation, pointe, clients, pertes, SAIDI, SAIFI, renouvelable.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "category": "Analytics",
    },
    {
        "name": "get_region_profile",
        "description": "Profil détaillé d'une région : consommation, pointe, clients, pertes, qualité de service.",
        "inputSchema": {
            "type": "object",
            "properties": {"region_code": {"type": "string", "enum": [r["code"] for r in regions()]}},
            "required": ["region_code"],
        },
        "category": "Analytics",
    },
    {
        "name": "get_consumption",
        "description": "Série mensuelle de consommation pour une région ou le niveau national.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "region_code": {"type": "string", "default": "NATIONAL"},
                "months": {"type": "integer", "minimum": 1, "maximum": 24, "default": 12},
            },
            "required": [],
        },
        "category": "Analytics",
    },
    {
        "name": "get_production_mix",
        "description": "Mix de production électrique national et part renouvelable.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "category": "Analytics",
    },
    {
        "name": "query_outages",
        "description": "Liste et agrège les incidents réseau (coupures) avec filtres région, statut et priorité.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "region_code": {"type": "string", "default": "NATIONAL"},
                "status": {"type": "string", "enum": ["Tous", "Résolu", "En cours", "Planifié"], "default": "Tous"},
                "priority": {"type": "string", "enum": ["Toutes", "P1", "P2", "P3"], "default": "Toutes"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
            },
            "required": [],
        },
        "category": "Exploitation",
    },
    {
        "name": "forecast_load",
        "description": "Prévision horaire de charge, pointe, marge de réserve et niveau de risque.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "region_code": {"type": "string", "default": "NATIONAL"},
                "horizon_h": {"type": "integer", "minimum": 1, "maximum": 72, "default": 24},
                "temperature_delta": {"type": "number", "minimum": -10, "maximum": 15, "default": 0},
            },
            "required": [],
        },
        "category": "Prévision",
    },
    {
        "name": "simulate_bill",
        "description": "Simule une facture d'électricité selon le segment tarifaire et la consommation mensuelle.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "segment": {"type": "string", "enum": list(tariffs().keys()), "default": "residentiel"},
                "consumption_mwh": {"type": "number", "minimum": 0, "maximum": 100000, "default": 0.35},
                "region_code": {"type": "string", "default": "CAS"},
            },
            "required": ["segment", "consumption_mwh"],
        },
        "category": "Commercial",
    },
    {
        "name": "search_knowledge",
        "description": "Recherche hybride (BM25 + TF-IDF) dans les procédures et référentiels internes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "minLength": 3},
                "top_k": {"type": "integer", "minimum": 1, "maximum": 8, "default": 4},
            },
            "required": ["query"],
        },
        "category": "RAG",
    },
    {
        "name": "recommend_energy_savings",
        "description": "Plan d'économies d'énergie personnalisé pour un client suivi.",
        "inputSchema": {
            "type": "object",
            "properties": {"customer_id": {"type": "string", "enum": [c["customer_id"] for c in customers()]}},
            "required": ["customer_id"],
        },
        "category": "Commercial",
    },
    {
        "name": "get_service_quality",
        "description": "Indicateurs réglementaires de continuité et de qualité pour une région.",
        "inputSchema": {
            "type": "object",
            "properties": {"region_code": {"type": "string", "default": "NATIONAL"}},
            "required": [],
        },
        "category": "Qualité",
    },
]


def list_tools() -> list[dict]:
    return TOOL_SPECS


def call_tool(name: str, arguments: dict | None = None) -> dict:
    arguments = arguments or {}
    if name == "get_grid_kpis":
        return national_kpis()
    if name == "get_region_profile":
        region = region_by_code(arguments.get("region_code", "CAS"))
        if not region:
            return {"error": f"Région inconnue : {arguments.get('region_code')}"}
        return {**region, "quality": service_quality(region["code"])}
    if name == "get_consumption":
        code = arguments.get("region_code", "NATIONAL")
        series = consumption_series(code)
        months = int(arguments.get("months", 12))
        return {
            "region": region_name(code) if code != "NATIONAL" else "National",
            "series": series[-months:],
            "total_gwh": round(sum(row["consumption_gwh"] for row in series[-months:]), 1),
        }
    if name == "get_production_mix":
        return production_mix()
    if name == "query_outages":
        code = arguments.get("region_code", "NATIONAL")
        status = arguments.get("status", "Tous")
        priority = arguments.get("priority", "Toutes")
        limit = int(arguments.get("limit", 10))
        rows = outages()
        if code and code != "NATIONAL":
            rows = [row for row in rows if row["region_code"] == code]
        if status and status != "Tous":
            rows = [row for row in rows if row["status"] == status]
        if priority and priority != "Toutes":
            rows = [row for row in rows if row["priority"] == priority]
        return {
            "region": region_name(code) if code != "NATIONAL" else "National",
            "summary": outage_summary(code),
            "incidents": rows[:limit],
            "total_matching": len(rows),
        }
    if name == "forecast_load":
        return forecast_load(
            arguments.get("region_code", "NATIONAL"),
            int(arguments.get("horizon_h", 24)),
            float(arguments.get("temperature_delta", 0)),
        )
    if name == "simulate_bill":
        return simulate_bill(
            arguments.get("segment", "residentiel"),
            float(arguments.get("consumption_mwh", 0.35)),
            arguments.get("region_code", "CAS"),
        )
    if name == "search_knowledge":
        return search_documents(arguments.get("query", ""), int(arguments.get("top_k", 4)))
    if name == "recommend_energy_savings":
        return recommend_energy_savings(arguments.get("customer_id", "CLI-001"))
    if name == "get_service_quality":
        return service_quality(arguments.get("region_code", "NATIONAL"))
    return {"error": f"Outil inconnu : {name}"}


def mcp_manifest() -> dict:
    return {
        "schema": "volt-is.mcp/1.0",
        "server": {
            "name": "volt-is-grid-mcp",
            "version": "1.0.0",
            "description": "Serveur MCP VOLTIS exposant les données et procédures du réseau électrique.",
            "transport": ["stdio", "streamable-http", "sse"],
            "endpoint": "http://127.0.0.1:8100/mcp",
            "health": "http://127.0.0.1:8100/api/health",
            "protocol_version": "2025-06-18",
        },
        "capabilities": {"tools": {"listChanged": True}, "resources": {"subscribe": False}, "prompts": {}},
        "tools": TOOL_SPECS,
        "resources": [
            {"uri": "volt-is://corpus/index", "name": "Index documentaire", "mimeType": "application/json"},
            {"uri": "volt-is://grid/kpis", "name": "KPI réseau", "mimeType": "application/json"},
            {"uri": "volt-is://grid/regions", "name": "Régions et profils", "mimeType": "application/json"},
        ],
        "prompts": [
            {
                "name": "diagnostic_incident",
                "description": "Analyser un incident et proposer un plan d'action priorisé.",
                "arguments": ["incident_id", "region_code"],
            },
            {
                "name": "briefing_dispatching",
                "description": "Produire le briefing de pointe du jour avec risques et actions.",
                "arguments": ["region_code", "temperature_delta"],
            },
        ],
    }


# --------------------------------------------------------------------------- #
# Tâches de référence et divers
# --------------------------------------------------------------------------- #
BENCHMARK_TASKS = [
    {
        "id": "T1",
        "question": "Pourquoi le quartier Maârif a-t-il subi des coupures hier soir et que doit faire l'exploitation ?",
        "region_code": "CAS",
        "expected_tools": ["query_outages", "search_knowledge"],
        "expected_docs": ["DOC-INCIDENTS", "DOC-DELESTAGE"],
    },
    {
        "id": "T2",
        "question": "Quel est le mix de production national et quelle est la part des renouvelables ?",
        "region_code": "NATIONAL",
        "expected_tools": ["get_production_mix", "get_grid_kpis"],
        "expected_docs": ["DOC-RENOUVELABLES"],
    },
    {
        "id": "T3",
        "question": "Simule la facture mensuelle d'un client industriel qui consomme 250 MWh à Casablanca.",
        "region_code": "CAS",
        "expected_tools": ["simulate_bill"],
        "expected_docs": ["DOC-TARIFS"],
    },
    {
        "id": "T4",
        "question": "Quel est le risque de surcharge sur le réseau de Casablanca à 19 h demain si la température monte de 5 °C ?",
        "region_code": "CAS",
        "expected_tools": ["forecast_load", "get_region_profile"],
        "expected_docs": ["DOC-PREVISION", "DOC-DELESTAGE"],
    },
    {
        "id": "T5",
        "question": "Quelles actions permettent de réduire les pertes techniques et non techniques de deux points ?",
        "region_code": "NATIONAL",
        "expected_tools": ["search_knowledge", "get_service_quality"],
        "expected_docs": ["DOC-AMI", "DOC-CODE-RESEAU"],
    },
]

AGENT_CAPABILITIES = {
    "grid-analyst": {
        "label": "Grid Analyst",
        "description": "Analyse la consommation, le mix de production et les KPI réseau.",
        "keywords": ["consommation", "production", "mix", "kpi", "région", "charge", "renouvelable", "clients", "pertes"],
        "tools": ["get_grid_kpis", "get_region_profile", "get_consumption", "get_production_mix"],
        "port": 8102,
        "icon": "grid",
    },
    "outage-inspector": {
        "label": "Outage Inspector",
        "description": "Diagnostique les incidents, coupures, causes et indicateurs de continuité.",
        "keywords": ["coupure", "incident", "panne", "délestage", "saidi", "saifi", "mttr", "urgence", "réseau"],
        "tools": ["query_outages", "get_service_quality", "search_knowledge"],
        "port": 8103,
        "icon": "alert",
    },
    "billing-advisor": {
        "label": "Billing Advisor",
        "description": "Simule les factures, explique les tarifs et propose des économies d'énergie.",
        "keywords": ["facture", "tarif", "prix", "client", "économies", "kwh", "mad", "consommation", "abonnement"],
        "tools": ["simulate_bill", "recommend_energy_savings"],
        "port": 8104,
        "icon": "billing",
    },
    "forecast-agent": {
        "label": "Forecast Agent",
        "description": "Prévoit la charge, la pointe, la marge de réserve et le risque de tension.",
        "keywords": ["prévision", "demain", "pointe", "risque", "surcharge", "réserve", "météo", "température", "19h"],
        "tools": ["forecast_load", "get_grid_kpis"],
        "port": 8105,
        "icon": "forecast",
    },
}


def benchmark_tasks() -> list[dict]:
    return BENCHMARK_TASKS


def data_freshness() -> dict:
    return {
        "regions": len(regions()),
        "outages": len(outages()),
        "load_rows": len(load_curve()),
        "customers": len(customers()),
        "documents": len(corpus()),
        "chunks": len(_chunks()),
        "tools": len(TOOL_SPECS),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


if __name__ == "__main__":
    print(json.dumps(national_kpis(), ensure_ascii=False, indent=2))
    print(json.dumps(search_documents("délestage pointe de charge", 2), ensure_ascii=False, indent=2)[:1200])
