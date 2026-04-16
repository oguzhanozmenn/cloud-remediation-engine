provider "aws" {
  access_key                  = "test"
  secret_key                  = "test"
  region                      = "eu-central-1"
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3  = "http://localhost:4566"
    sqs = "http://localhost:4566"
  }
}

# 1. Zafiyetli (Public) S3 Kovası
resource "aws_s3_bucket" "remediation_target" {
  bucket = "sirket-ozel-veriler"
}

# 2. Güvenlik Uyarı Kuyruğu (SQS)
resource "aws_sqs_queue" "security_alerts" {
  name = "security-alerts-queue"
}

output "sqs_url" {
  value = aws_sqs_queue.security_alerts.id
}