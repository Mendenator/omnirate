variable "environment" { type = string }

# Review photos + receipt uploads (P1-02: presigned URL, ≤10MB, EXIF stripped
# server-side before write — see apps/backend upload handler).
resource "aws_s3_bucket" "uploads" {
  bucket = "omnirate-${var.environment}-uploads"
}

resource "aws_s3_bucket_lifecycle_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  rule {
    id     = "expire-unlinked-uploads"
    status = "Enabled"
    expiration { days = 30 } # orphaned uploads (never attached to a review) age out
  }
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket                  = aws_s3_bucket.uploads.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# WAL-G continuous archiving target for the postgres module's PITR (P0-02).
resource "aws_s3_bucket" "postgres_wal_archive" {
  bucket = "omnirate-${var.environment}-postgres-wal"
}

resource "aws_s3_bucket_versioning" "postgres_wal_archive" {
  bucket = aws_s3_bucket.postgres_wal_archive.id
  versioning_configuration { status = "Enabled" }
}

output "uploads_bucket" {
  value = aws_s3_bucket.uploads.bucket
}

output "postgres_wal_archive_bucket" {
  value = aws_s3_bucket.postgres_wal_archive.bucket
}
