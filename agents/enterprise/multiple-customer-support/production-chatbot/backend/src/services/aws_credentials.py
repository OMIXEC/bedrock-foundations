"""AWS credentials manager with native CLI support."""

import os
from typing import Optional
import boto3


class AWSCredentialsManager:
    """Manages AWS credentials using standard boto3 credential chain.
    
    Supports:
    - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    - AWS CLI profiles (~/.aws/credentials)
    - IAM roles (EC2, ECS, Lambda)
    - SSO credentials
    """
    
    def __init__(self, profile_name: Optional[str] = None, region: Optional[str] = None):
        """Initialize credentials manager.
        
        Args:
            profile_name: AWS CLI profile name (optional)
            region: AWS region (optional, defaults to us-east-1)
        """
        self.profile_name = profile_name or os.getenv("AWS_PROFILE")
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self._session = None
    
    def get_session(self) -> boto3.Session:
        """Get boto3 session with credentials."""
        if self._session is None:
            if self.profile_name:
                self._session = boto3.Session(
                    profile_name=self.profile_name,
                    region_name=self.region
                )
            else:
                self._session = boto3.Session(region_name=self.region)
        
        return self._session
    
    def get_bedrock_client(self):
        """Get Bedrock runtime client with credentials."""
        session = self.get_session()
        return session.client("bedrock-runtime")
    
    def get_dynamodb_client(self):
        """Get DynamoDB client with credentials."""
        session = self.get_session()
        return session.client("dynamodb")
    
    def get_credentials_info(self) -> dict:
        """Get information about current credentials."""
        session = self.get_session()
        credentials = session.get_credentials()
        
        if credentials is None:
            return {"status": "no_credentials"}
        
        return {
            "status": "active",
            "access_key": credentials.access_key[:8] + "..." if credentials.access_key else None,
            "method": credentials.method if hasattr(credentials, "method") else "unknown",
            "region": self.region,
            "profile": self.profile_name
        }
