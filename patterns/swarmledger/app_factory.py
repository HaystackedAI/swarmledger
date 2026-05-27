# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware


def create_app() -> BedrockAgentCoreApp:
    return BedrockAgentCoreApp(
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=[
                    "http://localhost:3000",
                    "http://127.0.0.1:3000",
                ],
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["*"],
            )
        ]
    )
