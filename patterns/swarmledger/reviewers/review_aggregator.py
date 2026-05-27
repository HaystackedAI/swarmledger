# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Aggregates per-batch reviewer JSONs and publishes final review results."""

import json
import os
import re

import boto3
from botocore.config import Config
from strands import tool

from reviewers._common import REVIEWS_PREFIX, STAGING_BUCKET

s3_client = boto3.client("s3")
presign_s3_client = boto3.client(
    "s3",
    region_name=os.environ.get(
        "AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    ),
    config=Config(s3={"addressing_style": "virtual"}),
)

REVIEWER_KIND_RE = re.compile(r"/(?P<kind>generic|external|internal)_[^/]+\.json$")
URL_EXPIRATION = 3600


@tool
def get_reviews(session_id: str) -> str:
    """Aggregate all per-batch reviewer JSONs and return the findings directly.

    Reads every file under `s3://{STAGING_BUCKET}/reviews/{session_id}/`, tags each
    finding with the reviewer that produced it (`"generic" | "external" | "internal"`),
    sorts findings by page number, and returns the full aggregate JSON in memory.

    Parameters
    ----------
    session_id : str
        The same `session_id` that was passed to the reviewer tools.

    Returns
    -------
    str
        JSON string of shape:
        `{"findings": [...],
          "counts": {"generic": N, "external": N, "internal": N},
          "total": N}`
    """
    if not STAGING_BUCKET:
        raise RuntimeError("STAGING_BUCKET_NAME environment variable is not set")

    safe_session = re.sub(r"[^a-zA-Z0-9_-]", "_", session_id)
    prefix = f"{REVIEWS_PREFIX}/{safe_session}/"

    paginator = s3_client.get_paginator("list_objects_v2")
    findings: list[dict] = []
    counts = {"generic": 0, "external": 0, "internal": 0}
    for page in paginator.paginate(Bucket=STAGING_BUCKET, Prefix=prefix):
        for obj in page.get("Contents") or []:
            key = obj["Key"]
            match = REVIEWER_KIND_RE.search(key)
            if not match:
                continue
            kind = match.group("kind")
            body = s3_client.get_object(Bucket=STAGING_BUCKET, Key=key)["Body"].read()
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                continue
            if not isinstance(data, list):
                continue
            for item in data:
                if isinstance(item, dict):
                    item = {**item, "reviewer": kind}
                    findings.append(item)
                    counts[kind] += 1

    # Sort by page (missing/non-int page sinks to the end), preserving within-page
    # order for stability.
    def _sort_key(f: dict) -> tuple:
        page = f.get("page")
        return (0, page) if isinstance(page, int) else (1, 0)

    findings.sort(key=_sort_key)

    aggregate = {
        "findings": findings,
        "counts": counts,
        "total": len(findings),
    }
    return json.dumps(aggregate)


@tool
def publish_review_results(session_id: str, findings: list[dict]) -> str:
    """Publish the final edited findings JSON to S3 and return a presigned URL.

    Parameters
    ----------
    session_id : str
        The orchestrator session id, used to namespace final review output.
    findings : list[dict]
        Final edited review findings. Each item should contain: page, quote, issue,
        fix, reference, source, type, and score.

    Returns
    -------
    str
        JSON with the S3 URI, issue count, and a `[REVIEW_URL:...]` marker consumed
        by the frontend.
    """
    if not STAGING_BUCKET:
        raise RuntimeError("STAGING_BUCKET_NAME environment variable is not set")

    if not isinstance(findings, list):
        raise ValueError("findings must be a JSON array of review issue objects")

    safe_session = re.sub(r"[^a-zA-Z0-9_-]", "_", session_id)
    key = f"{REVIEWS_PREFIX}/{safe_session}/review_results.json"
    body = json.dumps(findings, indent=2).encode("utf-8")
    s3_client.put_object(
        Bucket=STAGING_BUCKET,
        Key=key,
        Body=body,
        ContentType="application/json",
    )
    url = presign_s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": STAGING_BUCKET, "Key": key},
        ExpiresIn=URL_EXPIRATION,
    )
    result = {
        "s3_uri": f"s3://{STAGING_BUCKET}/{key}",
        "count": len(findings),
        "review_url": url,
    }
    return json.dumps(result) + f"\n\n[REVIEW_URL:{url}]"
