"""Fine-tuning infrastructure stack for Bedrock model customization.

Deploys S3 buckets for training data and model output, plus an IAM role
that Bedrock assumes when running a model customization job.  The actual
fine-tuning job is a long-running operation started via CLI script, not CDK.
"""

from __future__ import annotations

from typing import Any

import aws_cdk as cdk
from aws_cdk import (
    RemovalPolicy,
    Stack,
    CfnOutput,
    Tags,
    aws_iam as iam,
    aws_s3 as s3,
)
from constructs import Construct


class BedrockFinetuningStack(Stack):
    """Fine-tuning infrastructure stack for Bedrock model customization.

    Resources created:
        - S3 bucket for training data (versioned, encrypted).
        - S3 bucket for model output (versioned, encrypted).
        - IAM role for Bedrock fine-tuning jobs.

    Note:
        The fine-tuning job itself is started via a CLI script
        (``scripts/start_finetuning.py``) because it is a long-running
        operation that does not fit the declarative CDK model.
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
        # S3 bucket for training data
        # ------------------------------------------------------------------
        training_bucket = s3.Bucket(
            self,
            "TrainingDataBucket",
            bucket_name=f"bedrock-ft-training-{env_name}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=removal,
            auto_delete_objects=(env_name == "dev"),
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
        )

        # ------------------------------------------------------------------
        # S3 bucket for model output
        # ------------------------------------------------------------------
        output_bucket = s3.Bucket(
            self,
            "ModelOutputBucket",
            bucket_name=f"bedrock-ft-output-{env_name}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=removal,
            auto_delete_objects=(env_name == "dev"),
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
        )

        # ------------------------------------------------------------------
        # IAM role for Bedrock fine-tuning jobs
        # ------------------------------------------------------------------
        finetuning_role = iam.Role(
            self,
            "FinetuningRole",
            role_name=f"bedrock-finetuning-role-{env_name}",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            inline_policies={
                "S3TrainingRead": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["s3:GetObject", "s3:ListBucket"],
                            resources=[
                                training_bucket.bucket_arn,
                                training_bucket.arn_for_objects("*"),
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                    ]
                ),
                "S3OutputWrite": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:ListBucket",
                            ],
                            resources=[
                                output_bucket.bucket_arn,
                                output_bucket.arn_for_objects("*"),
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                    ]
                ),
                "BedrockCustomization": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "bedrock:CreateModelCustomizationJob",
                                "bedrock:GetModelCustomizationJob",
                                "bedrock:ListModelCustomizationJobs",
                                "bedrock:StopModelCustomizationJob",
                            ],
                            resources=["*"],
                            effect=iam.Effect.ALLOW,
                        ),
                    ]
                ),
            },
        )

        # ------------------------------------------------------------------
        # Outputs
        # ------------------------------------------------------------------
        CfnOutput(
            self,
            "TrainingBucketName",
            value=training_bucket.bucket_name,
            description="S3 bucket for fine-tuning training data",
        )
        CfnOutput(
            self,
            "OutputBucketName",
            value=output_bucket.bucket_name,
            description="S3 bucket for fine-tuned model output",
        )
        CfnOutput(
            self,
            "FinetuningRoleArn",
            value=finetuning_role.role_arn,
            description="IAM role ARN for Bedrock fine-tuning jobs",
        )
