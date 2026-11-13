# -*- coding: utf-8 -*-
"""Graphiques de synthèse pour la présentation et la documentation."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
DATA = ROOT / "data"

NAVY = "#0A1F3C"
AMBER = "#F5B301"
TEAL = "#16A6A1"
BLUE = "#3B82C4"
GREEN = "#2E8B72"
RED = "#D9534F"
MUTED = "#64748B"
BG = "#F4F7FB"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})


def benchmark_chart() -> None:
    data = json.loads((DATA / "benchmarks.json").read_text(encoding="utf-8"))
    tasks = data["tasks"]
    labels = [task["id"] for task in tasks]
    initial = [task["initial"]["overall"] for task in tasks]
    final = [task["final"]["overall"] for task in tasks]
    x = np.arange(len(labels))
    width = 0.34
    fig, ax = plt.subplots(figsize=(8.6, 4.2), dpi=200)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    bars1 = ax.bar(x - width / 2, initial, width, label="Initial", color="#E8B4AE", edgecolor="none")
    bars2 = ax.bar(x + width / 2, final, width, label="Après 2 itérations", color=GREEN, edgecolor="none")
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.12, f"{bar.get_height():.1f}".replace(".", ","),
                ha="center", va="bottom", fontsize=8, color="#8B3A34")
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.12, f"{bar.get_height():.1f}".replace(".", ","),
                ha="center", va="bottom", fontsize=8, color=GREEN, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Tâche {label}" for label in labels], fontsize=9)
    ax.set_ylim(0, 10.8)
    ax.set_ylabel("Score / 10", fontsize=9)
    ax.set_title("Benchmark Reflexion — 5 tâches métier", fontsize=12, color=NAVY, fontweight="bold", loc="left")
    ax.legend(frameon=False, loc="upper left", ncol=2, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#DCE7F2")
    ax.grid(axis="y", color="#EDF2F8", linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(ASSETS / "benchmark_chart.png", facecolor="white")
    plt.close(fig)


def criteria_chart() -> None:
    data = json.loads((DATA / "benchmarks.json").read_text(encoding="utf-8"))
    criteria = ["clarity", "accuracy", "concision", "coherence"]
    labels = ["Clarté", "Exactitude", "Concision", "Cohérence"]
    initial = [np.mean([task["initial"]["scores"][c] for task in data["tasks"]]) for c in criteria]
    final = [np.mean([task["final"]["scores"][c] for task in data["tasks"]]) for c in criteria]
    x = np.arange(len(criteria))
    width = 0.34
    fig, ax = plt.subplots(figsize=(7.4, 3.8), dpi=200)
    fig.patch.set_facecolor("white")
    ax.bar(x - width / 2, initial, width, label="Initial", color="#E8B4AE")
    ax.bar(x + width / 2, final, width, label="Final", color=TEAL)
    for index, (a, b) in enumerate(zip(initial, final)):
        ax.text(index - width / 2, a + 0.1, f"{a:.1f}".replace(".", ","), ha="center", fontsize=8, color="#8B3A34")
        ax.text(index + width / 2, b + 0.1, f"{b:.1f}".replace(".", ","), ha="center", fontsize=8, color="#0C7B67", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 10.8)
    ax.set_ylabel("Score / 10")
    ax.set_title("Gain par critère du Critic", fontsize=11, color=NAVY, fontweight="bold", loc="left")
    ax.legend(frameon=False, ncol=2, fontsize=8, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#EDF2F8", linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(ASSETS / "criteria_chart.png", facecolor="white")
    plt.close(fig)


def mix_chart() -> None:
    data = json.loads((DATA / "production_mix.json").read_text(encoding="utf-8"))
    labels = [item["source"] for item in data["sources"]]
    values = [item["share_pct"] for item in data["sources"]]
    colors = [item["color"] for item in data["sources"]]
    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=200)
    wedges, _ = ax.pie(values, colors=colors, startangle=90, counterclock=False,
                       wedgeprops=dict(width=0.34, edgecolor="white", linewidth=2))
    ax.text(0, 0.08, f"{data['renewable_share_pct']} %", ha="center", va="center", fontsize=22,
            color=NAVY, fontweight="bold")
    ax.text(0, -0.18, "renouvelable", ha="center", va="center", fontsize=9, color=MUTED)
    ax.legend(wedges, [f"{label} · {value} %" for label, value in zip(labels, values)],
              loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=8)
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(ASSETS / "mix_chart.png", facecolor="white", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    benchmark_chart()
    criteria_chart()
    mix_chart()
    print("Graphiques générés dans", ASSETS)
