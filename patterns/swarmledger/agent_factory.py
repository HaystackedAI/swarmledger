# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import os
from pathlib import Path

from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager,
)
from accounting import (
    create_journal_entries,
    create_transactions,
    generate_financial_statements,
    generate_trial_balance,
    publish_accounting_results,
)
from strands import Agent
from strands.models import BedrockModel
from tools import batch_content, process_pdf
from utils.inference import get_bedrock_config, get_inference_configs

SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "orchestrator.txt"

INFERENCE_CONFIG, _ = get_inference_configs()
BEDROCK_CONFIG = get_bedrock_config()


def load_system_prompt() -> str:
    with open(SYSTEM_PROMPT_PATH, encoding="utf-8") as f:
        return f.read()


def create_sl_agent(user_id: str, session_id: str, external_sources_enabled: bool) -> Agent:
    model_id = os.environ.get("MODEL_ID", "amazon.nova-lite-v1:0")
    bedrock_model = BedrockModel(
        model_id=model_id,
        temperature=INFERENCE_CONFIG["temperature"],
        max_tokens=INFERENCE_CONFIG["maxTokens"],
        streaming=True,
        boto_client_config=BEDROCK_CONFIG,
    )

    memory_id = os.environ.get(
        "MEMORY_ID", "medicalcontentreviewcontentreviewbackend00452B8C-Vu19UiCsku"
    )
    if not memory_id:
        raise ValueError("MEMORY_ID environment variable is required")

    agentcore_memory_config = AgentCoreMemoryConfig(
        memory_id=memory_id, session_id=session_id, actor_id=user_id
    )
    session_manager = AgentCoreMemorySessionManager(
        agentcore_memory_config=agentcore_memory_config,
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    )

    tools = [
        process_pdf,
        batch_content,
        create_transactions,
        create_journal_entries,
        generate_trial_balance,
        generate_financial_statements,
        publish_accounting_results,
    ]

    return Agent(
        name="AccountingIntakeOrchestrator",
        system_prompt=load_system_prompt(),
        tools=tools,
        model=bedrock_model,
        session_manager=session_manager,
        trace_attributes={"user.id": user_id, "session.id": session_id},
    )
