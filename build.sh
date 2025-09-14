#!/bin/bash
set -e

echo "Zipping Lambda functions..."

# Create Lambda Create ZIP
cd lambda_create
zip -r ../lambda_create.zip .
cd ..

# Create Lambda Redirect ZIP
cd lambda_redirect
zip -r ../lambda_redirect.zip .
cd ..

echo "All Lambda functions zipped successfully!"
