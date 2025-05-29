"""Tests for the update-rss-feed service."""

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.update_rss_feed.generate_rss import (
    NoS3CredentialsError,
    S3AccessError,
    generate_rss_feed_content,
    get_s3_client,
    list_podcast_files,
    save_rss_feed_locally,
    update_rss_feed,
    upload_rss_feed,
)


def test_module_imports():
    """Test that the module can be imported successfully."""
    from src.update_rss_feed import generate_rss

    assert generate_rss is not None


class TestS3Client:
    """Tests for S3 client creation and validation."""

    def test_missing_credentials_raises_error(self):
        """Test that missing AWS credentials raise appropriate error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(NoS3CredentialsError) as exc_info:
                get_s3_client()
            assert "Missing required environment variables" in str(exc_info.value)

    @patch("boto3.Session")
    def test_successful_s3_client_creation(self, mock_session):
        """Test successful S3 client creation with valid credentials."""
        # Mock the session and client
        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.head_bucket.return_value = {}

        env_vars = {
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
            "S3_BUCKET_NAME": "test-bucket",
            "AWS_REGION": "us-west-2",
        }

        with patch.dict(os.environ, env_vars):
            client = get_s3_client()
            assert client == mock_client
            mock_client.head_bucket.assert_called_once_with(Bucket="test-bucket")

    @patch("boto3.Session")
    def test_s3_access_denied_raises_error(self, mock_session):
        """Test that S3 access denied raises appropriate error."""
        from botocore.exceptions import ClientError

        mock_client = Mock()
        mock_session.return_value.client.return_value = mock_client

        # Mock access denied error
        error_response = {"Error": {"Code": "403", "Message": "Access Denied"}}
        mock_client.head_bucket.side_effect = ClientError(error_response, "HeadBucket")

        env_vars = {
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
            "S3_BUCKET_NAME": "test-bucket",
        }

        with patch.dict(os.environ, env_vars):
            with pytest.raises(S3AccessError) as exc_info:
                get_s3_client()
            assert "Access denied" in str(exc_info.value)


class TestListPodcastFiles:
    """Tests for listing podcast files from S3."""

    def test_list_podcast_files_success(self):
        """Test successful listing of podcast files."""
        mock_s3_client = Mock()

        # Mock paginator response
        mock_paginator = Mock()
        mock_s3_client.get_paginator.return_value = mock_paginator

        # Mock page with podcast files
        mock_page = {
            "Contents": [
                {
                    "Key": "podcasts/2025-01-15T143022.mp3",
                    "LastModified": datetime(
                        2025, 1, 15, 14, 30, 22, tzinfo=timezone.utc
                    ),
                    "Size": 1024000,
                },
                {
                    "Key": "podcasts/2025-01-16T091545.mp3",
                    "LastModified": datetime(
                        2025, 1, 16, 9, 15, 45, tzinfo=timezone.utc
                    ),
                    "Size": 2048000,
                },
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        with patch.dict(os.environ, {"S3_BUCKET_NAME": "test-bucket"}):
            files = list_podcast_files(mock_s3_client)

        assert len(files) == 2
        assert files[0]["filename"] == "2025-01-16T091545.mp3"  # Newest first
        assert files[1]["filename"] == "2025-01-15T143022.mp3"
        assert "url" in files[0]
        assert "test-bucket" in files[0]["url"]

    def test_list_podcast_files_empty_bucket(self):
        """Test listing files from empty bucket."""
        mock_s3_client = Mock()
        mock_paginator = Mock()
        mock_s3_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{}]  # Empty response

        with patch.dict(os.environ, {"S3_BUCKET_NAME": "test-bucket"}):
            files = list_podcast_files(mock_s3_client)

        assert files == []

    def test_list_podcast_files_filters_non_audio(self):
        """Test that non-audio files are filtered out."""
        mock_s3_client = Mock()
        mock_paginator = Mock()
        mock_s3_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "Contents": [
                {
                    "Key": "podcasts/episode1.mp3",
                    "LastModified": datetime.now(timezone.utc),
                    "Size": 1024000,
                },
                {
                    "Key": "podcasts/readme.txt",  # Should be filtered out
                    "LastModified": datetime.now(timezone.utc),
                    "Size": 1024,
                },
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        with patch.dict(os.environ, {"S3_BUCKET_NAME": "test-bucket"}):
            files = list_podcast_files(mock_s3_client)

        assert len(files) == 1
        assert files[0]["filename"] == "episode1.mp3"


class TestRSSGeneration:
    """Tests for RSS feed generation."""

    def test_generate_rss_feed_content_stub(self):
        """Test the stub RSS feed generation."""
        podcast_files = [
            {"filename": "episode1.mp3", "last_modified": datetime.now(timezone.utc)},
            {"filename": "episode2.mp3", "last_modified": datetime.now(timezone.utc)},
        ]

        rss_content = generate_rss_feed_content(podcast_files)

        assert "<?xml version=" in rss_content
        assert "<rss version=" in rss_content
        assert "WaffleBot Podcast" in rss_content
        assert "Found 2 episodes" in rss_content
        assert "lastBuildDate" in rss_content

    def test_generate_rss_feed_content_empty_list(self):
        """Test RSS generation with empty podcast list."""
        rss_content = generate_rss_feed_content([])

        assert "<?xml version=" in rss_content
        assert "Found 0 episodes" in rss_content


class TestRSSUpload:
    """Tests for RSS feed upload to S3."""

    def test_upload_rss_feed_success(self):
        """Test successful RSS feed upload."""
        mock_s3_client = Mock()
        rss_content = "<rss>test content</rss>"

        env_vars = {"S3_BUCKET_NAME": "test-bucket", "RSS_FEED_NAME": "podcast.xml"}

        with patch.dict(os.environ, env_vars):
            upload_rss_feed(mock_s3_client, rss_content)

        mock_s3_client.put_object.assert_called_once()
        call_args = mock_s3_client.put_object.call_args
        assert call_args[1]["Bucket"] == "test-bucket"
        assert call_args[1]["Key"] == "rss/podcast.xml"
        assert call_args[1]["ContentType"] == "application/rss+xml"

    def test_upload_rss_feed_default_name(self):
        """Test RSS upload with default feed name."""
        mock_s3_client = Mock()
        rss_content = "<rss>test content</rss>"

        with patch.dict(os.environ, {"S3_BUCKET_NAME": "test-bucket"}):
            upload_rss_feed(mock_s3_client, rss_content)

        call_args = mock_s3_client.put_object.call_args
        assert call_args[1]["Key"] == "rss/podcast.xml"  # Default name


class TestLocalSave:
    """Tests for local RSS feed saving."""

    def test_save_rss_feed_locally(self):
        """Test saving RSS feed to local file."""
        rss_content = "<rss>test content</rss>"

        with tempfile.TemporaryDirectory() as temp_dir:
            rss_output_path = "src.update_rss_feed.generate_rss.RSS_OUTPUT_DIR"
            with patch(rss_output_path, Path(temp_dir)):
                with patch.dict(os.environ, {"RSS_FEED_NAME": "test.xml"}):
                    save_rss_feed_locally(rss_content)

                saved_file = Path(temp_dir) / "test.xml"
                assert saved_file.exists()
                assert saved_file.read_text(encoding="utf-8") == rss_content


class TestMainFunction:
    """Tests for the main update_rss_feed function."""

    @patch("src.update_rss_feed.generate_rss.upload_rss_feed")
    @patch("src.update_rss_feed.generate_rss.save_rss_feed_locally")
    @patch("src.update_rss_feed.generate_rss.generate_rss_feed_content")
    @patch("src.update_rss_feed.generate_rss.list_podcast_files")
    @patch("src.update_rss_feed.generate_rss.get_s3_client")
    def test_update_rss_feed_success(
        self,
        mock_get_client,
        mock_list_files,
        mock_generate_rss,
        mock_save_local,
        mock_upload,
    ):
        """Test successful RSS feed update."""
        # Setup mocks
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_list_files.return_value = [{"filename": "test.mp3"}]
        mock_generate_rss.return_value = "<rss>content</rss>"

        # Run the function
        update_rss_feed()

        # Verify all steps were called
        mock_get_client.assert_called_once()
        mock_list_files.assert_called_once_with(mock_client)
        mock_generate_rss.assert_called_once()
        mock_save_local.assert_called_once()
        mock_upload.assert_called_once()

    @patch("src.update_rss_feed.generate_rss.get_s3_client")
    def test_update_rss_feed_no_credentials(self, mock_get_client):
        """Test RSS update with missing credentials."""
        mock_get_client.side_effect = NoS3CredentialsError("Missing credentials")

        with pytest.raises(NoS3CredentialsError):
            update_rss_feed()

    @patch("src.update_rss_feed.generate_rss.list_podcast_files")
    @patch("src.update_rss_feed.generate_rss.get_s3_client")
    def test_update_rss_feed_no_files(self, mock_get_client, mock_list_files):
        """Test RSS update with no podcast files."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_list_files.return_value = []  # No files

        # Should complete without error but log warning
        update_rss_feed()

        mock_list_files.assert_called_once_with(mock_client)
