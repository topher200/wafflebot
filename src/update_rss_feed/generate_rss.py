import os
import pathlib
from datetime import datetime, timezone
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from src.utils.logging import setup_logger

logger = setup_logger(__name__)

RSS_OUTPUT_DIR = pathlib.Path("data/rss")


class NoS3CredentialsError(Exception):
    """Exception raised when AWS S3 credentials are not available."""


class S3AccessError(Exception):
    """Exception raised when S3 access fails."""


class RSSGenerationError(Exception):
    """Exception raised when RSS feed generation fails."""


def get_s3_client():
    """Create and return an S3 client using environment variables."""
    try:
        # Check for required environment variables
        required_vars = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "S3_BUCKET_NAME"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            raise NoS3CredentialsError(
                f"Missing required environment variables: {missing_vars}"
            )

        # Create S3 client
        session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            # Optional for temporary credentials
            aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )

        s3_client = session.client("s3")

        # Test credentials by listing bucket (this will fail if credentials are invalid)
        bucket_name = os.getenv("S3_BUCKET_NAME")
        s3_client.head_bucket(Bucket=bucket_name)

        logger.info(f"Successfully connected to S3 bucket: {bucket_name}")
        return s3_client

    except NoCredentialsError as e:
        raise NoS3CredentialsError(f"AWS credentials not found: {e}") from e
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "403":
            raise S3AccessError(f"Access denied to S3 bucket: {e}") from e
        elif error_code == "404":
            raise S3AccessError(f"S3 bucket not found: {e}") from e
        else:
            raise S3AccessError(f"S3 error: {e}") from e


def list_podcast_files(s3_client) -> List[Dict[str, Any]]:
    """List all podcast audio files from S3 bucket."""
    logger.info("Listing podcast files from S3...")

    bucket_name = os.getenv("S3_BUCKET_NAME")
    podcast_files = []

    try:
        # List objects in the podcasts/ prefix
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_name, Prefix="podcasts/")

        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    key = obj["Key"]
                    # Only include audio files
                    if key.endswith((".mp3", ".wav", ".m4a", ".ogg")):
                        file_info = {
                            "key": key,
                            "filename": pathlib.Path(key).name,
                            "last_modified": obj["LastModified"],
                            "size": obj["Size"],
                            "url": f"https://{bucket_name}.s3.amazonaws.com/{key}",
                        }
                        podcast_files.append(file_info)

        # Sort by last modified date (newest first)
        podcast_files.sort(key=lambda x: x["last_modified"], reverse=True)

        logger.info(f"Found {len(podcast_files)} podcast files")
        return podcast_files

    except ClientError as e:
        raise S3AccessError(f"Failed to list podcast files: {e}") from e


def generate_rss_feed_content(podcast_files: List[Dict[str, Any]]) -> str:
    """Generate RSS feed XML content from podcast files.

    This is a stub function that will be replaced with actual RSS library
    implementation.
    """
    logger.info("Generating RSS feed content...")

    # TODO: Replace this stub with actual RSS feed generation using a proper library
    # This should generate a valid RSS 2.0 feed with podcast metadata

    build_date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
    <channel>
        <title>WaffleBot Podcast</title>
        <description>Automated podcast generated from Discord voice memos</description>
        <language>en-us</language>
        <lastBuildDate>{build_date}</lastBuildDate>
        <generator>WaffleBot RSS Generator</generator>

        <!-- Podcast episodes will be added here by RSS library -->
        <!-- Stub: Found {len(podcast_files)} episodes -->

    </channel>
</rss>"""

    logger.info("RSS feed content generated (stub implementation)")
    return rss_content


def upload_rss_feed(s3_client, rss_content: str) -> None:
    """Upload the generated RSS feed to S3."""
    logger.info("Uploading RSS feed to S3...")

    bucket_name = os.getenv("S3_BUCKET_NAME")
    rss_feed_name = os.getenv("RSS_FEED_NAME", "podcast.xml")
    s3_key = f"rss/{rss_feed_name}"

    try:
        # Upload RSS feed with appropriate content type
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=rss_content.encode("utf-8"),
            ContentType="application/rss+xml",
            CacheControl="max-age=3600",  # Cache for 1 hour
        )

        rss_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
        logger.info(f"RSS feed uploaded successfully to: {rss_url}")

    except ClientError as e:
        raise S3AccessError(f"Failed to upload RSS feed: {e}") from e


def save_rss_feed_locally(rss_content: str) -> None:
    """Save the RSS feed content locally for debugging/testing."""
    logger.info("Saving RSS feed locally...")

    RSS_OUTPUT_DIR.mkdir(exist_ok=True)
    rss_feed_name = os.getenv("RSS_FEED_NAME", "podcast.xml")
    local_path = RSS_OUTPUT_DIR / rss_feed_name

    with open(local_path, "w", encoding="utf-8") as f:
        f.write(rss_content)

    logger.info(f"RSS feed saved locally to: {local_path}")


def update_rss_feed() -> None:
    """Main function to update the RSS feed."""
    logger.info("Starting RSS feed update...")

    try:
        # Step 1: Connect to S3
        s3_client = get_s3_client()

        # Step 2: List all podcast files
        podcast_files = list_podcast_files(s3_client)

        if not podcast_files:
            logger.warning("No podcast files found in S3 bucket")
            return

        # Step 3: Generate RSS feed content
        rss_content = generate_rss_feed_content(podcast_files)

        # Step 4: Save locally (for debugging)
        save_rss_feed_locally(rss_content)

        # Step 5: Upload to S3
        upload_rss_feed(s3_client, rss_content)

        logger.info("RSS feed update completed successfully!")

    except (NoS3CredentialsError, S3AccessError, RSSGenerationError) as e:
        logger.error(f"RSS feed update failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during RSS feed update: {e}")
        raise RSSGenerationError(f"RSS feed update failed: {e}") from e


if __name__ == "__main__":
    update_rss_feed()
