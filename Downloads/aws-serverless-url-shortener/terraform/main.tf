
provider "aws" {
  region = var.aws_region
}

resource "aws_dynamodb_table" "url_shortener" {
  name         = "URLShortener"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "short_code"

  attribute {
    name = "short_code"
    type = "S"
  }
}
