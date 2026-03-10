"""REST API Gateway stack for Bedrock enterprise Lambda functions.

Deploys five Lambda functions behind an API Gateway REST API with
least-privilege IAM, optional API key authentication, CORS, and
CloudWatch logging.
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
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_s3 as s3,
)
from constructs import Construct

_LAMBDAS_DIR = str(Path(__file__).resolve().parent.parent.parent / "lambdas")


class BedrockRestApiStack(Stack):
    """REST API Gateway stack exposing Bedrock-powered Lambda functions.

    Resources created:
        - 5 Lambda functions (chatbot, rag_query, text_summarization,
          image_generation, multimodal_rag) plus an inline health check.
        - API Gateway REST API with CORS and optional API key.
        - S3 bucket for image generation output.
        - CloudWatch log group for API Gateway access logs.
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
        # S3 bucket for image generation output
        # ------------------------------------------------------------------
        image_bucket = s3.Bucket(
            self,
            "ImageOutputBucket",
            bucket_name=f"bedrock-image-output-{env_name}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=removal,
            auto_delete_objects=(env_name == "dev"),
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
        )

        # ------------------------------------------------------------------
        # Shared Lambda settings
        # ------------------------------------------------------------------
        runtime = _lambda.Runtime.PYTHON_3_12
        default_memory = 256
        default_timeout = Duration.seconds(30)
        chatbot_timeout = Duration.seconds(60)

        # ------------------------------------------------------------------
        # IAM roles (least-privilege)
        # ------------------------------------------------------------------
        bedrock_invoke_policy = iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=["arn:aws:bedrock:*::foundation-model/*"],
            effect=iam.Effect.ALLOW,
        )

        bedrock_rag_policy = iam.PolicyStatement(
            actions=[
                "bedrock:InvokeModel",
                "bedrock:Retrieve",
                "bedrock:RetrieveAndGenerate",
            ],
            resources=["*"],
            effect=iam.Effect.ALLOW,
        )

        image_gen_s3_policy = iam.PolicyStatement(
            actions=["s3:PutObject"],
            resources=[image_bucket.arn_for_objects("*")],
            effect=iam.Effect.ALLOW,
        )

        def _make_role(id_: str, statements: list[iam.PolicyStatement]) -> iam.Role:
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
            for stmt in statements:
                role.add_to_policy(stmt)
            return role

        chatbot_role = _make_role("ChatbotRole", [bedrock_invoke_policy])
        rag_role = _make_role("RagQueryRole", [bedrock_rag_policy])
        summarization_role = _make_role("SummarizationRole", [bedrock_invoke_policy])
        image_gen_role = _make_role(
            "ImageGenRole", [bedrock_invoke_policy, image_gen_s3_policy]
        )
        multimodal_rag_role = _make_role("MultimodalRagRole", [bedrock_rag_policy])

        # ------------------------------------------------------------------
        # Lambda functions
        # ------------------------------------------------------------------
        chatbot_fn = _lambda.Function(
            self,
            "ChatbotFunction",
            function_name=f"bedrock-chatbot-{env_name}",
            runtime=runtime,
            handler="chatbot.handler",
            code=_lambda.Code.from_asset(os.path.join(_LAMBDAS_DIR, "chatbot")),
            memory_size=default_memory,
            timeout=chatbot_timeout,
            role=chatbot_role,
            environment={
                "ENV": env_name,
                "MODEL_ID": "anthropic.claude-sonnet-4-20250514-v1:0",
            },
        )

        rag_query_fn = _lambda.Function(
            self,
            "RagQueryFunction",
            function_name=f"bedrock-rag-query-{env_name}",
            runtime=runtime,
            handler="rag_query.handler",
            code=_lambda.Code.from_asset(os.path.join(_LAMBDAS_DIR, "rag_query")),
            memory_size=default_memory,
            timeout=default_timeout,
            role=rag_role,
            environment={"ENV": env_name},
        )

        summarization_fn = _lambda.Function(
            self,
            "SummarizationFunction",
            function_name=f"bedrock-summarization-{env_name}",
            runtime=runtime,
            handler="text_summarization.handler",
            code=_lambda.Code.from_asset(
                os.path.join(_LAMBDAS_DIR, "text_summarization")
            ),
            memory_size=default_memory,
            timeout=default_timeout,
            role=summarization_role,
            environment={
                "ENV": env_name,
                "MODEL_ID": "anthropic.claude-sonnet-4-20250514-v1:0",
            },
        )

        image_gen_fn = _lambda.Function(
            self,
            "ImageGenerationFunction",
            function_name=f"bedrock-image-gen-{env_name}",
            runtime=runtime,
            handler="image_generation.handler",
            code=_lambda.Code.from_asset(
                os.path.join(_LAMBDAS_DIR, "image_generation")
            ),
            memory_size=default_memory,
            timeout=default_timeout,
            role=image_gen_role,
            environment={
                "ENV": env_name,
                "IMAGE_BUCKET": image_bucket.bucket_name,
                "MODEL_ID": "amazon.titan-image-generator-v2:0",
            },
        )

        multimodal_rag_fn = _lambda.Function(
            self,
            "MultimodalRagFunction",
            function_name=f"bedrock-multimodal-rag-{env_name}",
            runtime=runtime,
            handler="multimodal_rag.handler",
            code=_lambda.Code.from_asset(
                os.path.join(_LAMBDAS_DIR, "multimodal_rag")
            ),
            memory_size=default_memory,
            timeout=default_timeout,
            role=multimodal_rag_role,
            environment={"ENV": env_name},
        )

        # Inline health-check Lambda
        health_fn = _lambda.Function(
            self,
            "HealthCheckFunction",
            function_name=f"bedrock-health-{env_name}",
            runtime=runtime,
            handler="index.handler",
            code=_lambda.Code.from_inline(
                'import json\n\ndef handler(event, context):\n    return {\n        "statusCode": 200,\n        "headers": {"Content-Type": "application/json"},\n        "body": json.dumps({"status": "healthy", "service": "bedrock-rest-api"}),\n    }\n'
            ),
            memory_size=128,
            timeout=Duration.seconds(5),
        )

        # ------------------------------------------------------------------
        # CloudWatch log group for API Gateway
        # ------------------------------------------------------------------
        api_log_group = logs.LogGroup(
            self,
            "ApiLogGroup",
            log_group_name=f"/aws/apigateway/bedrock-rest-api-{env_name}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=removal,
        )

        # ------------------------------------------------------------------
        # REST API Gateway
        # ------------------------------------------------------------------
        api = apigw.RestApi(
            self,
            "BedrockRestApi",
            rest_api_name=f"bedrock-rest-api-{env_name}",
            description="Bedrock enterprise REST API",
            deploy_options=apigw.StageOptions(
                stage_name=env_name,
                logging_level=apigw.MethodLoggingLevel.INFO,
                access_log_destination=apigw.LogGroupLogDestination(api_log_group),
                access_log_format=apigw.AccessLogFormat.json_with_standard_fields(),
                throttling_rate_limit=100,
                throttling_burst_limit=200,
            ),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=[
                    "Content-Type",
                    "X-Amz-Date",
                    "Authorization",
                    "X-Api-Key",
                ],
            ),
        )

        # --- Routes ---
        # POST /chat
        chat_resource = api.root.add_resource("chat")
        chat_resource.add_method(
            "POST",
            apigw.LambdaIntegration(chatbot_fn),
        )

        # POST /rag/query
        rag_resource = api.root.add_resource("rag")
        rag_query_resource = rag_resource.add_resource("query")
        rag_query_resource.add_method(
            "POST",
            apigw.LambdaIntegration(rag_query_fn),
        )

        # POST /summarize
        summarize_resource = api.root.add_resource("summarize")
        summarize_resource.add_method(
            "POST",
            apigw.LambdaIntegration(summarization_fn),
        )

        # POST /generate/image
        generate_resource = api.root.add_resource("generate")
        image_resource = generate_resource.add_resource("image")
        image_resource.add_method(
            "POST",
            apigw.LambdaIntegration(image_gen_fn),
        )

        # POST /multimodal/query
        multimodal_resource = api.root.add_resource("multimodal")
        multimodal_query_resource = multimodal_resource.add_resource("query")
        multimodal_query_resource.add_method(
            "POST",
            apigw.LambdaIntegration(multimodal_rag_fn),
        )

        # GET /health
        health_resource = api.root.add_resource("health")
        health_resource.add_method(
            "GET",
            apigw.LambdaIntegration(health_fn),
        )

        # ------------------------------------------------------------------
        # Optional API key + usage plan (enabled via context flag)
        # ------------------------------------------------------------------
        enable_api_key: bool = self.node.try_get_context("enable_api_key") or False
        if enable_api_key:
            api_key = api.add_api_key(
                "BedrockApiKey",
                api_key_name=f"bedrock-api-key-{env_name}",
            )
            plan = api.add_usage_plan(
                "UsagePlan",
                name=f"bedrock-usage-plan-{env_name}",
                throttle=apigw.ThrottleSettings(
                    rate_limit=50,
                    burst_limit=100,
                ),
                quota=apigw.QuotaSettings(
                    limit=10_000,
                    period=apigw.Period.MONTH,
                ),
            )
            plan.add_api_key(api_key)
            plan.add_api_stage(stage=api.deployment_stage)

        # ------------------------------------------------------------------
        # Outputs
        # ------------------------------------------------------------------
        CfnOutput(
            self,
            "RestApiUrl",
            value=api.url,
            description="REST API Gateway base URL",
        )
        CfnOutput(
            self,
            "ImageBucketName",
            value=image_bucket.bucket_name,
            description="S3 bucket for generated images",
        )
