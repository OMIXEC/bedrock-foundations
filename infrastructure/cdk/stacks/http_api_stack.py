"""HTTP API Gateway (v2) stack for lightweight Bedrock endpoints.

Deploys Lambda functions for embeddings and prompt routing behind an
HTTP API Gateway with CORS and least-privilege IAM.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import aws_cdk as cdk
from aws_cdk import (
    Duration,
    Stack,
    CfnOutput,
    Tags,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as integrations,
    aws_iam as iam,
    aws_lambda as _lambda,
)
from constructs import Construct

_LAMBDAS_DIR = str(Path(__file__).resolve().parent.parent.parent / "lambdas")


class BedrockHttpApiStack(Stack):
    """HTTP API Gateway stack for embeddings and prompt routing.

    Resources created:
        - 2 Lambda functions (embeddings, prompt_router).
        - HTTP API Gateway v2 with CORS.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        env_name: str = "dev",
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        Tags.of(self).add("Project", "bedrock-enterprise")
        Tags.of(self).add("Environment", env_name)

        # ------------------------------------------------------------------
        # Shared settings
        # ------------------------------------------------------------------
        runtime = _lambda.Runtime.PYTHON_3_12
        default_memory = 256
        default_timeout = Duration.seconds(30)

        bedrock_invoke_policy = iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=["arn:aws:bedrock:*::foundation-model/*"],
            effect=iam.Effect.ALLOW,
        )

        def _make_role(id_: str) -> iam.Role:
            role = iam.Role(
                self,
                id_,
                assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name(
                        "service-role/AWSLambdaBasicExecutionRole"
                    ),
                ],
            )
            role.add_to_policy(bedrock_invoke_policy)
            return role

        # ------------------------------------------------------------------
        # Lambda functions
        # ------------------------------------------------------------------
        embeddings_fn = _lambda.Function(
            self,
            "EmbeddingsFunction",
            function_name=f"bedrock-embeddings-{env_name}",
            runtime=runtime,
            handler="embeddings.handler",
            code=_lambda.Code.from_asset(os.path.join(_LAMBDAS_DIR, "embeddings")),
            memory_size=default_memory,
            timeout=default_timeout,
            role=_make_role("EmbeddingsRole"),
            environment={
                "ENV": env_name,
                "MODEL_ID": "amazon.titan-embed-text-v2:0",
            },
        )

        prompt_router_fn = _lambda.Function(
            self,
            "PromptRouterFunction",
            function_name=f"bedrock-prompt-router-{env_name}",
            runtime=runtime,
            handler="prompt_router.handler",
            code=_lambda.Code.from_asset(
                os.path.join(_LAMBDAS_DIR, "prompt_router")
            ),
            memory_size=default_memory,
            timeout=default_timeout,
            role=_make_role("PromptRouterRole"),
            environment={
                "ENV": env_name,
                "MODEL_ID": "anthropic.claude-sonnet-4-20250514-v1:0",
            },
        )

        # ------------------------------------------------------------------
        # HTTP API Gateway v2
        # ------------------------------------------------------------------
        http_api = apigwv2.HttpApi(
            self,
            "BedrockHttpApi",
            api_name=f"bedrock-http-api-{env_name}",
            description="Bedrock enterprise HTTP API",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigwv2.CorsHttpMethod.POST, apigwv2.CorsHttpMethod.GET],
                allow_headers=["Content-Type", "Authorization"],
            ),
        )

        # POST /embeddings
        embeddings_integration = integrations.HttpLambdaIntegration(
            "EmbeddingsIntegration",
            handler=embeddings_fn,
        )
        http_api.add_routes(
            path="/embeddings",
            methods=[apigwv2.HttpMethod.POST],
            integration=embeddings_integration,
        )

        # POST /route
        router_integration = integrations.HttpLambdaIntegration(
            "PromptRouterIntegration",
            handler=prompt_router_fn,
        )
        http_api.add_routes(
            path="/route",
            methods=[apigwv2.HttpMethod.POST],
            integration=router_integration,
        )

        # ------------------------------------------------------------------
        # Outputs
        # ------------------------------------------------------------------
        CfnOutput(
            self,
            "HttpApiUrl",
            value=http_api.api_endpoint,
            description="HTTP API Gateway v2 base URL",
        )
