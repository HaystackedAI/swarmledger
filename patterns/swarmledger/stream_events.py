# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import copy

FORWARDED_EVENT_KEYS = {
    "data",
    "delta",
    "current_tool_use",
    "message",
    "result",
    "init_event_loop",
    "start_event_loop",
    "start",
    "type",
}


def prepare_stream_event(event, max_tool_result_len: int = 3000) -> dict:
    # Deep-copy the subset we forward so truncation never mutates agent context.
    prepared = copy.deepcopy(
        {key: value for key, value in dict(event).items() if key in FORWARDED_EVENT_KEYS}
    )
    if not prepared:
        return {}

    if "current_tool_use" in prepared:
        ctu = prepared["current_tool_use"]
        prepared["current_tool_use"] = {
            "toolUseId": ctu.get("toolUseId"),
            "name": ctu.get("name"),
        }

    truncate_large_fields(prepared, max_len=max_tool_result_len)
    return prepared


def truncate_text(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len] + "... (truncated)"


def truncate_large_fields(d: dict, max_len: int = 3000) -> None:
    msg = d.get("message")
    if isinstance(msg, dict) and isinstance(msg.get("content"), list):
        for block in msg["content"]:
            if not isinstance(block, dict):
                continue
            tr = block.get("toolResult")
            if isinstance(tr, dict) and isinstance(tr.get("content"), list):
                for item in tr["content"]:
                    if isinstance(item, dict) and isinstance(item.get("text"), str):
                        item["text"] = truncate_text(item["text"], max_len)
