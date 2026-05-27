# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    DOCKER_CONTAINER=1 \
    OTEL_PYTHON_LOG_CORRELATION=true \
    PYTHONUNBUFFERED=1

COPY pyproject.toml .
COPY gateway/ gateway/

# System deps for pdf2image
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils && rm -rf /var/lib/apt/lists/*

COPY patterns/swarmledger/requirements.txt requirements.txt
RUN uv pip install --no-cache -r requirements.txt && \
    uv pip install --no-cache aws-opentelemetry-distro==0.10.1

RUN uv pip install --no-cache -e . --no-deps && \
    uv pip install --no-cache requests>=2.31.0

RUN useradd -m -u 1000 bedrock_agentcore

EXPOSE 8080

COPY patterns/swarmledger/main.py .
COPY patterns/swarmledger/agent_factory.py .
COPY patterns/swarmledger/app_factory.py .
COPY patterns/swarmledger/bootstrap.py .
COPY patterns/swarmledger/data_sources.py .
COPY patterns/swarmledger/request_context.py .
COPY patterns/swarmledger/stream_events.py .
COPY patterns/swarmledger/prompts/ prompts/
COPY patterns/swarmledger/accounting/ accounting/
COPY patterns/swarmledger/tools/ tools/
COPY patterns/utils/ utils/
RUN mkdir -p docs
COPY docs/COA.sql docs/COA.sql

USER bedrock_agentcore

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/ping', timeout=2)" || exit 1

CMD ["opentelemetry-instrument", "python", "-m", "main"]
