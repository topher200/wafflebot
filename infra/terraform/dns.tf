# Route53 record to point custom domain to CloudFront
resource "aws_route53_record" "podcast" {
  zone_id = var.route53_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.podcast.domain_name
    zone_id                = aws_cloudfront_distribution.podcast.hosted_zone_id
    evaluate_target_health = false
  }
}

# Optional: AAAA record for IPv6 support
resource "aws_route53_record" "podcast_ipv6" {
  zone_id = var.route53_zone_id
  name    = var.domain_name
  type    = "AAAA"

  alias {
    name                   = aws_cloudfront_distribution.podcast.domain_name
    zone_id                = aws_cloudfront_distribution.podcast.hosted_zone_id
    evaluate_target_health = false
  }
}
