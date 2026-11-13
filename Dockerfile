# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN mkdir -p data a2a/logs a2a/agent_cards screenshots \
    && python -c "import streamlit, fastapi, langgraph, docx, pptx; print('VOLTIS image ready')"

EXPOSE 8033 8100 8101 8102 8103 8104 8105

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8033/_stcore/health || exit 1

CMD ["python", "main.py"]
