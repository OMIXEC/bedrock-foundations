"""Multimodal RAG stack with Bedrock Knowledge Base and document processing.

Deploys an S3 bucket for multimodal documents (PDFs, images), a Bedrock
Knowledge Base configured with a multimodal parsing strategy, a Lambda
for document ingestion, and a DynamoDB table for document metadata.
"""

from __future__ import annotations

import json
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
    aws_opensearchserverless as aoss,
    aws_s3 as s3,
)
from constructs import Construct

_LAMBDAS_DIR = str(Path(__file__).resolve().parent.parent.parent / "lambdas")


class BedrockMultimodalRagStack(Stack):
    """Multimodal RAG infrastructure stack.

    Resources created:
        - S3 bucket for multimodal documents.
        - DynamoDB table for document metadata.
        - OpenSearch Serverless collection for vector storage.
        - Bedrock Knowledge Base with multimodal parsing strategy.
        - Lambda function for document processing/ingestion.
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
        collection_name = f"bedrock-mm-rag-{env_name}"

        # ------------------------------------------------------------------
        # S3 bucket for multimodal documents (PDFs, images)
        # ------------------------------------------------------------------
        docs_bucket = s3.Bucket(
            self,
            "MultimodalDocsBucket",
            bucket_name=f"bedrock-mm-rag-docs-{env_name}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=removal,
            auto_delete_objects=(env_name == "dev"),
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
        )

        # ------------------------------------------------------------------
        # DynamoDB table for document metadata
        # ------------------------------------------------------------------
        metadata_table = dynamodb.Table(
            self,
            "DocumentMetadataTable",
            table_name=f"bedrock-mm-rag-metadata-{env_name}",
            partition_key=dynamodb.Attribute(
                name="documentId",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="uploadTimestamp",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal,
        )

        # ------------------------------------------------------------------
        # IAM role for Bedrock Knowledge Base
        # ------------------------------------------------------------------
        kb_role = iam.Role(
            self,
            "MultimodalKBRole",
            role_name=f"bedrock-mm-kb-role-{env_name}",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            inline_policies={
                "S3Access": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["s3:GetObject", "s3:ListBucket"],
                            resources=[
                                docs_bucket.bucket_arn,
                                docs_bucket.arn_for_objects("*"),
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                    ]
                ),
                "BedrockAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["bedrock:InvokeModel"],
                            resources=[
                                f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0",
                                f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                    ]
                ),
                "AOSSAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["aoss:APIAccessAll"],
                            resources=[
                                f"arn:aws:aoss:{self.region}:{self.account}:collection/*",
                            ],
                            effect=iam.Effect.ALLOW,
                        ),
                    ]
                ),
            },
        )

        # ------------------------------------------------------------------
        # OpenSearch Serverless policies and collection
        # ------------------------------------------------------------------
        encryption_policy = aoss.CfnSecurityPolicy(
            self,
            "AOSSEncPolicy",
            name=f"bedrock-mm-enc-{env_name}",
            type="encryption",
            policy=json.dumps(
                {
                    "Rules": [
                        {
                            "ResourceType": "collection",
                            "Resource": [f"collection/{collection_name}"],
                        }
                    ],
                    "AWSOwnedKey": True,
                }
            ),
        )

        network_policy = aoss.CfnSecurityPolicy(
            self,
            "AOSSNetPolicy",
            name=f"bedrock-mm-net-{env_name}",
            type="network",
            policy=json.dumps(
                [
                    {
                        "Rules": [
                            {
                                "ResourceType": "collection",
                                "Resource": [f"collection/{collection_name}"],
                            },
                            {
                                "ResourceType": "dashboard",
                                "Resource": [f"collection/{collection_name}"],
                            },
                        ],
                        "AllowFromPublic": True,
                    }
                ]
            ),
        )

        data_access_policy = aoss.CfnAccessPolicy(
            self,
            "AOSSDataPolicy",
            name=f"bedrock-mm-dap-{env_name}",
            type="data",
            policy=json.dumps(
                [
                    {
                        "Rules": [
                            {
                                "ResourceType": "index",
                                "Resource": [f"index/{collection_name}/*"],
                                "Permission": [
                                    "aoss:CreateIndex",
                                    "aoss:UpdateIndex",
                                    "aoss:DescribeIndex",
                                    "aoss:ReadDocument",
                                    "aoss:WriteDocument",
                                ],
                            },
                            {
                                "ResourceType": "collection",
                                "Resource": [f"collection/{collection_name}"],
                                "Permission": [
                                    "aoss:CreateCollectionItems",
                                    "aoss:DescribeCollectionItems",
                                    "aoss:UpdateCollectionItems",
                                ],
                            },
                        ],
                        "Principal": [kb_role.role_arn],
                    }
                ]
            ),
        )

        collection = aoss.CfnCollection(
            self,
            "AOSSCollection",
            name=collection_name,
            description=f"Vector store for multimodal RAG ({env_name})",
            type="VECTORSEARCH",
        )
        collection.add_dependency(encryption_policy)
        collection.add_dependency(network_policy)
        collection.add_dependency(data_access_policy)

        # ------------------------------------------------------------------
        # Bedrock Knowledge Base with multimodal parsing strategy
        # ------------------------------------------------------------------
        index_name = f"bedrock-mm-rag-index-{env_name}"

        knowledge_base = bedrock.CfnKnowledgeBase(
            self,
            "MultimodalKnowledgeBase",
            name=f"bedrock-mm-rag-kb-{env_name}",
            description=f"Multimodal RAG knowledge base for {env_name}",
            role_arn=kb_role.role_arn,
            knowledge_base_configuration=bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
                type="VECTOR",
                vector_knowledge_base_configuration=bedrock.CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
                    embedding_model_arn=f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0",
                ),
            ),
            storage_configuration=bedrock.CfnKnowledgeBase.StorageConfigurationProperty(
                type="OPENSEARCH_SERVERLESS",
                opensearch_serverless_configuration=bedrock.CfnKnowledgeBase.OpenSearchServerlessConfigurationProperty(
                    collection_arn=collection.attr_arn,
                    vector_index_name=index_name,
                    field_mapping=bedrock.CfnKnowledgeBase.OpenSearchServerlessFieldMappingProperty(
                        vector_field="embedding",
                        text_field="text",
                        metadata_field="metadata",
                    ),
                ),
            ),
        )

        # Data source with multimodal parsing strategy
        data_source = bedrock.CfnDataSource(
            self,
            "MultimodalDataSource",
            name=f"bedrock-mm-rag-s3-source-{env_name}",
            knowledge_base_id=knowledge_base.attr_knowledge_base_id,
            data_source_configuration=bedrock.CfnDataSource.DataSourceConfigurationProperty(
                type="S3",
                s3_configuration=bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=docs_bucket.bucket_arn,
                ),
            ),
            vector_ingestion_configuration=bedrock.CfnDataSource.VectorIngestionConfigurationProperty(
                chunking_configuration=bedrock.CfnDataSource.ChunkingConfigurationProperty(
                    chunking_strategy="FIXED_SIZE",
                    fixed_size_chunking_configuration=bedrock.CfnDataSource.FixedSizeChunkingConfigurationProperty(
                        max_tokens=512,
                        overlap_percentage=20,
                    ),
                ),
                parsing_configuration=bedrock.CfnDataSource.ParsingConfigurationProperty(
                    parsing_strategy="BEDROCK_FOUNDATION_MODEL",
                    bedrock_foundation_model_configuration=bedrock.CfnDataSource.BedrockFoundationModelConfigurationProperty(
                        model_arn=f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-sonnet-4-20250514-v1:0",
                        parsing_prompt=bedrock.CfnDataSource.ParsingPromptProperty(
                            parsing_prompt_text=(
                                "Extract all text, tables, and descriptions of images "
                                "from this document. For images, describe the visual "
                                "content in detail. Preserve the document structure."
                            ),
                        ),
                    ),
                ),
            ),
        )

        # ------------------------------------------------------------------
        # Lambda function for document processing / ingestion trigger
        # ------------------------------------------------------------------
        ingestion_role = iam.Role(
            self,
            "IngestionLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )
        ingestion_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:ListBucket"],
                resources=[
                    docs_bucket.bucket_arn,
                    docs_bucket.arn_for_objects("*"),
                ],
                effect=iam.Effect.ALLOW,
            )
        )
        ingestion_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:GetItem",
                ],
                resources=[metadata_table.table_arn],
                effect=iam.Effect.ALLOW,
            )
        )
        ingestion_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:StartIngestionJob"],
                resources=[
                    f"arn:aws:bedrock:{self.region}:{self.account}:knowledge-base/*",
                ],
                effect=iam.Effect.ALLOW,
            )
        )

        ingestion_fn = _lambda.Function(
            self,
            "IngestionFunction",
            function_name=f"bedrock-mm-rag-ingestion-{env_name}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="document_ingestion.handler",
            code=_lambda.Code.from_asset(
                os.path.join(_LAMBDAS_DIR, "document_ingestion")
            ),
            memory_size=256,
            timeout=Duration.seconds(60),
            role=ingestion_role,
            environment={
                "ENV": env_name,
                "KNOWLEDGE_BASE_ID": knowledge_base.attr_knowledge_base_id,
                "DATA_SOURCE_ID": data_source.attr_data_source_id,
                "METADATA_TABLE": metadata_table.table_name,
                "DOCS_BUCKET": docs_bucket.bucket_name,
            },
        )

        # ------------------------------------------------------------------
        # Outputs
        # ------------------------------------------------------------------
        CfnOutput(
            self,
            "MultimodalKnowledgeBaseId",
            value=knowledge_base.attr_knowledge_base_id,
            description="Multimodal Bedrock Knowledge Base ID",
        )
        CfnOutput(
            self,
            "MultimodalDocsBucketName",
            value=docs_bucket.bucket_name,
            description="S3 bucket for multimodal documents",
        )
        CfnOutput(
            self,
            "MetadataTableName",
            value=metadata_table.table_name,
            description="DynamoDB table for document metadata",
        )
        CfnOutput(
            self,
            "AOSSCollectionEndpoint",
            value=collection.attr_collection_endpoint,
            description="OpenSearch Serverless collection endpoint",
        )
