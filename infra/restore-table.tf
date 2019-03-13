resource "aws_dynamodb_table" "restore_table" {
  lifecycle {
    prevent_destroy = true
  }

  name         = "${local.prefix}-restore-table"
  billing_mode = "PAY_PER_REQUEST"
  tags         = "${var.tags}"

  hash_key  = "key"
  range_key = "timestamp"

  attribute {
    name = "key"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }
}
