# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import json
import os

# Frontend display toggles for accounting context. They are intentionally not
# wired to backend Gateway tools in the accounting intake workflow.
ALL_DATA_SOURCES = {
    "pubmed": "Tax Registry",
    "openfda": "Business Registry",
    "clinicaltrials": "Bank Feed",
    "nova": "Member Directory",
    "coa": "Chart of Accounts",
    "tax": "Sales Tax Rules",
    "period": "Period Close Rules",
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
