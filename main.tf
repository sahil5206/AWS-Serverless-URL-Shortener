provider "aws"{
    region = "ap-south-1"
}

#DynamoDB table

resource "dynamo_db_table" "url_table" {
    name = "urlTable"
    billing_mode = "PAY_PER_REQUEST"
    hash_key = "shortId"

    attribute {
        name = "shortId"
        type = "S"
    }
}

#IAM roles

resource "aws_iam_role" "lambda_role" {
    name = "lambda_url_shortener_role"

    assure_role_policy = jsonencode({
        Version = 2012-10-17"
        Statement = [{
            Action = "sts:Asumerole"
            Effect = "Allow"
            Principal = {
                Service = "lambda.amazonaws.com"
            }
        }]
    })
}

resource "aws_iam_role_policy_attachement" "lambda_basic" {
    role = aws_iam_role.lambda_role.name
    policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachement" "lambda_dynamo" {
    role = aws_iam_role.lambda_role.name
    policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

#lambda: create shortener 

data "archieve_file" "create_zip" {
    type = "zip"
    source_dir =  ${path.module}/lambda_create"
    output_path = ${path.module}/lambda_create.zip"
}

resource "aws_lambda_function" "create_shortener" {
    fucntion_name = "createShortener"
    runtime = "python3.9"
    handleer = "main.lambda.handler"
    role = aws_iam_role.lambda_role.arn
    filename = data.archieve_file.create_zip.output_path

    environment {
        variables = {
            TABLE_NAME = aws_dynamodb_tbale.url_table.name
        }
    }
}

#lambda: redirect shortener

data "archieve_file" "redirect_zip" {
    type = "zip"
    source_dir = ${path.module}/lambda_redirect"
    output_path = "${path.module}/lambda_redirect.zip"
}

resource "aws_lambda_function" "redirect_shortener" {
    function_name = "redirectShortener"
    runtime = "python3.9"
    handler = "main.lambda_handler"
    role = aws_iam_role.lambda_role.arn
    filename = data.archieve_file.redirect_zip.output_path

    environment {
        variables = {
            TABLE_NAME = aws_dynamodb_tbale.url_table.name
        }
    }
}

#api gateway

resource "aws_api_gateway_rest_api" "api" {
    name = "UrlShortenerAPI"
}

resource "aws_api_gateway_resource" "shorten" {
    rest_api_id = aws_id_gateway_rest_api.api.id
    parent_id = aws_id_gateway_rest_api.api.root_resource_id
    path_part = "shorten"
}

resource "aws_api_gateway_method" "shorten_post" {
    rest_api_id = aws_id_gateway_rest_api.api.id
    resource_id=  aws_api_gateway_resource.shorten.id
    http_method = "POST"
    authorization = "NONE"
}

resource "aws_api_gateway_integration" "shorten_integration" {
    rest_api_id = aws_api_gateway_rest_api.api.id
    resource_id = aws_api_gateway_resource.shorten.id
    http_method = aws_api_gateway_method.shorten_post.http_method
    integration_http_method = "POST"
    type = "AWS_PROXY"
    uri = aws_lambda_function.create_shortener.invoke_arn
}

resource "aws_api_gateway_resource" "redirect" {
    rest_api_id = aws_api_gateway_rest_api.api.id
    parent_id = aws_api_gateway_rest_api.root_resource_id
    path_part = "{shortId}"
}

resource "aws_api_gateway_method" "redirect_get" {
    rest_api_id = aws_api_gateway_rest_api.api.id
    resource_id = aws_api_gateway_resource.redirect.id
    http_method = "GET"
    authorization = "NONE"
}

resource "aws_api_gateway_integration" "redirect_integration"{
    rest_api_id = aws_api_gateway_rest_api.api.id
    resource_id = aws_api_gateway_resource.redirect.id
    http_method = aws_api_gateway_method.redirect_get.http_method
    integration_http_method = "POST"
    type = "AWS_PROXY"
    uri = aws_lambda_function.redirect_shortener.invoke_arn
}

resource "aws_lambda_permission" "api_create" {
    action = "lambda: InvokeFunction"
    function_name = aws_lambda_function.create_shortener.function_name
    Principal = "apigateway.amazonaws.com"
}

resource "aws_lambda_permission" "api_redirect" {
    action = "lambda: InvokeFunction"
    function_name = aws_lambda_function.redirect_shortener.fucntion_name
    princiapl = "apigateway.amazonaws.com"
}

resource "aws_api_gateway_deployement" "deploy" {
    depends_on = [
        aws_api_gateway_integration.shorten_integration
        aws_api_gateway_integration.redirect_integration
    ]
    rest_api_id = aws_api_gateway_rest_api.api.id
    stage_name = "dev"
}

#cloudfront

resource "aws_cloudfront_distribution" "cdn" {
    enabled = true

    origin {
        domain_name = "${aws_api_gateway_rest_api.api.id}.execute-api.ap-south-1.amazonaws.com
        origin_id = "api-gw"
        origin_path = "/dev"
    }

    default_cache_behaivour {
        allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT', "POST", "PATCH", "DELETE"]
        cached_methods = ["GET", "HEAD"]
        target_origin_id = "api-gw"
        viewer_protocol_policy = "redirectto-https"

        forward_values {
            query_string = true
            headers = ["*"]
        }
    }
    viewer_certificate {
        cloudfront_default_certificate = true
    }
}