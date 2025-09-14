variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project name prefix for resource naming"
  type        = string
  default     = "serverless-url-shortener"
}

variable "table_name" {
  description = "DynamoDB table name"
  type        = string
  default     = "url_shortener_table"
}

variable "api_stage" {
  description = "Stage name for API Gateway deployment"
  type        = string
  default     = "prod"
}
