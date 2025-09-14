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
    
}
