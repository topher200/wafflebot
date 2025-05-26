# ACM certificate for the custom domain (must be in us-east-1 for CloudFront)
resource "aws_acm_certificate" "podcast" {
  provider          = aws.us_east_1
  domain_name       = var.domain_name
  validation_method = "DNS"

  tags = {
    Name        = "${var.project_name}-${var.environment}-cert"
    Environment = var.environment
    Project     = var.project_name
  }

  lifecycle {
    create_before_destroy = true
  }
}

# DNS validation records for ACM certificate
resource "aws_route53_record" "podcast_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.podcast.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = var.route53_zone_id
}

# ACM certificate validation
resource "aws_acm_certificate_validation" "podcast" {
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.podcast.arn
  validation_record_fqdns = [for record in aws_route53_record.podcast_cert_validation : record.fqdn]

  timeouts {
    create = "5m"
  }
}
