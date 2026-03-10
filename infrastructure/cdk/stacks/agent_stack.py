"""Bedrock Agent stack with action group Lambda and DynamoDB backing store.

Deploys a Bedrock Agent configured with an action group that invokes a
Lambda function for tool execution.  A DynamoDB table provides mock
banking data for the agent's action group.
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
    aws_bedrock as bedrock,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda as _lambda,
)
from constructs import Construct

_LAMBDAS_DIR = str(Path(__file__).resolve().parent.parent.parent / "lambdas")

_AGENT_INSTRUCTION = (
    "You are a helpful banking assistant. You can look up account balances, "
    "list recent transactions, and transfer funds between accounts. Always "
    "confirm details with the user before executing a transfer. Be concise "
    "and professional in your responses."
)

_ACTION_GROUP_SCHEMA = {
    "openapi": "3.0.0",
    "info": {
        "title": "Banking Actions API",
        "version": "1.0.0",
        "description": "API for banking operations via Bedrock Agent",
    },
    "paths": {
        "/getBalance": {
            "post": {
                "summary": "Get account balance",
                "description": "Retrieves the current balance for a given account ID.",
                "operationId": "getBalance",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "accountId": {
                                        "type": "string",
                                        "description": "The unique account identifier",
                                    }
                                },
                                "required": ["accountId"],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Account balance",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "accountId": {"type": "string"},
                                        "balance": {"type": "number"},
                                        "currency": {"type": "string"},
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/getTransactions": {
            "post": {
                "summary": "Get recent transactions",
                "description": "Retrieves the most recent transactions for an account.",
                "operationId": "getTransactions",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "accountId": {
                                        "type": "string",
                                        "description": "The unique account identifier",
                                    },
                                    "limit": {
                                        "type": "integer",
                                        "description": "Maximum number of transactions to return",
                                        "default": 10,
                                    },
                                },
                                "required": ["accountId"],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "List of transactions",
                    }
                },
            }
        },
        "/transferFunds": {
            "post": {
                "summary": "Transfer funds between accounts",
                "description": "Transfers a specified amount from one account to another.",
                "operationId": "transferFunds",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "sourceAccountId": {
                                        "type": "string",
                                        "description": "Source account ID",
                                    },
                                    "destinationAccountId": {
                                        "type": "string",
                                        "description": "Destination account ID",
                                    },
                                    "amount": {
                                        "type": "number",
                                        "description": "Amount to transfer",
                                    },
                                },
                                "required": [
                                    "sourceAccountId",
                                    "destinationAccountId",
                                    "amount",
                                ],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Transfer confirmation",
                    }
                },
            }
        },
    },
}


class BedrockAgentStack(Stack):
    """Bedrock Agent stack with action group and DynamoDB backing store.

    Resources created:
        - DynamoDB table for mock banking data.
        - Lambda function for agent action group execution.
        - Bedrock Agent (CfnAgent) with action group.
        - Bedrock Agent Alias for invocation.
        - IAM roles with least-privilege access.
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
        # DynamoDB table for mock banking data
        # ------------------------------------------------------------------
        banking_table = dynamodb.Table(
            self,
            "BankingDataTable",
            table_name=f"bedrock-agent-banking-{env_name}",
            partition_key=dynamodb.Attribute(
                name="accountId",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="recordType",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal,
        )

        # ------------------------------------------------------------------
        # Lambda function for agent action group
        # ------------------------------------------------------------------
        action_role = iam.Role(
            self,
            "AgentActionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )
        action_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:Query",
                ],
                resources=[banking_table.table_arn],
                effect=iam.Effect.ALLOW,
            )
        )

        action_fn = _lambda.Function(
            self,
            "AgentActionFunction",
            function_name=f"bedrock-agent-action-{env_name}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="agent_action.handler",
            code=_lambda.Code.from_asset(
                os.path.join(_LAMBDAS_DIR, "agent_action")
            ),
            memory_size=256,
            timeout=Duration.seconds(30),
            role=action_role,
            environment={
                "ENV": env_name,
                "BANKING_TABLE": banking_table.table_name,
            },
        )

        # Allow Bedrock to invoke the Lambda
        action_fn.add_permission(
            "AllowBedrockInvoke",
            principal=iam.ServicePrincipal("bedrock.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_account=self.account,
        )

        # ------------------------------------------------------------------
        # IAM role for Bedrock Agent
        # ------------------------------------------------------------------
        agent_role = iam.Role(
            self,
            "BedrockAgentRole",
            role_name=f"bedrock-agent-role-{env_name}",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            inline_policies={
                "BedrockInvoke": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["bedrock:InvokeModel"],
                            resources=[
                                f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                    ]
                ),
                "LambdaInvoke": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["lambda:InvokeFunction"],
                            resources=[action_fn.function_arn],
                            effect=iam.Effect.ALLOW,
                        ),
                    ]
                ),
            },
        )

        # ------------------------------------------------------------------
        # Bedrock Agent (L1 construct)
        # ------------------------------------------------------------------
        import json

        agent = bedrock.CfnAgent(
            self,
            "BedrockAgent",
            agent_name=f"bedrock-banking-agent-{env_name}",
            description=f"Banking assistant agent ({env_name})",
            agent_resource_role_arn=agent_role.role_arn,
            foundation_model="anthropic.claude-sonnet-4-20250514-v1:0",
            instruction=_AGENT_INSTRUCTION,
            idle_session_ttl_in_seconds=600,
            action_groups=[
                bedrock.CfnAgent.AgentActionGroupProperty(
                    action_group_name="BankingActions",
                    description="Banking operations: balance lookup, transactions, transfers",
                    action_group_executor=bedrock.CfnAgent.ActionGroupExecutorProperty(
                        lambda_=action_fn.function_arn,
                    ),
                    api_schema=bedrock.CfnAgent.APISchemaProperty(
                        payload=json.dumps(_ACTION_GROUP_SCHEMA),
                    ),
                )
            ],
        )

        # ------------------------------------------------------------------
        # Agent Alias for invocation
        # ------------------------------------------------------------------
        agent_alias = bedrock.CfnAgentAlias(
            self,
            "BedrockAgentAlias",
            agent_id=agent.attr_agent_id,
            agent_alias_name=f"{env_name}-alias",
            description=f"Agent alias for {env_name} environment",
        )

        # ------------------------------------------------------------------
        # Outputs
        # ------------------------------------------------------------------
        CfnOutput(
            self,
            "AgentId",
            value=agent.attr_agent_id,
            description="Bedrock Agent ID",
        )
        CfnOutput(
            self,
            "AgentAliasId",
            value=agent_alias.attr_agent_alias_id,
            description="Bedrock Agent Alias ID",
        )
        CfnOutput(
            self,
            "BankingTableName",
            value=banking_table.table_name,
            description="DynamoDB table for mock banking data",
        )
