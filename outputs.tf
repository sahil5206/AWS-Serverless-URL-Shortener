output "cloudfront_domain_name" {
  description = "CloudFront domain URL to access the URL shortener"
  value       = aws_cloudfront_distribution.cdn.domain_name
}

output "api_gateway_invoke_url" {
  description = "Base API Gateway URL (before CloudFront)"
  value       = "${aws_api_gateway_deployment.deployment.invoke_url}"
}


output "dyanmodb_table" {
    description = "DynamoDB table name and data"
    value = aws_dynamodb_table.url_table.name
}