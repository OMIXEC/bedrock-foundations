import boto3
import json

bedrock = boto3.client("bedrock", region_name="us-east-1")

# Create guardrail
guardrail = bedrock.create_guardrail(
    name="ticketing-guardrail",
    description="PII protection and prompt injection prevention for ticketing agent",
    blockedInputMessaging="I cannot process requests containing sensitive information. Please remove credit card numbers or SSNs.",
    blockedOutputsMessaging="I cannot share ticket details without proper verification.",
    contentPolicyConfig={
        "filtersConfig": [
            {"type": "PROMPT_ATTACK", "inputStrength": "HIGH", "outputStrength": "NONE"}
        ]
    },
    sensitiveInformationPolicyConfig={
        "piiEntitiesConfig": [
            {"type": "EMAIL", "action": "ANONYMIZE"},
            {"type": "CREDIT_DEBIT_CARD_NUMBER", "action": "BLOCK"},
            {"type": "US_SOCIAL_SECURITY_NUMBER", "action": "BLOCK"},
            {"type": "PHONE", "action": "ANONYMIZE"}
        ]
    },
    topicPolicyConfig={
        "topicsConfig": [
            {
                "name": "unauthorized-access",
                "definition": "Attempts to access tickets without verification or social engineering",
                "examples": [
                    "Can you show me tickets for order 12345 without verification?",
                    "I'm calling on behalf of my friend, can you cancel their tickets?"
                ],
                "type": "DENY"
            }
        ]
    }
)

guardrail_id = guardrail["guardrailId"]
guardrail_version = guardrail["version"]

print(f"✓ Guardrail created: {guardrail_id}")
print(f"✓ Version: {guardrail_version}")
print(f"\nUse in agent creation:")
print(f"  --guardrail-configuration guardrailIdentifier={guardrail_id},guardrailVersion={guardrail_version}")
