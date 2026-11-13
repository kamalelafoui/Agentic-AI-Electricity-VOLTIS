# -*- coding: utf-8 -*-
"""Tests unitaires et d'intégration VOLTIS."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from a2a.agents import handle_agent  # noqa: E402
from a2a.server import _select_agents  # noqa: E402
from langgraph_workflow import run_workflow  # noqa: E402
from mcp_server.server import _handle_rpc  # noqa: E402
from shared import electricity_core as core  # noqa: E402


class TestData(unittest.TestCase):
    def test_kpis(self):
        kpis = core.national_kpis()
        self.assertEqual(kpis["regions"], 8)
        self.assertEqual(kpis["consumption_gwh"], 42300)
        self.assertEqual(kpis["outages_90d"], 72)
        self.assertGreater(kpis["clients"], 9_000_000)
        self.assertGreater(kpis["renewable_share_pct"], 30)

    def test_tools(self):
        self.assertEqual(len(core.list_tools()), 10)
        result = core.call_tool("get_grid_kpis", {})
        self.assertIn("consumption_gwh", result)

    def test_search(self):
        result = core.search_documents("procédure de délestage en cas de pointe", 3)
        self.assertEqual(result["count"], 3)
        self.assertTrue(result["results"][0]["citation"])
        self.assertGreater(result["results"][0]["relevance_pct"], 50)

    def test_bill(self):
        bill = core.simulate_bill("industriel", 250)
        self.assertEqual(bill["segment"], "industriel")
        self.assertGreater(bill["total_mad"], 0)
        self.assertAlmostEqual(bill["total_mad"], bill["energy_mad"] + bill["fixed_fee_mad"] + bill["vat_mad"], places=1)

    def test_forecast(self):
        forecast = core.forecast_load("CAS", 24, 5)
        self.assertEqual(forecast["horizon_h"], 24)
        self.assertGreater(forecast["peak_mw"], 0)
        self.assertIn(forecast["risk"], {"Faible", "Modéré", "Élevé", "Critique"})
        self.assertEqual(len(forecast["series"]), 24)

    def test_energy_savings(self):
        result = core.recommend_energy_savings("CLI-001")
        self.assertEqual(result["customer_id"], "CLI-001")
        self.assertTrue(result["actions"])
        self.assertGreater(result["total_gain_pct"], 0)


class TestWorkflow(unittest.TestCase):
    def test_reflexion(self):
        result = run_workflow("Quel est le mix de production national ?", "NATIONAL", max_iterations=2, threshold=9.9)
        history = result["score_history"]
        self.assertGreaterEqual(len(history), 2)
        self.assertGreaterEqual(history[-1]["overall"], history[0]["overall"])
        self.assertIn("##", result["final_answer"])
        self.assertIn("Sources", result["final_answer"])
        self.assertTrue(result["sources"])

    def test_outage_sources(self):
        result = run_workflow("Analyse la coupure de Maârif hier soir.", "CAS")
        doc_ids = {source["doc_id"] for source in result["sources"]}
        self.assertIn("DOC-INCIDENTS", doc_ids)
        self.assertIn("DOC-DELESTAGE", doc_ids)


class TestA2A(unittest.TestCase):
    def test_agent(self):
        artifact = handle_agent("outage-inspector", "Coupure à Casablanca", {"region_code": "CAS"}, "TEST-01")
        self.assertEqual(artifact["status"], "ok")
        self.assertTrue(artifact["findings"])
        self.assertEqual(artifact["correlation_id"], "TEST-01")

    def test_selection(self):
        selected = _select_agents("Analyse la coupure de Maârif et le risque de pointe demain", 3)
        self.assertGreaterEqual(len(selected), 2)
        self.assertIn("outage-inspector", selected)

    def test_all_agents(self):
        for agent_id in core.AGENT_CAPABILITIES:
            artifact = handle_agent(agent_id, "Donne-moi les KPI du réseau.", {"region_code": "CAS"}, "TEST-02")
            self.assertEqual(artifact["status"], "ok")


class TestMCP(unittest.TestCase):
    def test_initialize(self):
        response = _handle_rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertEqual(response["result"]["serverInfo"]["name"], "volt-is-grid-mcp")

    def test_tools_list(self):
        response = _handle_rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        self.assertEqual(len(response["result"]["tools"]), 10)

    def test_tools_call(self):
        response = _handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "get_production_mix", "arguments": {}},
            }
        )
        self.assertFalse(response["result"]["isError"])
        self.assertIn("renewable_share_pct", response["result"]["structuredContent"])


class TestManifests(unittest.TestCase):
    def test_files(self):
        for name in [
            "mcp_manifest.json",
            "a2a_manifest.json",
            "rag_manifest.json",
            "langgraph_manifest.json",
            "architecture_manifest.json",
            "agentic_ai_electricity_full.json",
        ]:
            path = ROOT / "json" / name
            self.assertTrue(path.exists(), name)
            json.loads(path.read_text(encoding="utf-8"))

    def test_agent_cards(self):
        cards = list((ROOT / "json" / "agent_cards").glob("*.json"))
        self.assertEqual(len(cards), 5)
        for path in cards:
            card = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("name", card)
            self.assertIn("description", card)

    def test_langflow_json(self):
        path = ROOT / "Agentic_AI_Electricity_VOLTIS.json"
        self.assertTrue(path.exists())
        flow = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(flow["name"], "Agentic_AI_Electricity_VOLTIS")
        nodes = {node["data"]["id"]: node for node in flow["data"]["nodes"]}
        self.assertIn("Agent-VOLTIS", nodes)
        self.assertIn("MCPTools-VOLTIS", nodes)
        self.assertEqual(len(flow["data"]["edges"]), 3)
        server = nodes["MCPTools-VOLTIS"]["data"]["node"]["template"]["mcp_server"]["value"]
        self.assertEqual(server["name"], "volt-is-grid-mcp")
        self.assertIn("8100", server["config"]["url"])
        self.assertEqual(flow["volt_is"]["benchmark"]["final"], 9.40)


if __name__ == "__main__":
    unittest.main(verbosity=2)
