# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Generic reviewer: spelling, grammar, language exaggeration, and image consistency."""

import re

from strands import tool

from reviewers._common import (
    FINDINGS_SCHEMA_HINT,
    batch_stem,
    load_prompt,
    read_s3_text,
    run_inner_agent,
    write_review_json,
)

SYSTEM_PROMPT = load_prompt("generic_reviewer").format(schema=FINDINGS_SCHEMA_HINT)

PAGE_PATTERN = re.compile(r"\[page (?P<page>\d+)\]\n(?P<body>.*?)\n\[/page \1\]", re.DOTALL)

HIGH_RISK_PROMOTIONAL_PATTERNS: list[tuple[re.Pattern[str], str, str, int]] = [
    (
        re.compile(
            r"[^.\n]*(?:\d{2,3}%\s+reduction\s+in\s+cardiovascular\s+mortality|"
            r"cardiovascular\s+mortality\s+within\s+\d+\s+days)[^.\n]*[.]?",
            re.IGNORECASE,
        ),
        "High-magnitude mortality reduction in a very short treatment window is an extreme promotional clinical claim that requires careful substantiation and fair balance.",
        "Qualify the mortality claim, cite the exact approved/evidentiary source, and add balanced safety and limitations language.",
        95,
    ),
    (
        re.compile(
            r"[^.\n]*(?:completely\s+eliminated|eliminated\s+recurrent\s+stroke)[^.\n]*[.]?",
            re.IGNORECASE,
        ),
        "Absolute disease outcome language such as complete elimination overstates efficacy and creates a mandatory adherence risk.",
        "Replace absolute wording with precise, supported study results and include uncertainty, population, and endpoint limitations.",
        95,
    ),
    (
        re.compile(
            r"[^.\n]*(?:near-immediate|immediate)\s+symptom\s+resolution[^.\n]*[.]?",
            re.IGNORECASE,
        ),
        "Near-immediate symptom-resolution language is overconfident and may imply guaranteed rapid benefit.",
        "Use measured onset and response data from the supporting evidence, with appropriate qualifiers.",
        85,
    ),
    (
        re.compile(
            r"[^.\n]*(?:zero\s+severe\s+adverse\s+events|no\s+severe\s+adverse\s+events)[^.\n]*[.]?",
            re.IGNORECASE,
        ),
        "Absolute safety language such as zero severe adverse events can mislead readers about risk, especially in high-risk populations.",
        "State observed safety results exactly and add balanced risk information and study limitations.",
        95,
    ),
    (
        re.compile(
            r"[^.\n]*(?:first-line\s+therapy|superior\s+efficacy\s+compared\s+to\s+standard\s+of\s+care)[^.\n]*[.]?",
            re.IGNORECASE,
        ),
        "Broad first-line positioning and superiority claims are high-risk promotional claims when not tightly tied to approved labeling and evidence.",
        "Limit positioning to approved use and cite comparative evidence with balanced context.",
        90,
    ),
]


def _page_sections(markdown: str) -> list[tuple[int, str]]:
    sections = [
        (int(match.group("page")), match.group("body"))
        for match in PAGE_PATTERN.finditer(markdown)
    ]
    return sections or [(1, markdown)]


def _dedupe_findings(findings: list[dict]) -> list[dict]:
    seen: set[tuple[int | None, str]] = set()
    deduped: list[dict] = []
    for finding in findings:
        page = finding.get("page") if isinstance(finding.get("page"), int) else None
        quote = str(finding.get("quote", "")).strip().lower()
        key = (page, quote)
        if quote and key in seen:
            continue
        if quote:
            seen.add(key)
        deduped.append(finding)
    return deduped


def _detect_high_risk_promotional_claims(markdown: str) -> list[dict]:
    findings: list[dict] = []
    for page, body in _page_sections(markdown):
        for pattern, issue, fix, score in HIGH_RISK_PROMOTIONAL_PATTERNS:
            for match in pattern.finditer(body):
                quote = " ".join(match.group(0).split())
                if not quote:
                    continue
                findings.append(
                    {
                        "page": page,
                        "quote": quote,
                        "issue": issue,
                        "fix": fix,
                        "reference": "",
                        "source": "",
                        "type": "mandatory",
                        "score": score,
                    }
                )
    return _dedupe_findings(findings)


@tool
def run_generic_review(batch_md_s3_uri: str, session_id: str) -> str:
    """Run the generic reviewer on a single batch markdown and save findings to S3.

    Internally spins up a narrow sub-agent that checks spelling, grammar,
    language exaggeration, and figure/image description consistency. The
    sub-agent has no external tools — it works purely off the provided batch
    markdown.

    Parameters
    ----------
    batch_md_s3_uri : str
        S3 URI of a batch markdown file produced by `batch_content`.
    session_id : str
        The orchestrator's runtime session id, used to namespace review outputs
        under `reviews/{session_id}/`.

    Returns
    -------
    str
        S3 URI of the written findings JSON. Nothing else is returned.
    """
    markdown = read_s3_text(batch_md_s3_uri)
    findings = run_inner_agent(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=f"Review this batch:\n\n{markdown}",
        tools=[],
    )
    findings = _dedupe_findings(
        findings + _detect_high_risk_promotional_claims(markdown)
    )
    return write_review_json(
        session_id, "generic", batch_stem(batch_md_s3_uri), findings
    )
