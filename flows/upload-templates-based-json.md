AWS CLI/SDKs (Recommended for direct import)
The most direct way to use a JSON template is via the AWS Command Line Interface (CLI) or an AWS SDK (like Boto3 for Python) using the create-flow command. This approach allows you to pass your JSON content directly. 
Prerequisites:
Ensure you have the AWS CLI installed and configured with the necessary permissions.
Have an IAM execution role for your flow ready, which grants permissions to access other AWS services the flow uses (e.g., Lambda, S3, Bedrock models). 
Steps using AWS CLI:
Prepare your JSON file: Ensure your flow definition JSON file (e.g., flow-definition.json) is correctly formatted according to the CreateFlow request syntax documentation.
Run the CLI command: Execute the create-flow command, providing the path to your JSON file and other required parameters.
bash
aws bedrock-agent create-flow \
    --name "YourFlowName" \
    --execution-role-arn "arn:aws:iam::<account-id>:role/<bedrock-flow-role>" \
    --definition file://flow-definition.json \
    --region <your-aws-region>
Replace "YourFlowName", arn:aws:iam::<account-id>:role/<bedrock-flow-role>, and <your-aws-region> with your actual values.
Prepare the DRAFT version: After creating the flow, you need to prepare its DRAFT version so it can be tested and versioned.
bash
aws bedrock-agent prepare-flow --flow-identifier <flow-id>
You will get the <flow-id> from the output of the previous command. 
Amazon AWS Documentation
Amazon AWS Documentation
 +1
Steps using AWS SDK (Python/Boto3):
You can also use Boto3 in Python to achieve the same result programmatically. 
python
import boto3
import json

bedrock_agent_client = boto3.client('bedrock-agent', region_name='<your-aws-region>')

with open('flow-definition.json', 'r') as f:
    flow_definition = json.load(f)

response = bedrock_agent_client.create_flow(
    name='YourFlowName',
    executionRoleArn='arn:aws:iam::<account-id>:role/<bedrock-flow-role>',
    definition={
        'nodes': flow_definition['nodes'],
        'connections': flow_definition['connections']
    }
)

print(response)
After creation, the flow will be available in the Amazon Bedrock console, where you can further test, create versions, and deploy it. 
