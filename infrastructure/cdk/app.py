#!/usr/bin/env python3
"""AWS CDK v2 application for deploying Bedrock enterprise solutions.

Deploys seven independent stacks covering REST API, HTTP API, WebSocket API,
RAG, Multimodal RAG, Agent, and Fine-tuning infrastructure patterns.
Environment is selected via CDK context: ``cdk deploy -c env=prod``.
"""

import os

import aws_cdk as cdk

from stacks.rest_api_stack import BedrockRestApiStack
from stacks.http_api_stack import BedrockHttpApiStack
from stacks.websocket_stack import BedrockWebSocketStack
from stacks.rag_stack import BedrockRagStack
from stacks.multimodal_rag_stack import BedrockMultimodalRagStack
from stacks.agent_stack import BedrockAgentStack
from stacks.finetuning_stack import BedrockFinetuningStack

app = cdk.App()

env_name: str = app.node.try_get_context("env") or "dev"

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)

# ---------------------------------------------------------------------------
# Deploy stacks -- each stack is independently deployable via:
#   cdk deploy bedrock-rest-api-dev
#   cdk deploy bedrock-http-api-dev
#   cdk deploy bedrock-websocket-dev
#   cdk deploy bedrock-rag-dev
#   cdk deploy bedrock-multimodal-rag-dev
#   cdk deploy bedrock-agent-dev
#   cdk deploy bedrock-finetuning-dev
# ---------------------------------------------------------------------------

rest = BedrockRestApiStack(
    app,
    f"bedrock-rest-api-{env_name}",
    env=env,
    env_name=env_name,
)

http = BedrockHttpApiStack(
    app,
    f"bedrock-http-api-{env_name}",
    env=env,
    env_name=env_name,
)

ws = BedrockWebSocketStack(
    app,
    f"bedrock-websocket-{env_name}",
    env=env,
    env_name=env_name,
)

rag = BedrockRagStack(
    app,
    f"bedrock-rag-{env_name}",
    env=env,
    env_name=env_name,
)

multimodal = BedrockMultimodalRagStack(
    app,
    f"bedrock-multimodal-rag-{env_name}",
    env=env,
    env_name=env_name,
)

agent = BedrockAgentStack(
    app,
    f"bedrock-agent-{env_name}",
    env=env,
    env_name=env_name,
)

ft = BedrockFinetuningStack(
    app,
    f"bedrock-finetuning-{env_name}",
    env=env,
    env_name=env_name,
)

app.synth()
