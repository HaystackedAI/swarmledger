# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
from typing import Any

import botocore

BEDROCK_READ_TIMEOUT = 600
BEDROCK_CONNECT_TIMEOUT = 600
BEDROCK_MAX_ATTEMPTS = 3
BEDROCK_MAX_CONNECTIONS = 10

DEFAULT_MAX_TOKENS = 64_000
NOVA_MICRO_MAX_TOKENS = 2_048
DEFAULT_THINKING_TOKENS = 2_000
TEMPERATURE = 0.0


def get_env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc
    if value < 1:
        raise ValueError(f"{name} must be greater than 0")
    return value


def _default_max_tokens() -> int:
    model_id = os.environ.get("MODEL_ID", "")
    if "nova-micro" in model_id:
        return NOVA_MICRO_MAX_TOKENS
    return DEFAULT_MAX_TOKENS


def get_step_max_tokens(default: int | None = None) -> int:
    """
    Return the per-step generation token budget.

    STEP_MAX_TOKENS is the global override. Without an override, Nova Micro uses
    a smaller default so each agent turn has room inside its 10k context window.
    """
    fallback = _default_max_tokens() if default is None else default
    if "nova-micro" in os.environ.get("MODEL_ID", ""):
        fallback = min(fallback, NOVA_MICRO_MAX_TOKENS)
    return get_env_int("STEP_MAX_TOKENS", fallback)


MAX_TOKENS = get_step_max_tokens()
THINKING_TOKENS = get_env_int("THINKING_TOKENS", DEFAULT_THINKING_TOKENS)

INFERENCE_CONFIG = {
    "stopSequences": [],  # words after which the generation is stopped
    "maxTokens": MAX_TOKENS,  # max tokens to be generated
    "temperature": TEMPERATURE,  # randomness of the model's output
}

REASONING_CONFIG = {
    "thinking": {
        "type": "enabled",  # whether extended thinking is enabled
        "budget_tokens": THINKING_TOKENS,  # max tokens for thinking budget
    }
}


def get_inference_configs() -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Get inference and reasoning parameters for Bedrock language models.

    Returns
    -------
    tuple[dict[str, Any], dict[str, Any]]
        Tuple containing:
        - Inference config dict with temperature, maxTokens,
          topP and stopSequences parameters
        - Reasoning config dict with thinking settings
    """

    inference_config = INFERENCE_CONFIG.copy()
    reasoning_config = REASONING_CONFIG.copy()

    if reasoning_config["thinking"]["type"] == "enabled":
        inference_config["temperature"] = 1.0  # required in thinking mode
    else:
        reasoning_config = {
            "thinking": {
                "type": "disabled",
            }
        }

    return inference_config, reasoning_config


def get_bedrock_config() -> botocore.config.Config:
    """
    Get botocore configuration for Bedrock API calls.

    Returns
    -------
    botocore.config.Config
        Configuration object with read timeout and retry settings for Bedrock client
    """
    return botocore.config.Config(
        read_timeout=BEDROCK_READ_TIMEOUT,
        connect_timeout=BEDROCK_CONNECT_TIMEOUT,
        retries={
            "max_attempts": BEDROCK_MAX_ATTEMPTS,
            "mode": "adaptive",
        },
        max_pool_connections=BEDROCK_MAX_CONNECTIONS,
    )
