output "api_gateway_invoke_url" {
  value = aws_api_gateway_stage.dev.invoke_url
  description = "Direct API Gateway URL - USE THIS for your URL shortener"
}

output "cloudfront_url" {
  value = aws_cloudfront_distribution.cdn.domain_name
  description = "CloudFront URL (currently has 403 error on root path)"
}

output "working_endpoints" {
  value = {
    create_short_url = "${aws_api_gateway_stage.dev.invoke_url}/shorten"
    redirect_url = "${aws_api_gateway_stage.dev.invoke_url}/{shortId}"
    frontend_file = "url-shortener.html"
  }
  description = "Working endpoints for the URL shortener service"
}
