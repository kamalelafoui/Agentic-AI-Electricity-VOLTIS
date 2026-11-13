# -*- coding: utf-8 -*-
"""Serveur MCP VOLTIS — expose les outils du réseau électrique.

Deux interfaces :
  * REST  : /api/health, /api/tools, /api/tool (utilisée par le dashboard)
  * MCP   : /mcp (JSON-RPC 2.0) + /sse (transport SSE simplifié)

Lancement : python main.py mcp   (ou uvicorn mcp_server.server:app --port 8100)
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared import electricity_core as core  # noqa: E402

PORT = 8100
LOG_DIR = ROOT / "a2a" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
CALL_LOG = ROOT / "data" / "mcp_calls.jsonl"

app = FastAPI(
    title="VOLTIS MCP Server",
    description="Serveur MCP exposant les données et procédures du réseau électrique VOLTIS.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CALLS: list[dict] = []


class ToolRequest(BaseModel):
    tool: str
    arguments: dict = {}


def _log(event: dict) -> None:
    event["timestamp"] = datetime.now().isoformat(timespec="seconds")
    CALLS.append(event)
    del CALLS[:-200]
    with CALL_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    with (LOG_DIR / "mcp.log").open("a", encoding="utf-8") as handle:
        handle.write(f"{event['timestamp']} {event.get('tool', event.get('method', '?'))} "
                     f"{event.get('latency_ms', '')}ms {event.get('status', '')}\n")


def _execute(tool: str, arguments: dict) -> tuple[dict, float, str]:
    started = time.perf_counter()
    try:
        result = core.call_tool(tool, arguments)
        status = "ok" if "error" not in result else "error"
    except Exception as error:  # pragma: no cover
        result = {"error": str(error)}
        status = "error"
    latency = round((time.perf_counter() - started) * 1000, 2)
    _log({"tool": tool, "arguments": arguments, "status": status, "latency_ms": latency})
    return result, latency, status


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "volt-is-grid-mcp",
        "version": "1.0.0",
        "protocol": "MCP 2025-06-18",
        "port": PORT,
        "tools": [tool["name"] for tool in core.list_tools()],
        "tool_count": len(core.list_tools()),
        "corpus_documents": len(core.corpus()),
        "uptime_s": round(time.time() - STARTED, 1),
        "calls": len(CALLS),
    }


@app.get("/api/tools")
def tools() -> dict:
    return {"tools": core.list_tools(), "count": len(core.list_tools()), "protocol": "MCP"}


@app.post("/api/tool")
def tool_call(request: ToolRequest) -> JSONResponse:
    result, latency, status = _execute(request.tool, request.arguments)
    return JSONResponse(
        {
            "tool": request.tool,
            "arguments": request.arguments,
            "status": status,
            "latency_ms": latency,
            "result": result,
            "server": "volt-is-grid-mcp",
        }
    )


@app.get("/api/calls")
def calls(limit: int = 20) -> dict:
    return {"calls": CALLS[-limit:][::-1], "count": len(CALLS)}


@app.post("/mcp")
async def mcp_endpoint(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(_rpc_error(None, -32700, "Parse error"), status_code=400)
    response = _handle_rpc(payload)
    if response is None:
        return JSONResponse({}, status_code=202)
    return JSONResponse(response)


def _rpc_error(request_id, code: int, message: str, data=None) -> dict:
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def _handle_rpc(payload: dict) -> dict | None:
    request_id = payload.get("id")
    method = payload.get("method", "")
    params = payload.get("params", {}) or {}
    if method.startswith("notifications/"):
        return None
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {"listChanged": False}, "resources": {"subscribe": False}, "prompts": {}},
                "serverInfo": {"name": "volt-is-grid-mcp", "version": "1.0.0"},
                "instructions": "Serveur MCP VOLTIS : KPI réseau, incidents, prévision, facturation et RAG documentaire.",
            },
        }
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": core.list_tools()}}
    if method == "tools/call":
        name = params.get("name", "")
        arguments = params.get("arguments", {}) or {}
        result, latency, status = _execute(name, arguments)
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
                "structuredContent": result,
                "isError": status != "ok",
                "metadata": {"latency_ms": latency, "server": "volt-is-grid-mcp"},
            },
        }
    if method == "resources/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": [
                    {"uri": "volt-is://corpus/index", "name": "Index documentaire", "mimeType": "application/json"},
                    {"uri": "volt-is://grid/kpis", "name": "KPI réseau", "mimeType": "application/json"},
                    {"uri": "volt-is://grid/regions", "name": "Régions", "mimeType": "application/json"},
                ]
            },
        }
    if method == "resources/read":
        uri = params.get("uri", "")
        resources = {
            "volt-is://corpus/index": {"documents": core.corpus()},
            "volt-is://grid/kpis": core.national_kpis(),
            "volt-is://grid/regions": {"regions": core.regions()},
        }
        if uri not in resources:
            return _rpc_error(request_id, -32002, "Resource not found", {"uri": uri})
        text = json.dumps(resources[uri], ensure_ascii=False)
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"contents": [{"uri": uri, "mimeType": "application/json", "text": text}]},
        }
    if method == "prompts/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "prompts": [
                    {"name": "diagnostic_incident", "description": "Analyser un incident et proposer un plan d'action.",
                     "arguments": [{"name": "incident_id", "required": True}, {"name": "region_code", "required": False}]},
                    {"name": "briefing_dispatching", "description": "Briefing de pointe avec risques et actions.",
                     "arguments": [{"name": "region_code", "required": False}, {"name": "temperature_delta", "required": False}]},
                ]
            },
        }
    return _rpc_error(request_id, -32601, f"Method not found: {method}")


@app.get("/sse")
async def sse(request: Request) -> StreamingResponse:
    session_id = uuid.uuid4().hex[:12]

    async def event_stream():
        yield f"event: endpoint\ndata: /messages?session_id={session_id}\n\n"
        for _ in range(600):
            if await request.is_disconnected():
                break
            yield f"event: ping\ndata: {{\"session_id\":\"{session_id}\",\"time\":\"{datetime.now().isoformat(timespec='seconds')}\"}}\n\n"
            await asyncio.sleep(15)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/messages")
async def sse_messages(request: Request) -> JSONResponse:
    payload = await request.json()
    response = _handle_rpc(payload)
    return JSONResponse(response or {}, status_code=202 if response is None else 200)


STARTED = time.time()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("mcp_server.server:app", host="0.0.0.0", port=PORT, reload=False)
