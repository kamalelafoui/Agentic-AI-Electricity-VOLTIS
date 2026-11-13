# -*- coding: utf-8 -*-
"""Génère le jeu de données synthétique de VOLTIS (réseau électrique marocain).

Toutes les données sont fictives mais calibrées sur des ordres de grandeur
réalistes. Aucun document confidentiel n'est utilisé.
"""
from __future__ import annotations

import csv
import json
import math
import random
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CORPUS_DIR = DATA / "corpus"
DATA.mkdir(exist_ok=True)
CORPUS_DIR.mkdir(exist_ok=True)

random.seed(20261112)

REGIONS = [
    # name, code, population_m, clients, consumption_gwh, peak_mw, renewable_pct, losses_pct, saidi, saifi
    ("Casablanca-Settat", "CAS", 7.6, 2_140_000, 11_200, 3_260, 18.0, 7.8, 210, 4.2),
    ("Rabat-Salé-Kénitra", "RSK", 4.9, 1_360_000, 6_800, 1_980, 22.0, 7.2, 165, 3.4),
    ("Marrakech-Safi", "MRS", 4.7, 1_250_000, 5_600, 1_620, 31.0, 8.6, 245, 4.9),
    ("Fès-Meknès", "FES", 4.4, 1_180_000, 5_200, 1_510, 24.0, 8.1, 230, 4.5),
    ("Tanger-Tétouan-Al Hoceïma", "TTA", 4.0, 1_050_000, 4_900, 1_430, 38.0, 7.4, 195, 3.9),
    ("Souss-Massa", "SOM", 3.1, 860_000, 3_800, 1_180, 35.0, 9.2, 260, 5.1),
    ("Oriental", "ORI", 2.6, 690_000, 2_900, 960, 21.0, 8.9, 275, 5.4),
    ("Béni Mellal-Khénifra", "BMK", 2.7, 720_000, 1_900, 890, 29.0, 9.5, 285, 5.6),
]

PRODUCTION_MIX = [
    {"source": "Thermique (charbon, gaz)", "share_pct": 57.0, "gwh": 24_111, "color": "#546E8A", "renewable": False},
    {"source": "Éolien", "share_pct": 16.5, "gwh": 6_980, "color": "#16A6A1", "renewable": True},
    {"source": "Hydraulique", "share_pct": 12.0, "gwh": 5_076, "color": "#3B82C4", "renewable": True},
    {"source": "Solaire", "share_pct": 9.5, "gwh": 4_019, "color": "#F4B400", "renewable": True},
    {"source": "Import / interconnexion", "share_pct": 5.0, "gwh": 2_115, "color": "#8E6BBF", "renewable": False},
]

TARIFFS = {
    "residentiel": {
        "label": "Résidentiel (BT)",
        "currency": "MAD",
        "tiers": [
            {"min_kwh": 0, "max_kwh": 100, "price_kwh": 0.9010},
            {"min_kwh": 101, "max_kwh": 200, "price_kwh": 1.0730},
            {"min_kwh": 201, "max_kwh": 300, "price_kwh": 1.2120},
            {"min_kwh": 301, "max_kwh": 500, "price_kwh": 1.3450},
            {"min_kwh": 501, "max_kwh": None, "price_kwh": 1.5120},
        ],
        "fixed_fee": 26.0,
        "vat_pct": 14.0,
        "municipal_tax_pct": 7.0,
    },
    "commercial": {
        "label": "Commercial & services (MT/BT)",
        "currency": "MAD",
        "tiers": [{"min_kwh": 0, "max_kwh": None, "price_kwh": 1.4200}],
        "fixed_fee": 145.0,
        "vat_pct": 20.0,
        "municipal_tax_pct": 0.0,
    },
    "industriel": {
        "label": "Industriel (MT, > 1 GWh/an)",
        "currency": "MAD",
        "tiers": [
            {"min_kwh": 0, "max_kwh": 200_000, "price_kwh": 1.1800},
            {"min_kwh": 200_001, "max_kwh": None, "price_kwh": 0.9850},
        ],
        "fixed_fee": 2_400.0,
        "vat_pct": 20.0,
        "municipal_tax_pct": 0.0,
    },
    "agricole": {
        "label": "Agricole (BT, pompage)",
        "currency": "MAD",
        "tiers": [{"min_kwh": 0, "max_kwh": None, "price_kwh": 0.8300}],
        "fixed_fee": 40.0,
        "vat_pct": 7.0,
        "municipal_tax_pct": 0.0,
    },
    "administration": {
        "label": "Administration & éclairage public",
        "currency": "MAD",
        "tiers": [{"min_kwh": 0, "max_kwh": None, "price_kwh": 1.2900}],
        "fixed_fee": 90.0,
        "vat_pct": 20.0,
        "municipal_tax_pct": 0.0,
    },
}

OUTAGE_CAUSES = [
    ("Végétation", 0.20, 95),
    ("Équipement défaillant", 0.19, 175),
    ("Surcharge réseau", 0.17, 70),
    ("Météo extrême", 0.14, 240),
    ("Travaux programmés", 0.12, 300),
    ("Poste / transformateur", 0.10, 205),
    ("Cause externe (chantier)", 0.08, 130),
]

FEEDERS = {
    "CAS": ["MAARIF-01", "SIDI-BELYOUT-03", "AIN-SEBAÂ-02", "NOUACEUR-05", "BOUCHERON-04"],
    "RSK": ["AGDAL-02", "SALE-04", "TEMARA-01", "KENITRA-06", "SKHIRAT-03"],
    "MRS": ["GUELIZ-01", "MENARA-02", "SAFI-05", "ESSAOUIRA-03", "CHICHAOUA-04"],
    "FES": ["MEDINA-02", "ZOUAGHA-01", "MEKNES-04", "TAZA-03", "IFRANE-05"],
    "TTA": ["TANGER-MED-01", "TETOUAN-02", "ALHOCEIMA-04", "LARACHE-03", "CHEFCHAOUEN-05"],
    "SOM": ["AGADIR-01", "TIZNIT-03", "TAROUDANT-02", "OUARZAZATE-04", "Chtouka-05"],
    "ORI": ["OUJDA-01", "NADOR-02", "BERKANE-03", "TAOURIRT-04", "JERADA-05"],
    "BMK": ["BENI-MELLAL-01", "KHENIFRA-02", "FQUIH-BENSALAH-03", "AZILAL-04", "KASBA-TADLA-05"],
}

CUSTOMERS = [
    ("CLI-001", "Cimenterie Atlas", "industriel", "CAS", 3_450, "MT", 2019, 86),
    ("CLI-002", "AgroPlast Industries", "industriel", "CAS", 1_280, "MT", 2021, 79),
    ("CLI-003", "Textile Nord", "industriel", "TTA", 890, "MT", 2018, 74),
    ("CLI-004", "Maroc Phosphore Jorf", "industriel", "CAS", 5_600, "HT", 2015, 91),
    ("CLI-005", "Minoterie Souss", "industriel", "SOM", 410, "MT", 2020, 82),
    ("CLI-006", "Résidence Al Manar", "residentiel", "MRS", 46, "BT", 2022, 88),
    ("CLI-007", "Villa Anfa", "residentiel", "CAS", 18, "BT", 2023, 93),
    ("CLI-008", "Immeuble Agdal", "residentiel", "RSK", 62, "BT", 2017, 76),
    ("CLI-009", "Clinique Fès Nord", "commercial", "FES", 280, "MT", 2021, 85),
    ("CLI-010", "Hôtel Ménara", "commercial", "MRS", 340, "MT", 2016, 80),
    ("CLI-011", "Supermarché Tanger", "commercial", "TTA", 190, "MT", 2022, 87),
    ("CLI-012", "Zone franche Kénitra", "commercial", "RSK", 520, "MT", 2019, 83),
    ("CLI-013", "Ferme Agrumes Berkane", "agricole", "ORI", 95, "BT", 2020, 78),
    ("CLI-014", "Coopérative Souss", "agricole", "SOM", 130, "BT", 2021, 81),
    ("CLI-015", "Domaine Olivier Marrakech", "agricole", "MRS", 72, "BT", 2018, 75),
    ("CLI-016", "Université Al Quaraouiyine", "administration", "FES", 610, "MT", 2014, 89),
    ("CLI-017", "Commune Urbaine Oujda", "administration", "ORI", 480, "MT", 2015, 77),
    ("CLI-018", "Hôpital Régional Béni Mellal", "administration", "BMK", 390, "MT", 2017, 84),
    ("CLI-019", "Station de dessalement Agadir", "industriel", "SOM", 2_100, "HT", 2023, 90),
    ("CLI-020", "Data Center Casanearshore", "industriel", "CAS", 760, "MT", 2022, 94),
    ("CLI-021", "Marché de gros Marrakech", "commercial", "MRS", 150, "MT", 2020, 72),
    ("CLI-022", "Résidence Tanger Med", "residentiel", "TTA", 38, "BT", 2024, 86),
    ("CLI-023", "École nationale Meknès", "administration", "FES", 55, "BT", 2019, 80),
    ("CLI-024", "Serres Biougra", "agricole", "SOM", 110, "BT", 2022, 83),
]


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_regions() -> None:
    regions = []
    for name, code, population, clients, consumption, peak, renewable, losses, saidi, saifi in REGIONS:
        regions.append(
            {
                "code": code,
                "name": name,
                "population_m": population,
                "clients": clients,
                "consumption_gwh": consumption,
                "peak_mw": peak,
                "renewable_share_pct": renewable,
                "losses_pct": losses,
                "saidi_min": saidi,
                "saifi": saifi,
                "dependency_index": round(min(99, 100 - renewable * 0.9), 1),
            }
        )
    write_json(DATA / "regions.json", {"generated_at": "2026-11-12", "regions": regions})


def build_production_mix() -> None:
    write_json(
        DATA / "production_mix.json",
        {
            "year": 2026,
            "total_gwh": 42_300,
            "renewable_share_pct": 37.9,
            "co2_g_per_kwh": 412,
            "sources": PRODUCTION_MIX,
        },
    )


def load_shape(hour: int, month: int) -> float:
    """Profil de charge national normalisé (0-1), hiver plus marqué."""
    morning = 0.30 * math.exp(-((hour - 8.0) ** 2) / 6.0)
    evening = 0.62 * math.exp(-((hour - 19.2) ** 2) / 9.0)
    night = 0.12 * math.exp(-((hour - 3.0) ** 2) / 12.0)
    day = 0.18 if 9 <= hour <= 17 else 0.0
    season = 1.0 + (0.10 if month in (11, 12, 1, 2) else 0.0) - (0.06 if month in (6, 7, 8) else 0.0)
    return (0.46 + morning + evening + night + day) * season


def build_load_curve() -> None:
    start = date(2026, 10, 14)
    national_peak = sum(r[5] for r in REGIONS)  # 12 830 MW
    rows = []
    for day_index in range(30):
        day = start + timedelta(days=day_index)
        weekday = day.weekday()
        weekend_factor = 0.94 if weekday >= 5 else 1.0
        temperature = 19.0 - 4.0 * math.cos((day_index / 30) * 2 * math.pi) + random.uniform(-1.5, 1.5)
        for hour in range(24):
            shape = load_shape(hour, day.month) * weekend_factor
            national = national_peak * shape / 1.52
            if 18 <= hour <= 21:
                national *= 1.02
            national *= 1 + random.uniform(-0.012, 0.012)
            for name, code, population, clients, consumption, peak, *_ in REGIONS:
                weight = peak / national_peak
                region_load = national * weight * (1 + random.uniform(-0.018, 0.018))
                rows.append(
                    {
                        "timestamp": f"{day.isoformat()} {hour:02d}:00",
                        "date": day.isoformat(),
                        "hour": hour,
                        "region_code": code,
                        "region": name,
                        "load_mw": round(region_load, 1),
                        "temperature_c": round(temperature + (1.8 if 12 <= hour <= 16 else 0), 1),
                        "is_peak": int(18 <= hour <= 21),
                    }
                )
    with (DATA / "load_curve.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_monthly_consumption() -> None:
    rows = []
    months = ["2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05",
              "2026-06", "2026-07", "2026-08", "2026-09", "2026-10", "2026-11"]
    season = [1.14, 1.17, 1.10, 1.02, 0.94, 0.96, 1.06, 1.12, 1.10, 1.00, 0.93, 0.96]
    for name, code, population, clients, consumption, peak, *_ in REGIONS:
        base = consumption / 12
        for index, month in enumerate(months):
            value = base * season[index] * (1 + random.uniform(-0.025, 0.025))
            rows.append(
                {
                    "month": month,
                    "region_code": code,
                    "region": name,
                    "consumption_gwh": round(value, 1),
                    "clients": clients,
                    "peak_mw": round(peak * season[index] * (1 + random.uniform(-0.02, 0.02)), 1),
                }
            )
    with (DATA / "monthly_consumption.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_outages() -> None:
    rows = []
    start = datetime(2026, 8, 15, 6, 0)
    crews = ["Équipe Nord", "Équipe Centre", "Équipe Sud", "Équipe Est", "Astreinte 24/7"]
    for index in range(68):
        region = random.choice(REGIONS)
        code, name = region[1], region[0]
        cause, _, base_duration = random.choices(OUTAGE_CAUSES, weights=[c[1] for c in OUTAGE_CAUSES])[0]
        moment = start + timedelta(days=random.randint(0, 88), hours=random.randint(0, 22), minutes=random.choice([0, 15, 30, 45]))
        duration = max(12, int(random.gauss(base_duration, base_duration * 0.35)))
        customers = int(random.lognormvariate(6.2, 1.0))
        status = random.choices(["Résolu", "En cours", "Planifié"], weights=[0.82, 0.10, 0.08])[0]
        if status == "Planifié":
            cause = "Travaux programmés"
        priority = "P1" if customers > 8_000 or duration > 240 else "P2" if customers > 1_500 else "P3"
        rows.append(
            {
                "incident_id": f"INC-2026-{index + 101:04d}",
                "started_at": moment.strftime("%Y-%m-%d %H:%M"),
                "region_code": code,
                "region": name,
                "feeder": random.choice(FEEDERS[code]),
                "cause": cause,
                "duration_min": duration,
                "customers_affected": customers,
                "status": status,
                "priority": priority,
                "crew": random.choice(crews),
                "mttr_min": duration if status == "Résolu" else None,
                "energy_not_served_mwh": round(customers * duration * 0.0021, 1),
            }
        )
    rows.sort(key=lambda row: row["started_at"], reverse=True)
    curated = [
        {
            "incident_id": "INC-2026-0201",
            "started_at": "2026-11-11 19:20",
            "region_code": "CAS",
            "region": "Casablanca-Settat",
            "feeder": "MAARIF-01",
            "cause": "Surcharge réseau",
            "duration_min": 96,
            "customers_affected": 2340,
            "status": "Résolu",
            "priority": "P2",
            "crew": "Équipe Centre",
            "mttr_min": 96,
            "energy_not_served_mwh": 471.7,
        },
        {
            "incident_id": "INC-2026-0202",
            "started_at": "2026-11-12 08:10",
            "region_code": "CAS",
            "region": "Casablanca-Settat",
            "feeder": "SIDI-BELYOUT-03",
            "cause": "Équipement défaillant",
            "duration_min": 45,
            "customers_affected": 820,
            "status": "En cours",
            "priority": "P3",
            "crew": "Équipe Centre",
            "mttr_min": None,
            "energy_not_served_mwh": 77.5,
        },
        {
            "incident_id": "INC-2026-0203",
            "started_at": "2026-11-12 10:30",
            "region_code": "RSK",
            "region": "Rabat-Salé-Kénitra",
            "feeder": "AGDAL-02",
            "cause": "Travaux programmés",
            "duration_min": 180,
            "customers_affected": 1500,
            "status": "Planifié",
            "priority": "P3",
            "crew": "Équipe Nord",
            "mttr_min": None,
            "energy_not_served_mwh": 567.0,
        },
        {
            "incident_id": "INC-2026-0204",
            "started_at": "2026-11-11 18:45",
            "region_code": "TTA",
            "region": "Tanger-Tétouan-Al Hoceïma",
            "feeder": "TANGER-MED-01",
            "cause": "Météo extrême",
            "duration_min": 210,
            "customers_affected": 5200,
            "status": "En cours",
            "priority": "P2",
            "crew": "Équipe Nord",
            "mttr_min": None,
            "energy_not_served_mwh": 2293.2,
        },
    ]
    rows = curated + rows
    rows.sort(key=lambda row: row["started_at"], reverse=True)
    with (DATA / "outages.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_customers() -> None:
    rows = []
    for cid, name, segment, region, consumption_mwh, voltage, contract_year, satisfaction in CUSTOMERS:
        tariff = TARIFFS[segment]
        annual = consumption_mwh * 12
        energy = 0.0
        remaining = consumption_mwh
        for tier in tariff["tiers"]:
            if remaining <= 0:
                break
            capacity = math.inf if tier["max_kwh"] is None else tier["max_kwh"] - tier["min_kwh"]
            used = min(remaining, capacity)
            energy += used * tier["price_kwh"]
            remaining -= used
        bill = energy + tariff["fixed_fee"]
        bill *= 1 + tariff["vat_pct"] / 100 + tariff["municipal_tax_pct"] / 100
        rows.append(
            {
                "customer_id": cid,
                "name": name,
                "segment": segment,
                "segment_label": tariff["label"],
                "region_code": region,
                "region": next(r[0] for r in REGIONS if r[1] == region),
                "consumption_mwh_month": consumption_mwh,
                "annual_mwh": annual,
                "voltage": voltage,
                "contract_year": contract_year,
                "satisfaction": satisfaction,
                "bill_mad_month": round(bill, 2),
                "load_factor": round(random.uniform(0.52, 0.86), 2),
                "flexibility_score": round(random.uniform(0.35, 0.92), 2),
            }
        )
    write_json(DATA / "customers.json", {"customers": rows})
    write_json(DATA / "tariffs.json", TARIFFS)


DOCUMENTS = [
    {
        "doc_id": "DOC-DELESTAGE",
        "title": "Procédure de délestage et de gestion des pointes",
        "category": "Exploitation",
        "version": "3.2",
        "date": "2026-03-18",
        "owner": "Direction Exploitation Réseau",
        "summary": "Seuils de déclenchement, ordre de priorité des départs et communication aux clients lors d'une pointe de charge.",
        "keywords": ["délestage", "pointe", "charge", "priorité", "départ", "margin", "réserve"],
        "chunks": [
            "Le délestage est déclenché lorsque la marge de réserve nationale descend sous 4 % de la pointe prévisionnelle pendant plus de quinze minutes, ou lorsqu'un incident affecte deux postes sources simultanément.",
            "L'ordre de priorité des départs est le suivant : éclairage public et trafic, hôpitaux et cliniques, stations de pompage d'eau potable, installations industrielles critiques, puis zones résidentielles. Chaque départ possède un code de priorité P1, P2 ou P3.",
            "Avant tout délestage, le dispatcher vérifie la prévision J+1, la disponibilité des groupes, les importations et les consignes de sécurité. La décision est tracée dans le registre des manœuvres avec un horodatage à la seconde.",
            "La communication client est déclenchée dans les dix minutes : SMS aux abonnés concernés, message sur le portail et information de la presse régionale. Un délestage ne doit pas dépasser 90 minutes consécutives pour un même départ résidentiel.",
            "Le retour à la normale se fait progressivement, par blocs de 15 MW, afin d'éviter un appel de charge brutal et un risque de surtension en bout de réseau.",
        ],
    },
    {
        "doc_id": "DOC-MAINT-TR",
        "title": "Guide de maintenance préventive des transformateurs MT/BT",
        "category": "Maintenance",
        "version": "5.0",
        "date": "2026-01-22",
        "owner": "Direction Technique",
        "summary": "Périodicités, contrôles d'huile, thermographie infrarouge et critères de remplacement des transformateurs de distribution.",
        "keywords": ["transformateur", "maintenance", "huile", "thermographie", "charge", "température", "MT", "BT"],
        "chunks": [
            "Un transformateur de distribution fait l'objet d'une visite visuelle semestrielle, d'une thermographie annuelle et d'une analyse d'huile tous les deux ans. Les transformateurs de plus de 20 ans sont inspectés chaque trimestre.",
            "La thermographie recherche les points chauds sur les connexions, les bornes et les traversées. Un écart de plus de 15 °C entre phases impose une intervention sous 72 heures ; un point chaud supérieur à 90 °C impose une consignation immédiate.",
            "Le taux d'humidité de l'huile doit rester inférieur à 20 ppm et la rigidité diélectrique supérieure à 30 kV. Un transformateur dont la charge dépasse 85 % de sa puissance nominale pendant plus de quatre heures par jour est candidat à un renforcement.",
            "La maintenance conditionnelle s'appuie sur les capteurs de température et les compteurs communicants. Les alertes sont priorisées selon la charge, le nombre de clients impactés et la criticité du départ.",
        ],
    },
    {
        "doc_id": "DOC-CODE-RESEAU",
        "title": "Code du réseau de distribution — qualité de l'onde",
        "category": "Référentiel",
        "version": "2.4",
        "date": "2025-11-05",
        "owner": "Direction Réglementation",
        "summary": "Tensions nominales, tolérances de fréquence et de tension, taux de distorsion harmonique et règles de raccordement.",
        "keywords": ["tension", "fréquence", "harmonique", "qualité", "onde", "raccordement", "BT", "MT", "tolérance"],
        "chunks": [
            "La tension nominale est de 220/380 V en basse tension et de 20 kV en moyenne tension. La tolérance réglementaire est de ± 7 % en BT et ± 5 % en MT, mesurée sur une moyenne de dix minutes.",
            "La fréquence doit rester dans une plage de ± 0,5 Hz autour de 50 Hz. Tout écart supérieur à 1 Hz pendant plus de trente secondes doit être déclaré à l'autorité de régulation.",
            "Le taux de distorsion harmonique total de tension ne doit pas dépasser 8 % en BT et 5 % en MT. Les installations photovoltaïques et les variateurs de vitesse doivent être équipés de filtres conformes.",
            "Tout nouveau raccordement de production décentralisée fait l'objet d'une étude d'impact. La puissance injectée ne peut dépasser 30 % de la puissance de court-circuit du point de raccordement sans dispositif de limitation.",
        ],
    },
    {
        "doc_id": "DOC-TARIFS",
        "title": "Structure tarifaire et facturation de l'électricité",
        "category": "Commercial",
        "version": "4.1",
        "date": "2026-06-30",
        "owner": "Direction Commerciale",
        "summary": "Tranches résidentielles, tarifs industriel et agricole, primes fixes, TVA et taxe municipale.",
        "keywords": ["tarif", "facture", "tranche", "kWh", "TVA", "taxe", "résidentiel", "industriel", "agricole"],
        "chunks": [
            "Le tarif résidentiel est progressif par tranches de consommation mensuelle : 0,901 MAD/kWh jusqu'à 100 kWh, 1,073 MAD/kWh de 101 à 200 kWh, 1,212 MAD/kWh de 201 à 300 kWh, 1,345 MAD/kWh de 301 à 500 kWh et 1,512 MAD/kWh au-delà.",
            "Le tarif industriel moyenne tension comporte une prime fixe mensuelle de 2 400 MAD et un prix de l'énergie de 1,180 MAD/kWh jusqu'à 200 MWh, puis 0,985 MAD/kWh au-delà. La TVA est de 20 %.",
            "Le tarif agricole est de 0,830 MAD/kWh avec une prime fixe de 40 MAD et une TVA de 7 %. Le tarif commercial est de 1,420 MAD/kWh avec une prime fixe de 145 MAD.",
            "La facture totale additionne l'énergie consommée, la prime fixe, la TVA et, pour le résidentiel, la taxe municipale de 7 %. Les contestations doivent être déposées dans les 60 jours suivant l'émission de la facture.",
        ],
    },
    {
        "doc_id": "DOC-RENOUVELABLES",
        "title": "Intégration des énergies renouvelables au réseau de distribution",
        "category": "Technique",
        "version": "2.1",
        "date": "2026-04-12",
        "owner": "Direction Stratégie & Innovation",
        "summary": "Raccordement du solaire et de l'éolien, limites d'injection, stockage et gestion de l'intermittence.",
        "keywords": ["solaire", "éolien", "renouvelable", "raccordement", "injection", "stockage", "intermittence", "courbe de charge"],
        "chunks": [
            "La production solaire photovoltaïque suit une courbe en cloche centrée sur 13 h ; l'éolien est plus variable et peut produire la nuit. La combinaison des deux réduit la pointe de midi mais pas nécessairement la pointe du soir.",
            "Le raccordement d'une installation de production décentralisée nécessite une étude de flux de puissance, une vérification du plan de protection et un compteur bidirectionnel. L'injection est limitée à 30 % de la puissance de court-circuit du départ.",
            "Le stockage par batteries est mobilisé en priorité pour lisser les rampes de 17 h à 21 h. Une capacité de 100 MW / 200 MWh permet de couvrir environ 35 minutes de la pointe nationale.",
            "Le taux de pénétration renouvelable est calculé comme la production renouvelable divisée par la consommation totale. Il ne doit pas être confondu avec la part de capacité installée.",
        ],
    },
    {
        "doc_id": "DOC-INCIDENTS",
        "title": "Gestion des incidents et indicateurs de continuité",
        "category": "Exploitation",
        "version": "3.0",
        "date": "2026-02-09",
        "owner": "Direction Exploitation Réseau",
        "summary": "Classification P1/P2/P3, calcul du SAIDI, du SAIFI et du MTTR, escalade et retour d'expérience.",
        "keywords": ["incident", "SAIDI", "SAIFI", "MTTR", "P1", "P2", "P3", "coupure", "continuité", "escalade"],
        "chunks": [
            "Un incident P1 affecte plus de 8 000 clients ou dure plus de quatre heures ; un incident P2 affecte entre 1 500 et 8 000 clients ; un incident P3 est local et affecte moins de 1 500 clients. La priorité détermine le délai de prise en charge et le niveau d'escalade.",
            "Le SAIDI est la durée moyenne de coupure par client sur une période, exprimée en minutes. Le SAIFI est le nombre moyen de coupures par client. Le MTTR est la durée moyenne de réparation des incidents résolus.",
            "Chaque incident fait l'objet d'une fiche de retour d'expérience dans les cinq jours ouvrés. Les causes récurrentes sont analysées mensuellement et alimentent le plan de maintenance préventive.",
            "La compensation client est automatique lorsque la coupure dépasse 4 heures pour un client industriel ou 6 heures pour un client résidentiel, sous réserve d'un dossier complet.",
        ],
    },
    {
        "doc_id": "DOC-AMI",
        "title": "Compteurs communicants et télérelève (AMI)",
        "category": "Digital",
        "version": "1.8",
        "date": "2026-05-20",
        "owner": "Direction Digital & SI",
        "summary": "Architecture AMI, collecte toutes les 15 minutes, supervision des pertes et cybersécurité des concentrateurs.",
        "keywords": ["compteur", "AMI", "télérelève", "données", "pertes", "concentrateur", "cybersécurité", "15 minutes"],
        "chunks": [
            "Le compteur communicant transmet la courbe de charge toutes les 15 minutes via un concentrateur de quartier. Les données sont agrégées au niveau du départ et du poste source.",
            "La télérelève permet de détecter les pertes non techniques : branchements illicites, compteurs trafiqués, erreurs de relevé. Un écart supérieur à 3 % entre l'énergie injectée et l'énergie facturée déclenche une analyse.",
            "Les concentrateurs sont segmentés sur un VLAN dédié et communiquent avec la plateforme de collecte via TLS mutuel. Les mots de passe par défaut sont interdits et les firmwares sont signés.",
            "La disponibilité de la chaîne de collecte doit être supérieure à 98 %. Une panne de concentrateur est traitée comme un incident P2 si elle concerne plus de 500 compteurs.",
        ],
    },
    {
        "doc_id": "DOC-SECURITE",
        "title": "Sécurité des chantiers et consignations électriques",
        "category": "Sécurité",
        "version": "6.3",
        "date": "2026-01-05",
        "owner": "Direction HSE",
        "summary": "Habilitations, EPI, procédure de consignation et règles d'intervention à proximité des ouvrages sous tension.",
        "keywords": ["sécurité", "consignation", "EPI", "habilitation", "chantier", "tension", "HSE"],
        "chunks": [
            "Toute intervention sur un ouvrage électrique exige une habilitation valide, une analyse de risques et un plan de prévention. Les travaux sous tension sont réservés aux équipes habilitées BT ou HT.",
            "La consignation suit quatre étapes : séparation, condamnation, vérification d'absence de tension et mise à la terre. Un cadenas personnel est apposé sur chaque organe de coupure.",
            "Les EPI obligatoires comprennent le casque, les chaussures de sécurité, les gants isolants adaptés au niveau de tension, l'écran facial et la tenue ignifugée.",
            "Un permis de travail est exigé pour toute intervention de plus de deux heures ou nécessitant l'ouverture d'une tranchée. Le chef de chantier réalise un briefing sécurité quotidien.",
        ],
    },
    {
        "doc_id": "DOC-CLIENT",
        "title": "Relation client, réclamations et compensation",
        "category": "Commercial",
        "version": "2.6",
        "date": "2026-07-14",
        "owner": "Direction Commerciale",
        "summary": "Canaux de contact, délais de réponse, procédure de réclamation et gestes commerciaux.",
        "keywords": ["client", "réclamation", "délai", "compensation", "facture", "coupure", "satisfaction"],
        "chunks": [
            "Le client peut déposer une réclamation par téléphone, portail web, agence ou application mobile. Un accusé de réception avec numéro de dossier est envoyé sous 24 heures.",
            "Le délai de réponse est de 5 jours ouvrés pour une réclamation simple et de 15 jours pour une réclamation complexe nécessitant une enquête terrain.",
            "Une coupure de plus de 6 heures non planifiée ouvre droit à une compensation automatique de 150 MAD pour un client résidentiel et de 1 500 MAD pour un client industriel, plafonnée à 5 % de la facture annuelle.",
            "La satisfaction client est mesurée trimestriellement par enquête téléphonique et par le taux de réclamation réouverte. Un dossier rouvert plus de deux fois est escaladé au responsable régional.",
        ],
    },
    {
        "doc_id": "DOC-CYBER",
        "title": "Cybersécurité des systèmes SCADA et OT",
        "category": "Cybersécurité",
        "version": "3.4",
        "date": "2026-08-02",
        "owner": "RSSI",
        "summary": "Segmentation IT/OT, authentification multifacteur, journalisation, gestion des correctifs et réponse à incident.",
        "keywords": ["cybersécurité", "SCADA", "OT", "MFA", "segmentation", "journal", "incident", "correctif"],
        "chunks": [
            "Le réseau OT est segmenté du réseau IT par un pare-feu industriel et une zone démilitarisée. Les flux autorisés sont documentés dans une matrice de flux revue chaque semestre.",
            "L'accès aux postes de conduite exige une authentification multifacteur et une bastion d'administration. Les comptes génériques sont interdits.",
            "Les journaux des automates, des concentrateurs et des serveurs SCADA sont centralisés pendant au moins douze mois. Toute modification de configuration est signée et horodatée.",
            "Un incident de cybersécurité doit être signalé au RSSI dans l'heure. Le plan de réponse prévoit l'isolement du segment, la conservation des preuves et une communication encadrée.",
        ],
    },
    {
        "doc_id": "DOC-PREVISION",
        "title": "Prévision de la charge à J+1 et gestion des pointes",
        "category": "Exploitation",
        "version": "2.9",
        "date": "2026-09-11",
        "owner": "Direction Prévision & Dispatching",
        "summary": "Modèle de prévision, variables météo, événements, seuils d'alerte et marge de réserve.",
        "keywords": ["prévision", "charge", "pointe", "météo", "J+1", "réserve", "alerte", "température"],
        "chunks": [
            "La prévision J+1 est produite chaque jour à 11 h à partir des historiques de charge, de la météo (température, humidité, vent) et du calendrier (jours fériés, événements, ramadan).",
            "Une température maximale supérieure à 34 °C augmente la pointe de 6 à 9 % selon la région. Une baisse de 5 °C en hiver augmente la pointe de 4 à 7 %.",
            "Le seuil d'alerte est atteint lorsque la pointe prévisionnelle dépasse 92 % de la capacité disponible. Le seuil critique est de 97 %. Entre 92 % et 97 %, le dispatcher active les réserves et prépare un plan de délestage.",
            "La marge de réserve minimale est de 8 % de la pointe prévisionnelle. Elle peut être abaissée à 4 % pendant une heure maximum, avec validation du directeur d'exploitation.",
        ],
    },
    {
        "doc_id": "DOC-QUALITE-ANRE",
        "title": "Qualité de service et obligations réglementaires",
        "category": "Réglementation",
        "version": "1.5",
        "date": "2026-10-01",
        "owner": "Direction Réglementation",
        "summary": "Indicateurs suivis par l'autorité de régulation, seuils, pénalités et publication des résultats.",
        "keywords": ["ANRE", "régulation", "qualité", "SAIDI", "SAIFI", "pénalité", "publication", "seuil"],
        "chunks": [
            "L'autorité de régulation suit le SAIDI, le SAIFI, le délai de raccordement, le taux de réclamation traitée dans les délais et la qualité de l'onde. Les résultats sont publiés chaque trimestre.",
            "Le seuil national de SAIDI est fixé à 300 minutes par client et par an. Un dépassement de plus de 10 % expose l'opérateur à une pénalité proportionnelle au nombre de clients affectés.",
            "Le délai moyen de raccordement d'un client basse tension doit rester inférieur à 15 jours ouvrés. Pour un client moyenne tension, le délai cible est de 60 jours.",
            "Les coupures planifiées doivent être notifiées au moins 5 jours à l'avance, sauf urgence technique. Leur durée est exclue du calcul du SAIDI sous conditions.",
        ],
    },
]


def build_corpus() -> None:
    documents = []
    for document in DOCUMENTS:
        chunks = []
        for index, text in enumerate(document["chunks"]):
            chunks.append(
                {
                    "chunk_id": f"{document['doc_id']}-C{index + 1:02d}",
                    "text": text,
                    "tokens": len(text.split()),
                }
            )
        payload = {**document, "chunks": chunks}
        documents.append(payload)
        markdown = [
            f"# {document['title']}",
            "",
            f"**Référence :** {document['doc_id']} · **Version :** {document['version']} · **Date :** {document['date']}",
            f"**Propriétaire :** {document['owner']} · **Catégorie :** {document['category']}",
            "",
            document["summary"],
            "",
        ]
        for index, text in enumerate(document["chunks"]):
            markdown.append(f"## Article {index + 1}")
            markdown.append("")
            markdown.append(text)
            markdown.append("")
        (CORPUS_DIR / f"{document['doc_id'].lower()}.md").write_text("\n".join(markdown), encoding="utf-8")
    write_json(DATA / "corpus.json", {"documents": documents, "count": len(documents)})


def build_site() -> None:
    write_json(
        DATA / "site.json",
        {
            "brand": "VOLTIS",
            "tagline": "Agentic AI for the Electricity Sector",
            "version": "1.0.0",
            "date": "12 novembre 2026",
            "dashboard_port": 8033,
            "mcp_port": 8100,
            "a2a_port": 8101,
            "agents_ports": {"grid-analyst": 8102, "outage-inspector": 8103, "billing-advisor": 8104, "forecast-agent": 8105},
            "regions": [r[0] for r in REGIONS],
            "menu": [
                "Vue d'ensemble",
                "Assistant agentique",
                "MCP Playground",
                "Orchestration A2A",
                "Statistiques",
                "Architecture",
                "Documentation",
            ],
        },
    )


def main() -> None:
    build_regions()
    build_production_mix()
    build_load_curve()
    build_monthly_consumption()
    build_outages()
    build_customers()
    build_corpus()
    build_site()
    print("Données générées :", DATA)
    print("- regions.json, production_mix.json, customers.json, tariffs.json")
    print("- load_curve.csv (5 760 lignes), monthly_consumption.csv, outages.csv")
    print("- corpus.json +", len(list(CORPUS_DIR.glob('*.md'))), "documents Markdown")


if __name__ == "__main__":
    main()
