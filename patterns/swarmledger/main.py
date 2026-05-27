# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import json
import traceback

from bootstrap import bootstrap_runtime

bootstrap_runtime()

from agent_factory import create_sl_agent
from app_factory import create_app
from bedrock_agentcore.runtime import RequestContext
from data_sources import normalize_enabled_sources
from request_context import build_context_block
from stream_events import prepare_stream_event
from utils.auth import extract_user_id_from_context

app = create_app()


@app.entrypoint
async def agent_stream(payload, context: RequestContext):
    """
    Main entrypoint for the swarm ledger orchestrator.

    Payload fields:
    - prompt: User's review request (required)
    - runtimeSessionId: Session ID (required)
    - enabledSources: Subset of {pubmed, openfda, clinicaltrials, nova} (optional)
    - contentPdfUri: S3 URI of the swarm ledgerPDF to review
    - referenceUris: List of S3 URIs for reference materials (optional)
    """
    user_query = payload.get("prompt")
    session_id = payload.get("runtimeSessionId")
    enabled_sources = normalize_enabled_sources(payload.get("enabledSources"))
    content_pdf_uri = payload.get("contentPdfUri")
    content_pdf_name = payload.get("contentPdfName") or ""
    reference_uris = payload.get("referenceUris") or []
    reference_names = payload.get("referenceNames") or []

    if not all([user_query, session_id]):
        yield {
            "status": "error",
            "error": "Missing required fields: prompt or runtimeSessionId",
        }
        return

    print(
        "[SL Review] AgentCore request received "
        + json.dumps(
            {
                "session_id": session_id,
                "enabled_sources": enabled_sources,
                "content_pdf_uri": content_pdf_uri,
                "content_pdf_name": content_pdf_name,
                "reference_count": len(reference_uris),
                "reference_names": reference_names,
            },
            default=str,
        )
    )

    full_prompt = (
        user_query
        + "\n\n"
        + build_context_block(
            session_id=session_id,
            content_pdf_uri=content_pdf_uri,
            content_pdf_name=content_pdf_name,
            reference_uris=reference_uris,
            reference_names=reference_names,
            enabled_sources=enabled_sources,
        )
    )

    try:
        user_id = extract_user_id_from_context(context)
        agent = create_sl_agent(
            user_id,
            session_id,
            external_sources_enabled=bool(enabled_sources),
        )

        stream = agent.stream_async(full_prompt, session_id=session_id)
        async for event in stream:
            d = prepare_stream_event(event)
            if not d:
                continue
            if "current_tool_use" in d:
                ctu = d["current_tool_use"]
                print(
                    "[SL Review] Tool event "
                    + json.dumps(
                        {
                            "session_id": session_id,
                            "toolUseId": ctu.get("toolUseId"),
                            "name": ctu.get("name"),
                        },
                        default=str,
                    )
                )

            yield json.loads(json.dumps(d, default=str))

    except Exception as e:
        print(f"[STREAM ERROR] Error in agent_stream: {e}")
        traceback.print_exc()
        yield {"status": "error", "error": str(e)}


if __name__ == "__main__":
    app.run()
