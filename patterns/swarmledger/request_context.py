# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0


def build_context_block(
    session_id: str,
    content_pdf_uri: str | None,
    content_pdf_name: str | None,
    reference_uris: list[str],
    reference_names: list[str],
    enabled_sources: list[str],
) -> str:
    """Build the per-request input block that gets appended to the user prompt."""
    lines = [
        "## Accounting intake inputs",
        f"- session_id: `{session_id}`",
        "- content_pdf:",
        f"  - s3_uri: `{content_pdf_uri or '(missing)'}`",
        f"  - original_filename: `{content_pdf_name or '(unknown)'}`",
        "- references:",
    ]
    if reference_uris:
        for i, uri in enumerate(reference_uris):
            name = (
                reference_names[i]
                if i < len(reference_names) and reference_names[i]
                else "(unknown)"
            )
            lines.append(f"  - s3_uri: `{uri}` - original_filename: `{name}`")
    else:
        lines.append("  - (none)")
    lines.append(f"- enabled_sources: {enabled_sources}")
    return "\n".join(lines)
