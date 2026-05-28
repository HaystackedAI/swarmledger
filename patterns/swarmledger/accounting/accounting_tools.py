# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Accounting intake tools for accrual-basis document processing."""

from __future__ import annotations

import json
import os
import re
import time
from decimal import Decimal
from pathlib import Path, PurePosixPath

import boto3
from botocore.config import Config
from strands import Agent, tool
from strands.models import BedrockModel
from utils.inference import get_bedrock_config, get_inference_configs

s3_client = boto3.client("s3")
presign_s3_client = boto3.client(
    "s3",
    region_name=os.environ.get(
        "AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    ),
    config=Config(s3={"addressing_style": "virtual"}),
)

INFERENCE_CONFIG, _ = get_inference_configs()
BEDROCK_CONFIG = get_bedrock_config()
MODEL_ID = os.environ.get(
    "ACCOUNTING_MODEL_ID",
    os.environ.get("MODEL_ID", "global.anthropic.claude-sonnet-4-6"),
)
STAGING_BUCKET = os.environ.get("STAGING_BUCKET_NAME")
ACCOUNTING_PREFIX = "accounting"
URL_EXPIRATION = 3600


def _log_accounting_event(event: str, **fields) -> None:
    print(
        "[Accounting Intake] "
        + json.dumps({"event": event, **fields}, default=str)
    )


def _default_coa_path() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "docs" / "COA.sql"
        if candidate.exists():
            return candidate
    return Path(__file__).resolve().parent / "docs" / "COA.sql"


COA_PATH = Path(os.environ.get("COA_PATH", _default_coa_path()))


def _require_bucket() -> str:
    if not STAGING_BUCKET:
        raise RuntimeError("STAGING_BUCKET_NAME environment variable is not set")
    return STAGING_BUCKET


def _safe_session(session_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", session_id)


def _parse_s3_uri(s3_uri: str) -> tuple[str, str]:
    path = s3_uri[5:]
    return path.split("/", 1)


def _read_s3_text(s3_uri: str) -> str:
    bucket, key = _parse_s3_uri(s3_uri)
    return s3_client.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")


def _put_json(session_id: str, filename: str, payload) -> str:
    bucket = _require_bucket()
    key = f"{ACCOUNTING_PREFIX}/{_safe_session(session_id)}/{filename}"
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(payload, indent=2, default=str).encode("utf-8"),
        ContentType="application/json",
    )
    return f"s3://{bucket}/{key}"


def _list_json(session_id: str, prefix_name: str) -> list:
    bucket = _require_bucket()
    prefix = f"{ACCOUNTING_PREFIX}/{_safe_session(session_id)}/{prefix_name}"
    items: list = []
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents") or []:
            body = s3_client.get_object(Bucket=bucket, Key=obj["Key"])["Body"].read()
            parsed = json.loads(body)
            if isinstance(parsed, list):
                items.extend(parsed)
            elif isinstance(parsed, dict):
                items.append(parsed)
    return items


def _load_coa_accounts() -> list[dict]:
    sql = COA_PATH.read_text(encoding="utf-8")
    accounts: list[dict] = []
    for row in re.findall(r"\((.*?)\)", sql, flags=re.DOTALL):
        values = re.findall(r"'([^']*)'", row)
        if len(values) < 7:
            continue
        has_parent = len(values) >= 8
        code = values[3] if has_parent else values[2]
        name = values[4] if has_parent else values[3]
        normal_balance = values[5] if has_parent else values[4]
        is_posting = re.search(
            rf"'{re.escape(normal_balance)}'\s*,\s*true\s*,",
            row,
            flags=re.IGNORECASE,
        )
        accounts.append(
            {
                "code": code,
                "name": name,
                "normal_balance": normal_balance,
                "is_posting": bool(is_posting),
            }
        )
    return accounts


def _posting_coa_text() -> str:
    accounts = [a for a in _load_coa_accounts() if a["is_posting"]]
    return "\n".join(
        f"- {a['code']} {a['name']} ({a['normal_balance']})" for a in accounts
    )


def _build_model() -> BedrockModel:
    return BedrockModel(
        model_id=MODEL_ID,
        temperature=0,
        max_tokens=INFERENCE_CONFIG["maxTokens"],
        streaming=False,
        boto_client_config=BEDROCK_CONFIG,
    )


def _extract_json(text: str, tag: str):
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, flags=re.DOTALL)
    payload = match.group(1).strip() if match else text.strip()
    payload = re.sub(r"^```(?:json)?\s*|\s*```$", "", payload).strip()
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        array_match = re.search(r"\[[\s\S]*\]", payload)
        object_match = re.search(r"\{[\s\S]*\}", payload)
        candidate = array_match or object_match
        if not candidate:
            return [] if tag != "financial_statements" else {}
        try:
            return json.loads(candidate.group(0))
        except json.JSONDecodeError:
            return [] if tag != "financial_statements" else {}


def _run_json_agent(system_prompt: str, user_prompt: str, tag: str, step: str):
    start = time.time()
    agent = Agent(model=_build_model(), system_prompt=system_prompt, tools=[])
    _log_accounting_event(
        "llm_start",
        step=step,
        model_id=MODEL_ID,
        max_tokens=INFERENCE_CONFIG["maxTokens"],
        system_chars=len(system_prompt),
        user_chars=len(user_prompt),
    )
    try:
        result = agent(user_prompt)
        text = str(result)
        usage = getattr(result.metrics, "accumulated_usage", {}) if result.metrics else {}
        metrics = (
            getattr(result.metrics, "accumulated_metrics", {})
            if result.metrics
            else {}
        )
        _log_accounting_event(
            "llm_end",
            step=step,
            model_id=MODEL_ID,
            stop_reason=getattr(result, "stop_reason", None),
            context_size=getattr(result, "context_size", None),
            projected_context_size=getattr(result, "projected_context_size", None),
            usage=usage,
            metrics=metrics,
            output_chars=len(text),
            elapsed_seconds=round(time.time() - start, 3),
        )
        parsed = _extract_json(text, tag)
        parsed_count = len(parsed) if isinstance(parsed, list) else None
        _log_accounting_event(
            "json_parse",
            step=step,
            model_id=MODEL_ID,
            stop_reason=getattr(result, "stop_reason", None),
            parsed_type=type(parsed).__name__,
            parsed_count=parsed_count,
        )
        return parsed
    except Exception as exc:
        _log_accounting_event(
            "llm_error",
            step=step,
            model_id=MODEL_ID,
            max_tokens=INFERENCE_CONFIG["maxTokens"],
            system_chars=len(system_prompt),
            user_chars=len(user_prompt),
            elapsed_seconds=round(time.time() - start, 3),
            error_type=type(exc).__name__,
            error=str(exc),
        )
        raise


def _log_collection_step(step: str, **fields) -> None:
    _log_accounting_event(
        "step",
        step=step,
        model_id=MODEL_ID,
        max_tokens=INFERENCE_CONFIG["maxTokens"],
        **fields,
    )


def _amount(value) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except Exception:
        return Decimal("0")


@tool
def create_transactions(batch_md_s3_uri: str, session_id: str) -> str:
    """Extract accrual-basis transactions from one OCR batch and save them to S3."""
    markdown = _read_s3_text(batch_md_s3_uri)
    stem = PurePosixPath(_parse_s3_uri(batch_md_s3_uri)[1]).stem
    _log_collection_step(
        "create_transactions",
        session_id=session_id,
        batch_md_s3_uri=batch_md_s3_uri,
        markdown_chars=len(markdown),
    )
    system_prompt = """
You extract accounting transactions from receipts, invoices, and bank statements.
Use accrual basis only. Create transactions for economic events supported by the
document text. Do not invent missing amounts or dates. If evidence is ambiguous,
set confidence below 0.70 and explain in notes.

Return only JSON inside <transactions> tags. Schema:
[
  {
    "transaction_id": "short stable id",
    "date": "YYYY-MM-DD or empty string",
    "document_type": "receipt|invoice|bank_statement|other",
    "counterparty": "vendor/customer/bank",
    "description": "plain English description",
    "amount": number,
    "currency": "CAD unless shown otherwise",
    "tax_amount": number,
    "source_pages": [1],
    "evidence": "short quote or source detail",
    "confidence": number,
    "notes": "assumptions or empty string"
  }
]
""".strip()
    transactions = _run_json_agent(
        system_prompt=system_prompt,
        user_prompt=f"Extract transactions from this OCR batch:\n\n{markdown}",
        tag="transactions",
        step="create_transactions",
    )
    if not isinstance(transactions, list):
        transactions = []
    _log_collection_step(
        "create_transactions_complete",
        session_id=session_id,
        batch_md_s3_uri=batch_md_s3_uri,
        transaction_count=len(transactions),
    )
    return _put_json(session_id, f"transactions_{stem}.json", transactions)


@tool
def create_journal_entries(session_id: str) -> str:
    """Create balanced accrual journal entries from extracted transactions."""
    transactions = _list_json(session_id, "transactions_")
    _log_collection_step(
        "create_journal_entries",
        session_id=session_id,
        transaction_count=len(transactions),
    )
    system_prompt = f"""
You are an accrual accounting engine. Convert extracted transactions into balanced
journal entries using only posting accounts from this chart of accounts:

{_posting_coa_text()}

Rules:
- Every journal entry must balance: total debits equals total credits.
- Use accrual basis. Invoices create receivable/payable when cash settlement is
  not clearly shown.
- Put sales taxes into GST/HST Receivable or GST/HST Payable when tax is shown.
- Return only JSON inside <journal_entries> tags.

Schema:
[
  {{
    "entry_id": "JE-001",
    "date": "YYYY-MM-DD or empty string",
    "memo": "description",
    "source_transaction_id": "transaction id",
    "lines": [
      {{"account_code": "1111", "account_name": "Bank Account", "debit": 0, "credit": 0}}
    ]
  }}
]
""".strip()
    entries = _run_json_agent(
        system_prompt=system_prompt,
        user_prompt=json.dumps(transactions, indent=2),
        tag="journal_entries",
        step="create_journal_entries",
    )
    if not isinstance(entries, list):
        entries = []
    _log_collection_step(
        "create_journal_entries_complete",
        session_id=session_id,
        journal_entry_count=len(entries),
    )
    return _put_json(session_id, "journal_entries.json", entries)


@tool
def generate_trial_balance(session_id: str) -> str:
    """Generate a trial balance from saved journal entries."""
    entries = _list_json(session_id, "journal_entries")
    _log_collection_step(
        "generate_trial_balance",
        session_id=session_id,
        journal_entry_count=len(entries),
    )
    accounts = {a["code"]: a for a in _load_coa_accounts()}
    totals: dict[str, dict] = {}
    for entry in entries:
        for line in entry.get("lines", []):
            code = str(line.get("account_code", ""))
            if not code:
                continue
            account = accounts.get(code, {"name": line.get("account_name", code)})
            row = totals.setdefault(
                code,
                {
                    "account_code": code,
                    "account_name": account.get("name", line.get("account_name", "")),
                    "debit": Decimal("0"),
                    "credit": Decimal("0"),
                },
            )
            row["debit"] += _amount(line.get("debit"))
            row["credit"] += _amount(line.get("credit"))

    trial_balance = []
    for code in sorted(totals):
        row = totals[code]
        debit = row["debit"]
        credit = row["credit"]
        net = debit - credit
        trial_balance.append(
            {
                "account_code": code,
                "account_name": row["account_name"],
                "debit": float(debit),
                "credit": float(credit),
                "net_debit": float(net if net > 0 else Decimal("0")),
                "net_credit": float(-net if net < 0 else Decimal("0")),
            }
        )
    _log_collection_step(
        "generate_trial_balance_complete",
        session_id=session_id,
        trial_balance_rows=len(trial_balance),
    )
    return _put_json(session_id, "trial_balance.json", trial_balance)


@tool
def generate_financial_statements(session_id: str) -> str:
    """Generate basic financial statements from the trial balance."""
    trial_balance = _list_json(session_id, "trial_balance")
    _log_collection_step(
        "generate_financial_statements",
        session_id=session_id,
        trial_balance_rows=len(trial_balance),
    )
    by_prefix = {"1": 0.0, "2": 0.0, "3": 0.0, "4": 0.0, "5": 0.0}
    for row in trial_balance:
        code = str(row.get("account_code", ""))
        debit = float(row.get("debit", 0) or 0)
        credit = float(row.get("credit", 0) or 0)
        if code.startswith(("1", "5")):
            amount = debit - credit
        else:
            amount = credit - debit
        if code[:1] in by_prefix:
            by_prefix[code[:1]] += amount

    revenue = by_prefix["4"]
    expenses = by_prefix["5"]
    net_income = revenue - expenses
    statements = {
        "income_statement": {
            "revenue": revenue,
            "expenses": expenses,
            "net_income": net_income,
        },
        "balance_sheet": {
            "assets": by_prefix["1"],
            "liabilities": by_prefix["2"],
            "equity_before_current_income": by_prefix["3"],
            "current_net_income": net_income,
            "equity": by_prefix["3"] + net_income,
            "check": by_prefix["1"] - (by_prefix["2"] + by_prefix["3"] + net_income),
        },
        "basis": "Accrual",
    }
    _log_collection_step(
        "generate_financial_statements_complete",
        session_id=session_id,
        balance_sheet_check=statements["balance_sheet"]["check"],
    )
    return _put_json(session_id, "financial_statements.json", statements)


@tool
def publish_accounting_results(session_id: str) -> str:
    """Publish transactions, journal entries, TB, and statements to S3."""
    report = {
        "transactions": _list_json(session_id, "transactions_"),
        "journal_entries": _list_json(session_id, "journal_entries"),
        "trial_balance": _list_json(session_id, "trial_balance"),
        "financial_statements": (
            _list_json(session_id, "financial_statements") or [{}]
        )[0],
    }
    _log_collection_step(
        "publish_accounting_results",
        session_id=session_id,
        transaction_count=len(report["transactions"]),
        journal_entry_count=len(report["journal_entries"]),
        trial_balance_rows=len(report["trial_balance"]),
    )
    bucket = _require_bucket()
    key = f"{ACCOUNTING_PREFIX}/{_safe_session(session_id)}/accounting_results.json"
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(report, indent=2, default=str).encode("utf-8"),
        ContentType="application/json",
    )
    url = presign_s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=URL_EXPIRATION,
    )
    return json.dumps(
        {
            "s3_uri": f"s3://{bucket}/{key}",
            "transaction_count": len(report["transactions"]),
            "journal_entry_count": len(report["journal_entries"]),
            "review_url": url,
        }
    ) + f"\n\n[REVIEW_URL:{url}]"
