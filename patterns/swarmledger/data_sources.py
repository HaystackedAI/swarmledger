# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import json
import os

# External data sources reachable via the AgentCore Gateway. The orchestrator
# itself does NOT call these; only the external-review sub-agent does.
ALL_DATA_SOURCES = {
    "pubmed": "PubMed Search",
    "openfda": "OpenFDA Drug Search",
    "clinicaltrials": "ClinicalTrials.gov Search",
    "nova": "Nova Web Grounding",
}


def load_tools_config() -> dict:
    raw = os.environ.get("TOOLS_CONFIG", "{}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


TOOLS_CONFIG = load_tools_config()

DEFAULT_ENABLED_SOURCES = [
    key
    for key in ALL_DATA_SOURCES
    if TOOLS_CONFIG.get(key, {}).get("enabled", True)
    and TOOLS_CONFIG.get(key, {}).get("default_on", True)
]


def normalize_enabled_sources(enabled_sources: list[str] | None) -> list[str]:
    sources = enabled_sources or DEFAULT_ENABLED_SOURCES
    return [source for source in sources if source in ALL_DATA_SOURCES]
