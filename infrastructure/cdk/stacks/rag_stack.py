"""RAG infrastructure stack with Bedrock Knowledge Base and OpenSearch Serverless.

Deploys an S3 document bucket, an OpenSearch Serverless (AOSS) collection
for vector storage, and a Bedrock Knowledge Base with an S3 data source
using Titan Embed Text v2 for embeddings.
"""

from __future__ import annotations

import json
from typing import Any

import aws_cdk as cdk
from aws_cdk import (
    RemovalPolicy,
    Stack,
    CfnOutput,
    Tags,
    aws_bedrock as bedrock,
    aws_iam as iam,
    aws_opensearchserverless as aoss,
    aws_s3 as s3,
)
from constructs import Construct


class BedrockRagStack(Stack):
    """RAG infrastructure stack with Bedrock Knowledge Base.

    Resources created:
        - S3 bucket for document storage (versioned, encrypted).
        - OpenSearch Serverless collection and access/security policies.
        - IAM role for Bedrock KB to access S3 and AOSS.
        - Bedrock Knowledge Base (CfnKnowledgeBase).
        - Bedrock Data Source (CfnDataSource) pointing to the S3 bucket.
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
        collection_name = f"bedrock-rag-{env_name}"

        # ------------------------------------------------------------------
        # S3 bucket for document storage
        # ------------------------------------------------------------------
        docs_bucket = s3.Bucket(
            self,
            "DocumentsBucket",
            bucket_name=f"bedrock-rag-docs-{env_name}-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=removal,
            auto_delete_objects=(env_name == "dev"),
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
        )

        # ------------------------------------------------------------------
        # IAM role for Bedrock Knowledge Base
        # ------------------------------------------------------------------
        kb_role = iam.Role(
            self,
            "KnowledgeBaseRole",
            role_name=f"bedrock-kb-role-{env_name}",
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
        # OpenSearch Serverless -- encryption policy
        # ------------------------------------------------------------------
        encryption_policy = aoss.CfnSecurityPolicy(
            self,
            "AOSSEncryptionPolicy",
            name=f"bedrock-rag-enc-{env_name}",
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

        # ------------------------------------------------------------------
        # OpenSearch Serverless -- network policy (public for simplicity)
        # ------------------------------------------------------------------
        network_policy = aoss.CfnSecurityPolicy(
            self,
            "AOSSNetworkPolicy",
            name=f"bedrock-rag-net-{env_name}",
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

        # ------------------------------------------------------------------
        # OpenSearch Serverless -- data access policy
        # ------------------------------------------------------------------
        data_access_policy = aoss.CfnAccessPolicy(
            self,
            "AOSSDataAccessPolicy",
            name=f"bedrock-rag-dap-{env_name}",
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

        # ------------------------------------------------------------------
        # OpenSearch Serverless collection
        # ------------------------------------------------------------------
        collection = aoss.CfnCollection(
            self,
            "AOSSCollection",
            name=collection_name,
            description=f"Vector store for Bedrock RAG ({env_name})",
            type="VECTORSEARCH",
        )
        collection.add_dependency(encryption_policy)
        collection.add_dependency(network_policy)
        collection.add_dependency(data_access_policy)

        # ------------------------------------------------------------------
        # Bedrock Knowledge Base (L1 construct)
        # ------------------------------------------------------------------
        index_name = f"bedrock-rag-index-{env_name}"

        knowledge_base = bedrock.CfnKnowledgeBase(
            self,
            "KnowledgeBase",
            name=f"bedrock-rag-kb-{env_name}",
            description=f"RAG knowledge base for {env_name}",
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

        # ------------------------------------------------------------------
        # Bedrock Data Source (S3)
        # ------------------------------------------------------------------
        data_source = bedrock.CfnDataSource(
            self,
            "DataSource",
            name=f"bedrock-rag-s3-source-{env_name}",
            knowledge_base_id=knowledge_base.attr_knowledge_base_id,
            data_source_configuration=bedrock.CfnDataSource.DataSourceConfigurationProperty(
                type="S3",
                s3_configuration=bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=docs_bucket.bucket_arn,
                ),
            ),
        )

        # ------------------------------------------------------------------
        # Outputs
        # ------------------------------------------------------------------
        CfnOutput(
            self,
            "KnowledgeBaseId",
            value=knowledge_base.attr_knowledge_base_id,
            description="Bedrock Knowledge Base ID",
        )
        CfnOutput(
            self,
            "DocumentsBucketName",
            value=docs_bucket.bucket_name,
            description="S3 bucket for RAG documents",
        )
        CfnOutput(
            self,
            "AOSSCollectionEndpoint",
            value=collection.attr_collection_endpoint,
            description="OpenSearch Serverless collection endpoint",
        )
