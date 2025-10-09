
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "URLShortener"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# DynamoDB Table
resource "aws_dynamodb_table" "url_shortener" {
  name         = "${var.environment}-URLShortener"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "short_code"

  attribute {
    name = "short_code"
    type = "S"
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Enable encryption at rest
  server_side_encryption {
    enabled = true
  }

  # Enable deletion protection in production
  deletion_protection_enabled = var.environment == "prod" ? true : false

  tags = {
    Name        = "${var.environment}-URLShortener"
    Description = "DynamoDB table for URL shortener"
  }
}

# CloudWatch Log Group for monitoring
resource "aws_cloudwatch_log_group" "url_shortener_logs" {
  name              = "/aws/lambda/url-shortener"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.environment}-URLShortener-Logs"
  }
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "url_shortener_dashboard" {
  dashboard_name = "${var.environment}-URLShortener-Dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", aws_dynamodb_table.url_shortener.name],
            [".", "ConsumedWriteCapacityUnits", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "DynamoDB Capacity Usage"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/DynamoDB", "ItemCount", "TableName", aws_dynamodb_table.url_shortener.name]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Total URL Count"
        }
      }
    ]
  })

  tags = {
    Name = "${var.environment}-URLShortener-Dashboard"
  }
}
