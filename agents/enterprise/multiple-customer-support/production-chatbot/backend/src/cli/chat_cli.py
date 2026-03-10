#!/usr/bin/env python3
"""CLI tool for chatting with Bedrock using native AWS credentials."""

import argparse
import sys
from typing import Optional

from ..services.aws_credentials import AWSCredentialsManager
from ..services.bedrock_client import BedrockClient
from ..utils.config_loader import load_config


def chat_loop(bedrock_client: BedrockClient, system_prompt: str):
    """Interactive chat loop."""
    print("\n🤖 Bedrock Chat CLI")
    print("=" * 50)
    print("Type 'quit' or 'exit' to end the conversation\n")
    
    messages = []
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit"]:
                print("\nGoodbye! 👋")
                break
            
            messages.append({"role": "user", "content": user_input})
            
            print("\nAssistant: ", end="", flush=True)
            
            full_response = ""
            for chunk in bedrock_client.converse_stream(
                messages=messages,
                system_prompt=system_prompt
            ):
                print(chunk, end="", flush=True)
                full_response += chunk
            
            print("\n")
            
            messages.append({"role": "assistant", "content": full_response})
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Chat with AWS Bedrock using native credentials"
    )
    parser.add_argument(
        "--profile",
        help="AWS CLI profile name",
        default=None
    )
    parser.add_argument(
        "--region",
        help="AWS region",
        default="us-east-1"
    )
    parser.add_argument(
        "--model",
        help="Bedrock model ID",
        default="anthropic.claude-sonnet-4-5-20250929-v1:0"
    )
    parser.add_argument(
        "--config",
        help="Path to config.yaml",
        default=None
    )
    
    args = parser.parse_args()
    
    try:
        # Load config
        config = load_config(args.config)
        
        # Override with CLI args
        if args.model:
            config.bedrock.model_id = args.model
        if args.region:
            config.bedrock.region = args.region
        
        # Setup AWS credentials
        creds_manager = AWSCredentialsManager(
            profile_name=args.profile,
            region=config.bedrock.region
        )
        
        # Verify credentials
        creds_info = creds_manager.get_credentials_info()
        if creds_info["status"] != "active":
            print("❌ No AWS credentials found!")
            print("\nPlease configure credentials using one of:")
            print("  1. AWS CLI: aws configure")
            print("  2. Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
            print("  3. IAM role (if running on AWS)")
            sys.exit(1)
        
        print(f"✅ Using AWS credentials: {creds_info['method']}")
        print(f"   Region: {creds_info['region']}")
        print(f"   Model: {config.bedrock.model_id}")
        if creds_info.get("profile"):
            print(f"   Profile: {creds_info['profile']}")
        
        # Create Bedrock client
        session = creds_manager.get_session()
        bedrock_client = BedrockClient(config, boto_session=session)
        
        # Start chat loop
        chat_loop(bedrock_client, config.conversation.system_prompt)
        
    except FileNotFoundError as e:
        print(f"❌ Config file not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
