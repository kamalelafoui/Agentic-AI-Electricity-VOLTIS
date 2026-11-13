# -*- coding: utf-8 -*-
"""VOLTIS — Agentic AI for the Electricity Sector.

Point d'entrée unique :
    python main.py                 # dashboard + MCP + A2A
    python main.py dashboard       # dashboard Streamlit sur 8033
    python main.py mcp             # serveur MCP sur 8100
    python main.py a2a             # orchestrateur 8101 + agents 8102-8105
    python main.py demo            # benchmark Reflexion + démo A2A
    python main.py check           # validation des données et livrables
    python main.py build           # régénère données, schémas, JSON, DOCX, PPTX
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DASHBOARD_PORT = int(os.getenv("VOLTIS_DASHBOARD_PORT", "8033"))
MCP_PORT = int(os.getenv("VOLTIS_MCP_PORT", "8100"))
A2A_PORT = int(os.getenv("VOLTIS_A2A_PORT", "8101"))
AGENT_PORTS = [8102, 8103, 8104, 8105]

BANNER = r"""
 __   __ ___  _    _____ ___ ___
 \ \ / /| _ \| |  |_   _|_ _/ __|
  \ V / |   /| |__  | |  | |\__ \
   \_/  |_|_\|____| |_| |___|___/   ENERGY INTELLIGENCE
 Agentic AI for the Electricity Sector · v1.0
"""


def run_dashboard() -> None:
    command = [
        sys.executable, "-m", "streamlit", "run", str(ROOT / "dashboard" / "app.py"),
        "--server.port", str(DASHBOARD_PORT),
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
    ]
    print(f"  · Dashboard  http://localhost:{DASHBOARD_PORT}")
    subprocess.run(command, cwd=ROOT)


def run_mcp() -> None:
    import uvicorn

    print(f"  · MCP        http://127.0.0.1:{MCP_PORT}/mcp")
    uvicorn.run("mcp_server.server:app", host="0.0.0.0", port=MCP_PORT, log_level="info")


def run_a2a() -> None:
    from a2a.server import run_all

    print(f"  · A2A        http://127.0.0.1:{A2A_PORT}")
    run_all()


def _spawn(args: list[str]) -> subprocess.Popen:
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    return subprocess.Popen([sys.executable, str(ROOT / "main.py"), *args], cwd=ROOT, creationflags=creationflags)


def run_all() -> None:
    print(BANNER)
    print("Démarrage de l'écosystème VOLTIS…")
    processes: list[subprocess.Popen] = []
    try:
        mcp = _spawn(["mcp"])
        processes.append(mcp)
        a2a = _spawn(["a2a"])
        processes.append(a2a)
        print("  · Attente des services (3 s)…")
        time.sleep(3)
        run_dashboard()
    except KeyboardInterrupt:
        print("\nArrêt demandé…")
    finally:
        for process in processes:
            if process.poll() is None:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)], capture_output=True)
                else:
                    process.terminate()
        print("Services arrêtés.")


def run_demo() -> None:
    import statistics

    from a2a.agents import handle_agent
    from a2a.server import _aggregate, _select_agents
    from langgraph_workflow import run_workflow
    from shared import electricity_core as core

    print(BANNER)
    print("=== Démonstration 1/2 : boucle Reflexion sur 5 tâches ===\n")
    rows = []
    for task in core.benchmark_tasks():
        result = run_workflow(task["question"], task["region_code"], max_iterations=2, threshold=9.9)
        history = result["score_history"]
        initial, final = history[0], history[-1]
        rows.append((task["id"], initial["overall"], final["overall"], final["overall"] - initial["overall"], result["elapsed_ms"]))
        print(
            f"  {task['id']} · {task['question'][:72]:<72} "
            f"{initial['overall']:>4}/10 → {final['overall']:>4}/10 "
            f"(+{final['overall'] - initial['overall']:.1f}) en {result['elapsed_ms']:.0f} ms"
        )
    average_initial = statistics.mean(row[1] for row in rows)
    average_final = statistics.mean(row[2] for row in rows)
    average_gain = statistics.mean(row[3] for row in rows)
    print(f"\n  Moyenne : {average_initial:.2f}/10 → {average_final:.2f}/10 (gain +{average_gain:.2f})\n")

    print("=== Démonstration 2/2 : collaboration A2A ===\n")
    question = "Analyse la coupure de Maârif hier soir, évalue le risque de pointe demain et propose un plan d'action."
    selected = _select_agents(question, 3)
    artifacts = [handle_agent(agent_id, question, {"region_code": "CAS"}, "A2A-DEMO-0001") for agent_id in selected]
    print(f"  Question : {question}")
    print(f"  Agents   : {', '.join(selected)}")
    for artifact in artifacts:
        print(f"  - {artifact['agent_label']:<20} {artifact['latency_ms']:>6.1f} ms · {artifact['summary'][:96]}")
    print("\n  Agrégation :")
    for line in _aggregate(question, "A2A-DEMO-0001", artifacts).splitlines()[:12]:
        print("   ", line)
    report = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "reflexion": {
            "tasks": [
                {"id": row[0], "initial": row[1], "final": row[2], "gain": row[3], "latency_ms": row[4]}
                for row in rows
            ],
            "averages": {"initial": round(average_initial, 2), "final": round(average_final, 2), "gain": round(average_gain, 2)},
        },
        "a2a": {"question": question, "agents": selected, "artifacts": artifacts},
    }
    (ROOT / "data" / "demo_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nRapport enregistré dans data/demo_report.json")


def run_check() -> int:
    print(BANNER)
    checks: list[tuple[str, bool, str]] = []

    required = [
        "data/regions.json", "data/load_curve.csv", "data/outages.csv", "data/customers.json",
        "data/tariffs.json", "data/corpus.json", "data/benchmarks.json",
        "json/mcp_manifest.json", "json/a2a_manifest.json", "json/rag_manifest.json",
        "json/langgraph_manifest.json", "json/architecture_manifest.json",
        "a2a/agent_cards/orchestrator.json", "assets/logo.png", "assets/architecture_hub.png",
        "dashboard/app.py", "main.py", "Dockerfile", "docker-compose.yml",
        "docs/Documentation_Finale_VOLTIS.docx", "docs/Documentation_Finale_VOLTIS.pdf",
        "presentation/Presentation_Finale_VOLTIS.pptx", "presentation/Presentation_Finale_VOLTIS.pdf",
        "screenshots/home.png", "tests/test_volt_is.py",
    ]
    for relative in required:
        path = ROOT / relative
        checks.append((relative, path.exists(), f"{path.stat().st_size/1024:.0f} Ko" if path.exists() else "manquant"))

    try:
        from shared import electricity_core as core

        checks.append(("Données métier", len(core.regions()) == 8, f"{len(core.regions())} régions"))
        checks.append(("Outil MCP", len(core.list_tools()) == 10, f"{len(core.list_tools())} outils"))
        checks.append(("Corpus RAG", len(core.corpus()) == 12, f"{len(core.corpus())} documents"))
        search = core.search_documents("procédure de délestage", 3)
        checks.append(("Recherche hybride", search["count"] == 3, f"{search['results'][0]['title']}"))
        bill = core.simulate_bill("industriel", 250)
        checks.append(("Simulation facture", bill["total_mad"] > 0, f"{bill['total_mad']:.0f} MAD"))
    except Exception as error:
        checks.append(("Socle métier", False, str(error)[:80]))

    try:
        from langgraph_workflow import run_workflow

        result = run_workflow("Quel est le mix de production national ?", "NATIONAL", max_iterations=2, threshold=9.9)
        checks.append(("Workflow LangGraph", result["final_answer"].startswith("##"), f"{result['score_history'][-1]['overall']}/10"))
    except Exception as error:
        checks.append(("Workflow LangGraph", False, str(error)[:80]))

    try:
        from a2a.agents import handle_agent

        artifact = handle_agent("outage-inspector", "Coupure à Casablanca", {"region_code": "CAS"}, "CHECK-01")
        checks.append(("Agent A2A", artifact["status"] == "ok", artifact["summary"][:60]))
    except Exception as error:
        checks.append(("Agent A2A", False, str(error)[:80]))

    try:
        import docx  # noqa: F401
        import pptx  # noqa: F401

        checks.append(("Bibliothèques DOCX/PPTX", True, "python-docx / python-pptx"))
    except Exception as error:
        checks.append(("Bibliothèques DOCX/PPTX", False, str(error)[:80]))

    width = max(len(name) for name, _, _ in checks) + 2
    for name, ok, detail in checks:
        print(f"  {'✓' if ok else '✗'} {name:<{width}} {detail}")
    failed = [name for name, ok, _ in checks if not ok]
    print(f"\n{len(checks) - len(failed)}/{len(checks)} contrôles réussis.")
    if failed:
        print("Échecs :", ", ".join(failed))
        return 1
    return 0


def run_build() -> None:
    scripts = [
        "scripts/build_data.py",
        "scripts/build_logo.py",
        "scripts/build_diagrams.py",
        "scripts/build_diagrams_v2.py",
        "scripts/build_json.py",
        "scripts/build_charts.py",
        "scripts/build_docs.py",
        "scripts/build_deck.py",
        "scripts/make_zip.py",
    ]
    for script in scripts:
        path = ROOT / script
        if not path.exists():
            print(f"  · {script} — absent, ignoré")
            continue
        print(f"  · exécution de {script}")
        subprocess.run([sys.executable, str(path)], cwd=ROOT, check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="VOLTIS — Agentic AI for the Electricity Sector")
    parser.add_argument(
        "command",
        nargs="?",
        default="all",
        choices=["all", "dashboard", "mcp", "a2a", "demo", "check", "build"],
        help="Commande à exécuter (défaut : all)",
    )
    args = parser.parse_args()
    if args.command == "dashboard":
        run_dashboard()
        return 0
    if args.command == "mcp":
        run_mcp()
        return 0
    if args.command == "a2a":
        run_a2a()
        return 0
    if args.command == "demo":
        run_demo()
        return 0
    if args.command == "check":
        return run_check()
    if args.command == "build":
        run_build()
        return 0
    run_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
