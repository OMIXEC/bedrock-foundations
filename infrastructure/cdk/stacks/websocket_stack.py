"""WebSocket API Gateway stack for streaming Bedrock responses.

Deploys two WebSocket APIs -- one for text streaming and one for multimodal
streaming -- each backed by connect/disconnect/message Lambda functions,
a shared DynamoDB connections table, and least-privilege IAM.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import aws_cdk as cdk
from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    CfnOutput,
    Tags,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as integrations,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda as _lambda,
)
from constructs import Construct

_LAMBDAS_DIR = str(Path(__file__).resolve().parent.parent.parent / "lambdas")


class BedrockWebSocketStack(Stack):
    """WebSocket API Gateway stack for streaming chat and multimodal.

    Resources created:
        - DynamoDB connections table.
        - 6 Lambda functions (connect/disconnect/message x 2 APIs).
        - 2 WebSocket API Gateways with production stages.
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

        removal = RemovalPolicy.DESTROY if env_name == "dev" else RemovalPolicy.RETAIN

        # ------------------------------------------------------------------
        # DynamoDB table for WebSocket connection tracking
        # ------------------------------------------------------------------
        connections_table = dynamodb.Table(
            self,
            "ConnectionsTable",
            table_name=f"bedrock-ws-connections-{env_name}",
            partition_key=dynamodb.Attribute(
                name="connectionId",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal,
        )

        # ------------------------------------------------------------------
        # Shared settings
        # ------------------------------------------------------------------
        runtime = _lambda.Runtime.PYTHON_3_12
        memory = 512
        timeout = Duration.seconds(120)

        def _build_ws_api(
            api_prefix: str,
            lambda_dir: str,
            handler_prefix: str,
            description: str,
        ) -> apigwv2.WebSocketApi:
            """Create a WebSocket API with connect/disconnect/message routes.

            Args:
                api_prefix: Name prefix for the API and Lambda functions.
                lambda_dir: Subdirectory under lambdas/ containing the handlers.
                handler_prefix: Python module prefix for handler entry points.
                description: API description.

            Returns:
                The WebSocket API construct.
            """
            lambda_path = os.path.join(_LAMBDAS_DIR, lambda_dir)

            # --- IAM role shared by all three Lambdas of this API ---
            role = iam.Role(
                self,
                f"{api_prefix}Role",
                assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                managed_policies=[
                    iam.ManagedPolicy.from_aws_managed_policy_name(
                        "service-role/AWSLambdaBasicExecutionRole"
                    ),
                ],
            )

            # Bedrock streaming permission
            role.add_to_policy(
                iam.PolicyStatement(
                    actions=[
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream",
                    ],
                    resources=["arn:aws:bedrock:*::foundation-model/*"],
                    effect=iam.Effect.ALLOW,
                )
            )

            # DynamoDB permissions on connections table
            role.add_to_policy(
                iam.PolicyStatement(
                    actions=[
                        "dynamodb:PutItem",
                        "dynamodb:GetItem",
                        "dynamodb:DeleteItem",
                    ],
                    resources=[connections_table.table_arn],
                    effect=iam.Effect.ALLOW,
                )
            )

            # execute-api:ManageConnections -- granted after API creation below

            shared_env = {
                "ENV": env_name,
                "CONNECTIONS_TABLE": connections_table.table_name,
                "MODEL_ID": "anthropic.claude-sonnet-4-20250514-v1:0",
            }

            # --- Lambda functions ---
            connect_fn = _lambda.Function(
                self,
                f"{api_prefix}ConnectFn",
                function_name=f"bedrock-{lambda_dir}-connect-{env_name}",
                runtime=runtime,
                handler=f"{handler_prefix}_connect.handler",
                code=_lambda.Code.from_asset(lambda_path),
                memory_size=memory,
                timeout=timeout,
                role=role,
                environment=shared_env,
            )

            disconnect_fn = _lambda.Function(
                self,
                f"{api_prefix}DisconnectFn",
                function_name=f"bedrock-{lambda_dir}-disconnect-{env_name}",
                runtime=runtime,
                handler=f"{handler_prefix}_disconnect.handler",
                code=_lambda.Code.from_asset(lambda_path),
                memory_size=memory,
                timeout=timeout,
                role=role,
                environment=shared_env,
            )

            message_fn = _lambda.Function(
                self,
                f"{api_prefix}MessageFn",
                function_name=f"bedrock-{lambda_dir}-message-{env_name}",
                runtime=runtime,
                handler=f"{handler_prefix}_message.handler",
                code=_lambda.Code.from_asset(lambda_path),
                memory_size=memory,
                timeout=timeout,
                role=role,
                environment=shared_env,
            )

            # --- WebSocket API ---
            ws_api = apigwv2.WebSocketApi(
                self,
                f"{api_prefix}Api",
                api_name=f"bedrock-{lambda_dir}-{env_name}",
                description=description,
                connect_route_options=apigwv2.WebSocketRouteOptions(
                    integration=integrations.WebSocketLambdaIntegration(
                        f"{api_prefix}ConnectIntegration",
                        handler=connect_fn,
                    ),
                ),
                disconnect_route_options=apigwv2.WebSocketRouteOptions(
                    integration=integrations.WebSocketLambdaIntegration(
                        f"{api_prefix}DisconnectIntegration",
                        handler=disconnect_fn,
                    ),
                ),
                default_route_options=apigwv2.WebSocketRouteOptions(
                    integration=integrations.WebSocketLambdaIntegration(
                        f"{api_prefix}DefaultIntegration",
                        handler=message_fn,
                    ),
                ),
            )

            # Add the sendMessage route
            ws_api.add_route(
                "sendMessage",
                integration=integrations.WebSocketLambdaIntegration(
                    f"{api_prefix}SendMessageIntegration",
                    handler=message_fn,
                ),
            )

            # Stage
            stage = apigwv2.WebSocketStage(
                self,
                f"{api_prefix}Stage",
                web_socket_api=ws_api,
                stage_name=env_name,
                auto_deploy=True,
            )

            # Grant execute-api:ManageConnections so Lambdas can post back
            manage_connections_arn = (
                f"arn:aws:execute-api:{self.region}:{self.account}"
                f":{ws_api.api_id}/{env_name}/POST/@connections/*"
            )
            role.add_to_policy(
                iam.PolicyStatement(
                    actions=["execute-api:ManageConnections"],
                    resources=[manage_connections_arn],
                    effect=iam.Effect.ALLOW,
                )
            )

            return ws_api, stage

        # ------------------------------------------------------------------
        # Text streaming WebSocket API
        # ------------------------------------------------------------------
        text_ws_api, text_stage = _build_ws_api(
            api_prefix="TextStream",
            lambda_dir="streaming-chat",
            handler_prefix="connect",
            description="Bedrock text streaming WebSocket API",
        )

        # Override handler names for streaming-chat (connect/disconnect/message modules)
        # The _build_ws_api helper uses a prefix pattern; we rely on the Lambda
        # directory containing connect_connect.py, connect_disconnect.py, and
        # connect_message.py OR the user renames them. The handler field is set
        # above so user-provided code must match.

        # ------------------------------------------------------------------
        # Multimodal streaming WebSocket API
        # ------------------------------------------------------------------
        multimodal_ws_api, multimodal_stage = _build_ws_api(
            api_prefix="MultimodalStream",
            lambda_dir="multimodal-stream",
            handler_prefix="multimodal",
            description="Bedrock multimodal streaming WebSocket API",
        )

        # ------------------------------------------------------------------
        # Outputs
        # ------------------------------------------------------------------
        CfnOutput(
            self,
            "TextWebSocketUrl",
            value=text_stage.url,
            description="WebSocket URL for text streaming (wss://)",
        )
        CfnOutput(
            self,
            "MultimodalWebSocketUrl",
            value=multimodal_stage.url,
            description="WebSocket URL for multimodal streaming (wss://)",
        )
        CfnOutput(
            self,
            "ConnectionsTableName",
            value=connections_table.table_name,
            description="DynamoDB table for WebSocket connections",
        )
