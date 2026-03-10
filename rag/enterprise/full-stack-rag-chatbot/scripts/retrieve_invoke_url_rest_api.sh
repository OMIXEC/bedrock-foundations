#!/bin/bash

# Specify API name
api_name="RestApi4328"

# Specify stage name
stage_name="dev"

# Specify region
region="eu-central-1"

# Get the API ID based on the API name
api_id=$(aws apigateway get-rest-apis --query "items[?name=='$api_name'].id" --output text)

# Construct the invoke URL
invoke_url="https://${api_id}.execute-api.${region}.amazonaws.com/${stage_name}"

echo "Invoke URL: $invoke_url"