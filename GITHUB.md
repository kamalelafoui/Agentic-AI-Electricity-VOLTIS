# Publication GitHub — VOLTIS

**Dépôt :** https://github.com/kamalelafoui/Agentic-AI-Electricity-VOLTIS

Dépôt **public** contenant le mini-projet final *Agentic AI for the Electricity Sector* :
dashboard Streamlit 8033, serveur MCP, orchestrateur A2A, RAG agentique, LangGraph,
documentation DOCX/PDF, présentation PPTX/PDF et vidéo de démonstration.

---

## 1. Contenu publié

- `dashboard/`, `mcp_server/`, `a2a/`, `langgraph_workflow/`, `shared/`
- `data/`, `json/`, `docs/`, `presentation/`, `assets/`, `screenshots/`, `videos/`
- `Agentic_AI_Electricity_VOLTIS.json` (workflow Langflow final)
- `Dockerfile`, `docker-compose.yml`, `main.py`, `requirements.txt`
- `README.md`, `LIVRABLES.md`, `MANIFEST.txt`, `LICENSE`
- `tests/`, `scripts/`

## 2. Fichiers exclus

- `.env` (secret)
- `.venv/`, `__pycache__/`
- `a2a/logs/`, `data/mcp_calls.jsonl`, `data/a2a_delegations.jsonl`
- archives `*.zip`
- fichiers temporaires `_preview*`, `_export_*`, `_one_*`

## 3. Commandes de publication

```powershell
cd "C:\Users\HP\Documents\Projet par défaut\Agentic_AI_Electricity_FINAL"

git init
git branch -M main
git add .
git commit -m "VOLTIS — Agentic AI for the Electricity Sector, version finale"

git remote add origin https://github.com/kamalelafoui/Agentic-AI-Electricity-VOLTIS.git
git push -u origin main
```

## 4. Mise à jour ultérieure

```powershell
git add .
git commit -m "Mise à jour de la documentation et des livrables"
git push
```

## 5. Description du dépôt

> VOLTIS — plateforme agentique pour le secteur électrique : MCP (10 outils), A2A
> (4 agents + AgentCards), RAG hybride (12 documents / 49 chunks), LangGraph
> Reflexion (6,48 → 9,40), dashboard Streamlit 8033, Docker, documentation et vidéo.

## 6. Topics GitHub

`agentic-ai`, `electricity`, `energy`, `mcp`, `a2a`, `rag`, `langgraph`,
`streamlit`, `python`, `docker`, `multi-agent`, `smart-grid`

## 7. Remarques

- La vidéo `videos/VOLTIS_Demo.mp4` fait environ 3 Mo : aucun besoin de Git LFS.
- Le dossier `docs/` contient les versions DOCX et PDF.
- Le dossier `presentation/` contient les versions PPTX et PDF.
- Les données sont **100 % synthétiques** : aucun client réel.
