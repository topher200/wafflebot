"""End-to-end tests for the complete audio processing pipeline."""

import logging
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import pytest

from tests.e2e.utils.docker_helpers import (
    DockerComposeTestManager,
    wait_for_service_completion,
)
from tests.e2e.utils.minio_helpers import MinIOTestClient

logger = logging.getLogger(__name__)

@pytest.fixture
def dummy_podcast_file(docker_manager: DockerComposeTestManager):
    """
    This fixture creates a dummy podcast file directly in the podcast volume for
    upload tests.
    """
    full_volume_name = "wafflebot_test-podcast-audio"
    result = subprocess.run([
        "docker", "run", "--rm", "--platform", "linux/amd64",
        "-v", f"{full_volume_name}:/data",
        "alpine", "sh", "-c",
        "echo 'dummy audio content for testing' > /data/voice_memo_mix.mp3"
    ], capture_output=True, text=True)
    assert result.returncode == 0, (
        f"Failed to create dummy podcast file: {result.stderr}"
    )
    yield "/data/voice_memo_mix.mp3"

class TestFullPipeline:
    """Test the complete audio processing pipeline."""

    def test_audio_mixer_processes_test_files(
        self,
        test_audio_files: List[Dict[str, Any]],
        test_background_music: List[Dict[str, Any]],
        docker_manager: DockerComposeTestManager,
        clean_docker_environment,
    ):
        """Test that the audio mixer can process test audio files successfully."""
        logger.info("Testing audio mixer with test files...")

        # Verify test files are available
        assert len(test_audio_files) >= 2, "Need at least 2 test audio files"
        assert len(test_background_music) >= 1, "Need at least 1 background music file"

        for file_config in test_audio_files:
            assert file_config[
                "local_path"
            ].exists(), f"Test file missing: {file_config['local_path']}"

        for music_config in test_background_music:
            assert music_config[
                "local_path"
            ].exists(), f"Background music missing: {music_config['local_path']}"

        # Build the audio mixer service
        assert docker_manager.build_services(
            ["audio-mixer"]
        ), "Failed to build audio-mixer service"

        # Run the audio mixer
        result = docker_manager.run_service("audio-mixer")

        # Check that the service completed successfully
        if result.returncode != 0:
            logger.error(f"Audio mixer STDOUT: {result.stdout}")
            logger.error(f"Audio mixer STDERR: {result.stderr}")
        assert result.returncode == 0, f"Audio mixer failed: {result.stderr}"

        # Verify that output was created in the podcast volume
        volume_contents = docker_manager.get_volume_contents(
            "test-podcast-audio", "/data"
        )
        assert (
            volume_contents is not None
        ), "Could not inspect test-podcast-audio volume"

        # Look for the expected output file
        output_files = [
            line for line in volume_contents if "voice_memo_mix.mp3" in line
        ]
        assert (
            len(output_files) > 0
        ), "Expected output file voice_memo_mix.mp3 not found in volume"

        logger.info("Audio mixer test completed successfully")

    def test_publish_to_dropbox_creates_versioned_file(
        self,
        docker_manager: DockerComposeTestManager,
        clean_docker_environment,
        temp_output_dir: Path,
        dummy_podcast_file,
    ):
        """
        This test verifies that the publish script creates properly versioned files
        using a dummy audio file.
        """
        logger.info(
            "Testing publish-to-dropbox with versioned naming (using dummy file)..."
        )
        assert docker_manager.build_services([
            "publish-to-dropbox"
        ]), "Failed to build publish-to-dropbox service"
        publish_result = docker_manager.run_service("publish-to-dropbox")
        assert (
            publish_result.returncode == 0
        ), f"Publish script failed: {publish_result.stderr}"

        # Get the filenames of the files in the dropbox output volume
        filenames = docker_manager.get_volume_filenames(
            "test-dropbox-output", "/data", "*.mp3"
        )
        logger.debug(f"Dropbox output filenames: {filenames}")
        assert filenames is not None, (
            "Could not get filenames from dropbox output volume"
        )
        assert len(filenames) > 0, (
            "No MP3 files found in dropbox output volume"
        )

        # Check for versioned naming pattern:
        # starts with 4 digits, dash, then has .mp3 extension
        versioned_files = [
            f for f in filenames
            if f.startswith(("0001-", "0002-", "0003-")) and f.endswith(".mp3")
        ]
        assert len(versioned_files) > 0, (
            f"No properly versioned files found. Files: {filenames}"
        )

        logger.info("Publish script test completed successfully")

    def test_publish_to_s3_uploads_to_minio(
        self,
        docker_manager: DockerComposeTestManager,
        clean_docker_environment,
        minio_client: MinIOTestClient,
        dummy_podcast_file,
    ):
        logger.info("Testing publish-podcast-to-s3 with MinIO (using dummy file)...")
        assert docker_manager.build_services([
            "publish-podcast-to-s3"
        ]), "Failed to build publish-podcast-to-s3 service"
        publish_result = docker_manager.run_service("publish-podcast-to-s3")
        if publish_result.returncode != 0:
            logger.error(f"S3 publish STDOUT: {publish_result.stdout}")
            logger.error(f"S3 publish STDERR: {publish_result.stderr}")
        assert (
            publish_result.returncode == 0
        ), f"S3 publish script failed: {publish_result.stderr}"

        bucket_name = "test-podcast-bucket"
        objects = minio_client.list_bucket_objects(bucket_name, "podcasts/")
        assert len(objects) > 0, "No objects found in MinIO bucket"

        # Check for ISO 8601 timestamp pattern: podcasts/YYYY-MM-DDTHHMMSS.mp3
        iso_pattern = re.compile(r"^podcasts/\d{4}-\d{2}-\d{2}T\d{6}\.mp3$")
        timestamped_files = [
            obj for obj in objects if iso_pattern.match(obj)
        ]
        assert len(timestamped_files) > 0, (
            f"No properly timestamped files found. Objects: {objects}"
        )

        logger.info(
            f"S3 publish test completed successfully. Uploaded: {timestamped_files[0]}"
        )

    def test_complete_pipeline_end_to_end(
        self,
        test_audio_files: List[Dict[str, Any]],
        test_background_music: List[Dict[str, Any]],
        docker_manager: DockerComposeTestManager,
        minio_client: MinIOTestClient,
        clean_docker_environment,
    ):
        """Test the complete pipeline from audio files to published output."""
        logger.info("Running complete end-to-end pipeline test...")

        # Verify prerequisites
        assert (
            len(test_audio_files) >= 2
        ), "Need at least 2 test audio files for complete test"
        assert len(test_background_music) >= 1, "Need at least 1 background music file"

        # Build all required services
        services_to_build = ["audio-mixer", "publish-to-dropbox"]
        assert docker_manager.build_services(
            services_to_build
        ), "Failed to build required services"

        # Step 1: Run audio mixer
        logger.info("Step 1: Running audio mixer...")
        mixer_success = wait_for_service_completion(docker_manager, "audio-mixer")
        assert mixer_success, "Audio mixer step failed"

        # Verify intermediate output exists
        podcast_volume_contents = docker_manager.get_volume_contents(
            "test-podcast-audio", "/data"
        )
        assert (
            podcast_volume_contents is not None
        ), "Could not inspect podcast volume after mixer"

        mixed_files = [
            line for line in podcast_volume_contents if "voice_memo_mix.mp3" in line
        ]
        assert len(mixed_files) > 0, "Mixed audio file not created by audio mixer"

        # Step 2: Run both publish services
        logger.info("Step 2: Running Dropbox publish...")
        dropbox_success = wait_for_service_completion(
            docker_manager, "publish-to-dropbox"
        )
        assert dropbox_success, "Dropbox publish step failed"

        logger.info("Step 3: Running S3 publish...")
        s3_success = wait_for_service_completion(
            docker_manager, "publish-podcast-to-s3"
        )
        assert s3_success, "S3 publish step failed"

        # Verify Dropbox output
        dropbox_filenames = docker_manager.get_volume_filenames(
            "test-dropbox-output", "/data", "*.mp3"
        )
        assert dropbox_filenames is not None, (
            "Could not get filenames from dropbox output volume"
        )
        assert len(dropbox_filenames) > 0, (
            "No files found in Dropbox output"
        )

        # Verify S3 output
        bucket_name = "test-podcast-bucket"
        s3_objects = minio_client.list_bucket_objects(bucket_name, "podcasts/")
        assert len(s3_objects) > 0, "No objects found in S3 bucket"

        # Verify naming patterns
        # Check Dropbox versioned naming pattern:
        # starts with 4 digits, dash, then has .mp3 extension
        versioned_files = [
            f for f in dropbox_filenames
            if f.startswith(("0001-", "0002-", "0003-")) and f.endswith(".mp3")
        ]
        assert len(versioned_files) > 0, (
            f"No properly versioned Dropbox files. Files: {dropbox_filenames}"
        )

        # Check S3 ISO 8601 timestamp pattern: podcasts/YYYY-MM-DDTHHMMSS.mp3
        iso_pattern = re.compile(r"^podcasts/\d{4}-\d{2}-\d{2}T\d{6}\.mp3$")
        timestamped_files = [
            obj for obj in s3_objects if iso_pattern.match(obj)
        ]
        assert len(timestamped_files) > 0, (
            f"No properly timestamped S3 files. Objects: {s3_objects}"
        )

        logger.info("Complete dual-publishing pipeline test completed successfully!")
        logger.info(f"Dropbox files: {versioned_files}")
        logger.info(f"S3 objects: {timestamped_files}")
