#!/bin/bash
# Package Lambda deployment package

set -e

cd backend

# Create package directory
rm -rf package
mkdir package

# Install dependencies
pip install -r requirements.txt -t package/

# Copy source code
cp -r src/* package/

# Create zip
cd package
zip -r ../lambda-package.zip .
cd ..

echo "Lambda package created: lambda-package.zip"
