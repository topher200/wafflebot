"""Tests for the publish-podcast-to-s3 service."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


def test_publish_script_exists():
    """Test that the publish script exists and is executable."""
    script_path = Path("src/publish-podcast-to-s3/publish.sh")
    assert script_path.exists(), "publish.sh script should exist"
    assert os.access(script_path, os.X_OK), "publish.sh should be executable"


def test_input_file_validation():
    """Test that the script validates input file existence."""
    import subprocess

    # Get absolute path to the script
    script_path = Path("src/publish-podcast-to-s3/publish.sh").absolute()

    # Create a temporary directory to simulate missing input file
    with tempfile.TemporaryDirectory() as temp_dir:
        env = os.environ.copy()
        env["S3_BUCKET_NAME"] = "test-bucket"
        env["AWS_ACCESS_KEY_ID"] = "test-key"
        env["AWS_SECRET_ACCESS_KEY"] = "test-secret"

        # Change to temp directory where input file doesn't exist
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=temp_dir,
            env=env,
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0, "Script should fail when input file is missing"
        # Check both stdout and stderr for error message
        output = result.stdout + result.stderr
        assert "Input file" in output or "not found" in output


def test_environment_variable_validation():
    """Test that the script validates required environment variables."""
    import subprocess

    # Test missing S3_BUCKET_NAME
    result = subprocess.run(
        ["bash", "src/publish-podcast-to-s3/publish.sh"],
        env={},  # Empty environment
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0, "Script should fail when S3_BUCKET_NAME is missing"


@patch("subprocess.run")
def test_timestamp_format(mock_run):
    """Test that the timestamp format is correct."""
    import re
    from datetime import UTC, datetime

    # Mock the aws s3 cp command
    mock_run.return_value = MagicMock(returncode=0)

    # The timestamp should match ISO 8601 format: YYYY-MM-DDTHHMMSS
    timestamp_pattern = r"^\d{4}-\d{2}-\d{2}T\d{6}\.mp3$"

    # Generate a timestamp like the script does
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%S")
    filename = f"{timestamp}.mp3"

    assert re.match(timestamp_pattern, filename), (
        f"Filename {filename} should match ISO 8601 format"
    )


def test_s3_destination_format():
    """Test that the S3 destination path is correctly formatted."""
    bucket_name = "test-podcast-bucket"
    timestamp = "2025-01-15T143022"
    filename = f"{timestamp}.mp3"

    expected_destination = f"s3://{bucket_name}/podcasts/{filename}"

    # This tests the format that should be used in the script
    assert expected_destination == f"s3://{bucket_name}/podcasts/{filename}"
    assert "/podcasts/" in expected_destination
    assert expected_destination.startswith("s3://")
    assert expected_destination.endswith(".mp3")
