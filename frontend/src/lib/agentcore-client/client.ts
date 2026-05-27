// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import type {
    AgentCoreConfig,
    AgentPattern,
    ChunkParser,
    StreamCallback,
} from "./types";
import { parseStrandsChunk } from "./parsers/strands";
import { readSSEStream } from "./utils/sse";

const PARSERS: Record<AgentPattern, ChunkParser> = {
    "medical-content-review": parseStrandsChunk,
};

const DEBUG_PREFIX = "[Accounting Intake]";

function base64UrlEncode(value: unknown): string {
    const encoded = btoa(JSON.stringify(value));
    return encoded.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function createLocalMockJwt(): string {
    return [
        base64UrlEncode({ alg: "none", typ: "JWT" }),
        base64UrlEncode({ sub: "local-frontend-user" }),
        "",
    ].join(".");
}

export class AgentCoreClient {
    private runtimeArn: string;
    private region: string;
    private parser: ChunkParser;
    private localEndpoint?: string;

    constructor(config: AgentCoreConfig) {
        this.runtimeArn = config.runtimeArn;
        this.region = config.region ?? "us-east-1";
        this.parser = PARSERS[config.pattern];
        this.localEndpoint = config.localEndpoint?.replace(/\/$/, "");
    }

    // Abort any in-flight stream
    abort(): void {
        this._abortController?.abort();
        this._abortController = null;
    }

    private _abortController: AbortController | null = null;

    async invoke(
        query: string,
        sessionId: string,
        accessToken: string,
        onEvent: StreamCallback,
        enabledSources?: string[],
        contentPdfUri?: string,
        referenceUris?: string[],
        contentPdfName?: string,
        referenceNames?: string[],
    ): Promise<void> {
        if (!accessToken && !this.localEndpoint)
            throw new Error("No valid access token found.");
        if (!this.runtimeArn && !this.localEndpoint)
            throw new Error("Agent Runtime ARN not configured.");

        // Abort any previous in-flight request
        this._abortController?.abort();
        this._abortController = new AbortController();

        const endpoint =
            this.localEndpoint ?? `https://bedrock-agentcore.${this.region}.amazonaws.com`;
        const escapedArn = encodeURIComponent(this.runtimeArn);
        const url = this.localEndpoint
            ? `${this.localEndpoint}/invocations`
            : `${endpoint}/runtimes/${escapedArn}/invocations?qualifier=DEFAULT`;

        const traceId = `1-${Math.floor(Date.now() / 1000).toString(
            16,
        )}-${crypto.randomUUID()}`;

        // Build payload with optional enabled sources
        const payload: Record<string, unknown> = {
            prompt: query,
            runtimeSessionId: sessionId,
        };

        if (enabledSources) {
            payload.enabledSources = enabledSources;
        }

        if (contentPdfUri) {
            payload.contentPdfUri = contentPdfUri;
        }
        if (contentPdfName) {
            payload.contentPdfName = contentPdfName;
        }

        if (referenceUris && referenceUris.length > 0) {
            payload.referenceUris = referenceUris;
        }
        if (referenceNames && referenceNames.length > 0) {
            payload.referenceNames = referenceNames;
        }

        // User identity is extracted server-side from the validated JWT token
        // (Authorization header), not sent in the payload body. This prevents
        // impersonation via prompt injection.
        const headers: Record<string, string> = {
            "Content-Type": "application/json",
            "X-Amzn-Trace-Id": traceId,
            "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": sessionId,
        };
        if (accessToken) {
            headers.Authorization = `Bearer ${accessToken}`;
        } else if (this.localEndpoint) {
            headers.Authorization = `Bearer ${createLocalMockJwt()}`;
        }

        console.info(`${DEBUG_PREFIX} Invoking AgentCore Runtime`, {
            endpoint,
            url,
            runtimeArn: this.runtimeArn,
            region: this.region,
            sessionId,
            traceId,
            headers: {
                Authorization: headers.Authorization ? "Bearer <redacted>" : undefined,
                "X-Amzn-Trace-Id": traceId,
                "Content-Type": "application/json",
                "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": sessionId,
            },
            payload,
        });

        const response = await fetch(url, {
            method: "POST",
            headers,
            body: JSON.stringify(payload),
            signal: this._abortController.signal,
        });

        console.info(`${DEBUG_PREFIX} AgentCore response received`, {
            status: response.status,
            statusText: response.statusText,
            contentType: response.headers.get("content-type"),
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`${DEBUG_PREFIX} AgentCore invocation failed`, {
                status: response.status,
                statusText: response.statusText,
                body: errorText,
            });
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        await readSSEStream(response, this.parser, onEvent);
    }
}
