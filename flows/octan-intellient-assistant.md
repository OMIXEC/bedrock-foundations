Project Overview: "Octan" Intelligent Assistant Flow
This workflow uses Amazon Bedrock Flows to route user queries. We have enhanced the "Generic" vs. "Octan" split to include a Lambda-backed "Transaction" path, fully instrumented with OpenTelemetry.
Logic:
Input: User asks a question.
Classifier (Prompt Node): Decides if the intent is:
Octan: Internal company info (routes to Knowledge Base).
Transaction: Operational task (routes to Lambda).
Generic: General knowledge (routes to LLM).
Router (Condition Node): Directs the traffic.
Processors:
KB Node: Searches "Octan" documentation.
Lambda Node: Executes a transaction (with OpenTelemetry tracing).
Prompt Node: Generates a generic answer in JSON format.
Output: Returns the final response.

1. Lambda Function (With OpenTelemetry)
This Python script is the "Transaction" handler. It uses the AWS Distro for OpenTelemetry (ADOT) via a Lambda Layer for auto-instrumentation.
File: transaction_handler.py
Python
import json
import logging
import os

# OpenTelemetry is auto-injected via the AWS ADOT Layer, 
# but we can import it to add custom spans if needed.
from opentelemetry import trace

logger = logging.getLogger()
logger.setLevel(logging.INFO)
tracer = trace.get_tracer(__name__)

def lambda_handler(event, context):
    """
    Handles 'Transaction' requests from Bedrock Flow.
    """
    # Start a custom span for business logic tracking
    with tracer.start_as_current_span("process_transaction"):
        
        # Bedrock Flow passes input in the 'node.inputs' structure
        logger.info("Received event: %s", json.dumps(event))
        
        try:
            # Extract user input (assuming single input connected)
            user_input = event.get('node', {}).get('inputs', [])[0].get('value', 'unknown')
            
            logger.info(f"Processing transaction for: {user_input}")
            
            # Mock transaction logic
            result = {
                "status": "success",
                "transaction_id": "TXN-999888",
                "message": f"Processed transaction for: {user_input}",
                "trace_id": os.environ.get('_X_AMZN_TRACE_ID') # Return trace ID for visibility
            }
            
            return {
                "messageVersion": "1.0",
                "response": {
                    "actionGroup": "transaction",
                    "function": "process",
                    "functionResponse": {
                        "responseBody": {
                            "TEXT": {
                                "body": json.dumps(result)
                            }
                        }
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            with tracer.start_as_current_span("error_handling"):
                return {
                    "messageVersion": "1.0",
                    "response": {
                        "functionResponse": {
                            "responseBody": {
                                "TEXT": {"body": f"Error processing transaction: {str(e)}"}
                            }
                        }
                    }
                }

2. Bedrock Flow Definition (JSON)
This is the "full bedrock json file" you requested. It defines the visual workflow structure. You can save this as flow-definition.json.
Note: You must replace ARN_OF_YOUR_LAMBDA, ARN_OF_YOUR_KB, and MODEL_ARN (e.g., Claude 3 Sonnet) with your actual ARNs.
File: flow-definition.json
JSON
{
  "name": "OctanSmartAssistantFlow",
  "description": "Routes queries between Octan KB, Transaction Lambda, and Generic LLM",
  "executionRoleArn": "arn:aws:iam::YOUR_ACCOUNT_ID:role/BedrockFlowExecutionRole",
  "definition": {
    "nodes": [
      {
        "name": "FlowInput",
        "type": "Input",
        "outputs": [
          {
            "name": "document",
            "type": "String"
          }
        ]
      },
      {
        "name": "ClassifierPrompt",
        "type": "Prompt",
        "configuration": {
          "prompt": {
            "sourceConfiguration": {
              "inline": {
                "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
                "templateType": "TEXT",
                "inferenceConfiguration": {
                  "text": {
                    "temperature": 0.0
                  }
                },
                "templateConfiguration": {
                  "text": {
                    "text": "Classify the user input into one of: Octan (if the user is asking about Octan company projects), Transaction (if the user wants to perform an action or transaction), or Generic (anything else). Answer ONLY with the category name."
                  }
                }
              }
            }
          }
        },
        "inputs": [
          {
            "name": "input",
            "type": "String",
            "expression": "$.data"
          }
        ],
        "outputs": [
          {
            "name": "modelOutput",
            "type": "String"
          }
        ]
      },
      {
        "name": "RouteCondition",
        "type": "Condition",
        "inputs": [
          {
            "name": "category",
            "type": "String",
            "expression": "$.data"
          }
        ],
        "conditions": [
          {
            "name": "IsOctan",
            "expression": "Equals(category, 'Octan')"
          },
          {
            "name": "IsTransaction",
            "expression": "Equals(category, 'Transaction')"
          },
          {
            "name": "IsGeneric",
            "expression": "Equals(category, 'Generic')"
          }
        ]
      },
      {
        "name": "OctanKnowledgeBase",
        "type": "KnowledgeBase",
        "configuration": {
          "knowledgeBase": {
            "knowledgeBaseId": "YOUR_KB_ID",
            "modelId": "anthropic.claude-3-sonnet-20240229-v1:0"
          }
        },
        "inputs": [
          {
            "name": "retrievalQuery",
            "type": "String",
            "expression": "$.data"
          }
        ],
        "outputs": [
          {
            "name": "retrievalResult",
            "type": "String"
          }
        ]
      },
      {
        "name": "TransactionLambda",
        "type": "LambdaFunction",
        "configuration": {
          "lambdaFunction": {
            "lambdaArn": "arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:TransactionHandler"
          }
        },
        "inputs": [
          {
            "name": "input",
            "type": "String",
            "expression": "$.data"
          }
        ],
        "outputs": [
          {
            "name": "functionResult",
            "type": "String"
          }
        ]
      },
      {
        "name": "GenericPrompt",
        "type": "Prompt",
        "configuration": {
          "prompt": {
            "sourceConfiguration": {
              "inline": {
                "modelId": "anthropic.claude-3-sonnet-20240229-v1:0",
                "templateType": "TEXT",
                "templateConfiguration": {
                  "text": {
                    "text": "Answer the user question in a single and brief sentence into a JSON. Only answer with a JSON."
                  }
                }
              }
            }
          }
        },
        "inputs": [
          {
            "name": "input",
            "type": "String",
            "expression": "$.data"
          }
        ],
        "outputs": [
          {
            "name": "modelOutput",
            "type": "String"
          }
        ]
      },
      {
        "name": "FlowOutput",
        "type": "Output",
        "inputs": [
          {
            "name": "document",
            "type": "String",
            "expression": "$.data"
          }
        ]
      }
    ],
    "connections": [
      {
        "type": "Data",
        "source": "FlowInput",
        "target": "ClassifierPrompt",
        "configuration": {
          "data": {
            "sourceOutput": "document",
            "targetInput": "input"
          }
        }
      },
      {
        "type": "Data",
        "source": "ClassifierPrompt",
        "target": "RouteCondition",
        "configuration": {
          "data": {
            "sourceOutput": "modelOutput",
            "targetInput": "category"
          }
        }
      },
      {
        "type": "Conditional",
        "source": "RouteCondition",
        "target": "OctanKnowledgeBase",
        "configuration": {
          "conditional": {
            "condition": "IsOctan"
          }
        }
      },
      {
        "type": "Data",
        "source": "FlowInput",
        "target": "OctanKnowledgeBase",
        "configuration": {
          "data": {
            "sourceOutput": "document",
            "targetInput": "retrievalQuery"
          }
        }
      },
      {
        "type": "Conditional",
        "source": "RouteCondition",
        "target": "TransactionLambda",
        "configuration": {
          "conditional": {
            "condition": "IsTransaction"
          }
        }
      },
      {
        "type": "Data",
        "source": "FlowInput",
        "target": "TransactionLambda",
        "configuration": {
          "data": {
            "sourceOutput": "document",
            "targetInput": "input"
          }
        }
      },
      {
        "type": "Conditional",
        "source": "RouteCondition",
        "target": "GenericPrompt",
        "configuration": {
          "conditional": {
            "condition": "IsGeneric"
          }
        }
      },
      {
        "type": "Data",
        "source": "FlowInput",
        "target": "GenericPrompt",
        "configuration": {
          "data": {
            "sourceOutput": "document",
            "targetInput": "input"
          }
        }
      },
      {
        "type": "Data",
        "source": "OctanKnowledgeBase",
        "target": "FlowOutput",
        "configuration": {
          "data": {
            "sourceOutput": "retrievalResult",
            "targetInput": "document"
          }
        }
      },
      {
        "type": "Data",
        "source": "TransactionLambda",
        "target": "FlowOutput",
        "configuration": {
          "data": {
            "sourceOutput": "functionResult",
            "targetInput": "document"
          }
        }
      },
      {
        "type": "Data",
        "source": "GenericPrompt",
        "target": "FlowOutput",
        "configuration": {
          "data": {
            "sourceOutput": "modelOutput",
            "targetInput": "document"
          }
        }
      }
    ]
  }
}

3. CDK Import & Deployment
Use this CDK code to deploy the infrastructure. It creates the Lambda with the ADOT (OpenTelemetry) layer and creates the Bedrock Flow using the JSON definition.
File: app.py (Python CDK)
Python
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_bedrock as bedrock,
    CfnOutput
)
from constructs import Construct
import json

class BedrockFlowStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # 1. Lambda Role
        lambda_role = iam.Role(self, "LambdaExecRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSXRayDaemonWriteAccess") # Required for ADOT/X-Ray
            ]
        )

        # 2. ADOT Layer (AWS Distro for OpenTelemetry) for Python
        # Check https://aws-otel.github.io/docs/getting-started/lambda for latest ARNs per region
        adot_layer_arn = "arn:aws:lambda:us-east-1:901920570463:layer:aws-otel-python-amd64-ver-1-24-0:1"
        adot_layer = _lambda.LayerVersion.from_layer_version_arn(self, "AdotLayer", adot_layer_arn)

        # 3. Transaction Lambda Function
        txn_function = _lambda.Function(self, "TransactionHandler",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="transaction_handler.lambda_handler",
            code=_lambda.Code.from_asset("lambda"), # Folder containing transaction_handler.py
            role=lambda_role,
            layers=[adot_layer],
            environment={
                "AWS_LAMBDA_EXEC_WRAPPER": "/opt/otel-instrument", # Auto-instrumentation magic
                "OPENTELEMETRY_COLLECTOR_CONFIG_FILE": "/var/task/collector.yaml" # Optional custom config
            },
            tracing=_lambda.Tracing.ACTIVE
        )

        # 4. Bedrock Flow Execution Role
        flow_role = iam.Role(self, "FlowExecRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com")
        )
        # Grant Flow permission to invoke Lambda and Models
        flow_role.add_to_policy(iam.PolicyStatement(
            actions=["lambda:InvokeFunction"],
            resources=[txn_function.function_arn]
        ))
        flow_role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel", "bedrock:Retrieve"],
            resources=["*"] # Restrict this in production
        ))

        # 5. Import and Update JSON Definition
        with open("flow-definition.json", "r") as f:
            flow_def_json = json.load(f)

        # Dynamically inject the created Lambda ARN into the JSON definition
        for node in flow_def_json['definition']['nodes']:
            if node['name'] == 'TransactionLambda':
                node['configuration']['lambdaFunction']['lambdaArn'] = txn_function.function_arn

        # 6. Create Bedrock Flow
        cfn_flow = bedrock.CfnFlow(self, "OctanFlow",
            name="OctanSmartAssistantFlow",
            execution_role_arn=flow_role.role_arn,
            definition=flow_def_json['definition']
        )

        CfnOutput(self, "FlowIdentifier", value=cfn_flow.attr_flow_id)
        CfnOutput(self, "FlowArn", value=cfn_flow.attr_flow_arn)

4. AWS CLI Upload Commands
If you prefer to skip CDK and upload the JSON definition directly via AWS CLI, follow these steps:
Prepare the file: Ensure flow-definition.json has the correct executionRoleArn and lambdaArn (you must create these resources first if not using CDK).
Upload Command:
Bash
aws bedrock-agent create-flow \
    --name "OctanSmartAssistantFlow" \
    --description "Flow from video walkthrough with OTEL Lambda" \
    --execution-role-arn "arn:aws:iam::123456789012:role/service-role/BedrockFlowsRole" \
    --definition file://flow-definition.json \
    --region us-east-1

Version and Alias (as shown in video):
Bash

# Create a version
aws bedrock-agent prepare-flow --flow-identifier FLOW_ID
aws bedrock-agent create-flow-version --flow-identifier FLOW_ID

# Create an Alias
aws bedrock-agent create-flow-alias \
    --flow-identifier FLOW_ID \
    --name "ProdAlias" \
    --routing-configuration "[{\"flowVersion\": \"1\"}]"



Demo - Amazon Bedrock Prompt Flows | Amazon Web Services
Amazon Web Services · 23K‏ צפיות




