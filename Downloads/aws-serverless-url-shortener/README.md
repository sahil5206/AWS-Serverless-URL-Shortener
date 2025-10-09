
# AWS Serverless URL Shortener

## Overview
A serverless URL shortener using Python Lambda, API Gateway, and DynamoDB. Terraform is used to provision the DynamoDB table.

## Endpoints
- POST /shorten
  - Body: { "url": "https://example.com" }
  - Response: { "short_url": "https://<api-domain>/<shortCode>" }

- GET /{shortCode}
  - Redirects to the original URL.

## Deployment
1. Provision DynamoDB using Terraform:
   ```bash
   cd terraform
   terraform init
   terraform apply
   ```
2. Deploy Lambda functions using AWS SAM:
   ```bash
   sam build
   sam deploy --guided
   ```
