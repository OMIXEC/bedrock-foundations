#!/bin/bash

# Replace this with your API name
api_name="HttpApi4328"

# Replace this with your stage name
stage_name="dev"

# Get the API endpoint
api_endpoint=$(aws apigatewayv2  get-apis --query "Items[?Name=='$api_name'].ApiEndpoint" --output text)

# Construct the "Invoke URL"
invoke_url="$api_endpoint/$stage_name"

echo "Invoke URL: $invoke_url"