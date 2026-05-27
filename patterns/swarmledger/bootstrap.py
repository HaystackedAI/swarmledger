# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import os
import sys
from pathlib import Path

PATTERN_DIR = Path(__file__).resolve().parent
PATTERNS_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = Path(__file__).resolve().parents[2]


def setup_import_paths() -> None:
    for path in (PATTERN_DIR, PATTERNS_DIR):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))


def load_local_env_file() -> None:
    env_path = REPO_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip().strip("'\"")
        os.environ[key] = value


def bootstrap_runtime() -> None:
    os.environ["BYPASS_TOOL_CONSENT"] = "true"
    setup_import_paths()
    load_local_env_file()
