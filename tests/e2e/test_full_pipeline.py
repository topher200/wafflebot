"""End-to-end tests for the complete audio processing pipeline."""

import logging
import re
from datetime import datetime
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
def dummy_podcast_file(clean_test_outputs):
    """Fixture to create a dummy podcast file directly in the local podcast
    directory for upload tests.
    """
    podcast_dir = clean_test_outputs / "podcast"
    dummy_file = podcast_dir / "voice_memo_mix.mp3"
    dummy_file.write_text("dummy audio content for testing")
    yield dummy_file


class TestFullPipeline:
    """Test the complete audio processing pipeline."""

    def test_audio_mixer_processes_test_files(
        self,
        test_audio_files: List[Dict[str, Any]],
        test_background_music: List[Dict[str, Any]],
        docker_manager: DockerComposeTestManager,
        clean_docker_environment,
        clean_test_outputs: Path,
    ):
        """Test that the audio mixer can process test audio files successfully."""
        logger.info("Testing audio mixer with test files...")

        # Verify test files are available
        assert len(test_audio_files) >= 2, "Need at least 2 test audio files"
        assert len(test_background_music) >= 1, "Need at least 1 background music file"

        for file_config in test_audio_files:
            assert file_config["local_path"].exists(), (
                f"Test file missing: {file_config['local_path']}"
            )

        for music_config in test_background_music:
            assert music_config["local_path"].exists(), (
                f"Background music missing: {music_config['local_path']}"
            )

        # Build the audio mixer service
        assert docker_manager.build_services(["audio-mixer"]), (
            "Failed to build audio-mixer service"
        )

        # Run the audio mixer
        result = docker_manager.run_service("audio-mixer")

        # Check that the service completed successfully
        if result.returncode != 0:
            logger.error(f"Audio mixer STDOUT: {result.stdout}")
            logger.error(f"Audio mixer STDERR: {result.stderr}")
        assert result.returncode == 0, f"Audio mixer failed: {result.stderr}"

        # Verify that output was created in the local podcast directory
        podcast_dir = clean_test_outputs / "podcast"
        output_files = list(podcast_dir.glob("voice_memo_mix.mp3"))
        assert len(output_files) > 0, (
            f"Expected output file voice_memo_mix.mp3 not found in {podcast_dir}"
        )
        logger.info(
            f"✅ Generated audio file: {output_files[0]} "
            f"({output_files[0].stat().st_size} bytes)"
        )
        logger.info(f"🎵 You can listen to it with: mpv {output_files[0]}")
        logger.info("Audio mixer test completed successfully")

    def test_publish_to_dropbox_creates_versioned_file(
        self,
        docker_manager: DockerComposeTestManager,
        clean_docker_environment,
        clean_test_outputs: Path,
        dummy_podcast_file,
    ):
        """Test that the publish script creates properly versioned files
        using dummy audio.
        """
        logger.info(
            "Testing publish-to-dropbox with versioned naming (using dummy file)..."
        )
        assert docker_manager.build_services(["publish-to-dropbox"]), (
            "Failed to build publish-to-dropbox service"
        )
        publish_result = docker_manager.run_service("publish-to-dropbox")
        assert publish_result.returncode == 0, (
            f"Publish script failed: {publish_result.stderr}"
        )

        # Check the local dropbox output directory
        dropbox_dir = clean_test_outputs / "dropbox"
        mp3_files = list(dropbox_dir.glob("*.mp3"))
        assert len(mp3_files) > 0, f"No MP3 files found in {dropbox_dir}"
        versioned_files = [
            f
            for f in mp3_files
            if f.name.startswith(("0001-", "0002-", "0003-"))
            and f.name.endswith(".mp3")
        ]
        assert len(versioned_files) > 0, (
            f"No properly versioned files found. Files: {[f.name for f in mp3_files]}"
        )
        for file in versioned_files:
            logger.info(
                f"✅ Generated Dropbox file: {file} ({file.stat().st_size} bytes)"
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
        assert docker_manager.build_services(["publish-podcast-to-s3"]), (
            "Failed to build publish-podcast-to-s3 service"
        )
        publish_result = docker_manager.run_service("publish-podcast-to-s3")
        if publish_result.returncode != 0:
            logger.error(f"S3 publish STDOUT: {publish_result.stdout}")
            logger.error(f"S3 publish STDERR: {publish_result.stderr}")
        assert publish_result.returncode == 0, (
            f"S3 publish script failed: {publish_result.stderr}"
        )

        bucket_name = "test-podcast-bucket"
        objects = minio_client.list_bucket_objects(bucket_name, "podcasts/")
        assert len(objects) > 0, "No objects found in MinIO bucket"

        # Check for ISO 8601 timestamp pattern: podcasts/YYYY-MM-DDTHHMMSS.mp3
        iso_pattern = re.compile(r"^podcasts/\d{4}-\d{2}-\d{2}T\d{6}\.mp3$")
        timestamped_files = [obj for obj in objects if iso_pattern.match(obj)]
        assert len(timestamped_files) > 0, (
            f"No properly timestamped files found. Objects: {objects}"
        )

        logger.info(
            f"S3 publish test completed successfully. Uploaded: {timestamped_files[0]}"
        )

    # TODO(topher): re-enable this when RSS feed is implemented
    @pytest.mark.skip(reason="RSS feed is not implemented yet")
    def test_update_rss_feed_generates_feed(
        self,
        docker_manager: DockerComposeTestManager,
        clean_docker_environment,
        minio_client: MinIOTestClient,
        clean_test_outputs: Path,
    ):
        """Test that the RSS feed service generates and uploads RSS feed to S3."""
        logger.info("Testing update-rss-feed with MinIO...")

        # First, we need some podcast files in S3 for the RSS feed to process
        # Upload a dummy podcast file using the new MinIOTestClient upload method
        bucket_name = "test-podcast-bucket"
        test_filename = f"podcasts/{datetime.now().strftime('%Y-%m-%dT%H%M%S')}.mp3"
        test_content = "dummy podcast content for RSS testing"

        # Upload test content using the MinIO helper
        upload_success = minio_client.upload_content(
            bucket_name, test_filename, test_content
        )
        assert upload_success, "Failed to upload test podcast file to MinIO"

        # Verify the test file was uploaded
        objects_before = minio_client.list_bucket_objects(bucket_name, "podcasts/")
        assert len(objects_before) > 0, "Test podcast file should be uploaded"

        # Build and run the RSS feed service
        assert docker_manager.build_services(["update-rss-feed"]), (
            "Failed to build update-rss-feed service"
        )

        rss_result = docker_manager.run_service("update-rss-feed")
        if rss_result.returncode != 0:
            logger.error(f"RSS feed STDOUT: {rss_result.stdout}")
            logger.error(f"RSS feed STDERR: {rss_result.stderr}")
        assert rss_result.returncode == 0, (
            f"RSS feed service failed: {rss_result.stderr}"
        )

        # Verify RSS feed was saved locally
        rss_dir = clean_test_outputs / "rss"
        rss_files = list(rss_dir.glob("*.xml"))
        assert len(rss_files) > 0, f"No RSS files found in {rss_dir}"

        rss_file = rss_files[0]
        rss_content = rss_file.read_text(encoding="utf-8")

        # Verify RSS content structure
        assert "<?xml version=" in rss_content, "RSS should have XML declaration"
        assert "<rss version=" in rss_content, "RSS should have rss element"
        assert "WaffleBot Podcast" in rss_content, "RSS should have podcast title"
        assert "<channel>" in rss_content, "RSS should have channel element"
        assert "Found 1 episodes" in rss_content, (
            "RSS should reference the test episode"
        )

        # Verify RSS feed was uploaded to S3
        rss_objects = minio_client.list_bucket_objects(bucket_name, "rss/")
        assert len(rss_objects) > 0, "No RSS objects found in MinIO bucket"

        # Should find podcast.xml (default name)
        rss_files_s3 = [obj for obj in rss_objects if obj.endswith(".xml")]
        assert len(rss_files_s3) > 0, (
            f"No XML files found in S3. Objects: {rss_objects}"
        )
        assert "rss/podcast.xml" in rss_files_s3, "Default RSS feed name not found"

        logger.info(
            f"✅ RSS feed saved locally: {rss_file} ({rss_file.stat().st_size} bytes)"
        )
        logger.info(f"☁️  RSS feed uploaded to S3: {rss_files_s3[0]}")
        logger.info("RSS feed test completed successfully")

    def test_complete_pipeline_end_to_end(
        self,
        test_audio_files: List[Dict[str, Any]],
        test_background_music: List[Dict[str, Any]],
        docker_manager: DockerComposeTestManager,
        minio_client: MinIOTestClient,
        clean_docker_environment,
        clean_test_outputs: Path,
    ):
        """Test the complete pipeline from audio files to published output."""
        logger.info("Running complete end-to-end pipeline test...")

        # Verify prerequisites
        assert len(test_audio_files) >= 2, (
            "Need at least 2 test audio files for complete test"
        )
        assert len(test_background_music) >= 1, "Need at least 1 background music file"

        # Build all required services
        services_to_build = [
            "audio-mixer",
            "publish-to-dropbox",
            "publish-podcast-to-s3",
            "update-rss-feed",
        ]
        assert docker_manager.build_services(services_to_build), (
            "Failed to build required services"
        )

        # Step 1: Run audio mixer
        logger.info("Step 1: Running audio mixer...")
        mixer_success = wait_for_service_completion(docker_manager, "audio-mixer")
        assert mixer_success, "Audio mixer step failed"

        # Verify intermediate output exists in local directory
        podcast_dir = clean_test_outputs / "podcast"
        mixed_files = list(podcast_dir.glob("voice_memo_mix.mp3"))
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

        # TODO(topher): re-enable this when RSS feed is implemented
        # logger.info("Step 4: Running RSS feed update...")
        # rss_success = wait_for_service_completion(docker_manager, "update-rss-feed")
        # assert rss_success, "RSS feed update step failed"

        # Verify Dropbox output in local directory
        dropbox_dir = clean_test_outputs / "dropbox"
        dropbox_files = list(dropbox_dir.glob("*.mp3"))
        assert len(dropbox_files) > 0, f"No files found in {dropbox_dir}"
        versioned_files = [
            f
            for f in dropbox_files
            if f.name.startswith(("0001-", "0002-", "0003-"))
            and f.name.endswith(".mp3")
        ]
        assert len(versioned_files) > 0, (
            f"No properly versioned Dropbox files. Files: "
            f"{[f.name for f in dropbox_files]}"
        )

        # Verify S3 output
        bucket_name = "test-podcast-bucket"
        s3_objects = minio_client.list_bucket_objects(bucket_name, "podcasts/")
        assert len(s3_objects) > 0, "No objects found in S3 bucket"

        # Verify naming patterns
        # Check Dropbox versioned naming pattern: starts with 4 digits,
        # dash, then has .mp3 extension
        versioned_files = [
            f
            for f in dropbox_files
            if f.name.startswith(("0001-", "0002-", "0003-"))
            and f.name.endswith(".mp3")
        ]
        assert len(versioned_files) > 0, (
            f"No properly versioned Dropbox files. Files: "
            f"{[f.name for f in dropbox_files]}"
        )

        # Check S3 ISO 8601 timestamp pattern: podcasts/YYYY-MM-DDTHHMMSS.mp3
        iso_pattern = re.compile(r"^podcasts/\d{4}-\d{2}-\d{2}T\d{6}\.mp3$")
        timestamped_files = [obj for obj in s3_objects if iso_pattern.match(obj)]
        assert len(timestamped_files) > 0, (
            f"No properly timestamped S3 files. Objects: {s3_objects}"
        )

        # TODO(topher): re-enable this when RSS feed is implemented
        # # Verify RSS feed output
        # rss_dir = clean_test_outputs / "rss"
        # rss_files = list(rss_dir.glob("*.xml"))
        # assert len(rss_files) > 0, f"No RSS files found in {rss_dir}"

        # # Verify RSS feed was uploaded to S3
        # rss_objects = minio_client.list_bucket_objects(bucket_name, "rss/")
        # assert len(rss_objects) > 0, "No RSS objects found in S3 bucket"
        # rss_files_s3 = [obj for obj in rss_objects if obj.endswith(".xml")]
        # assert len(rss_files_s3) > 0, (
        #     f"No RSS XML files found in S3. Objects: {rss_objects}"
        # )

        logger.info(
            f"🎵 Mixed audio: {mixed_files[0]} ({mixed_files[0].stat().st_size} bytes)"
        )
        for file in versioned_files:
            logger.info(f"📦 Dropbox file: {file} ({file.stat().st_size} bytes)")
        logger.info(f"☁️  S3 objects: {timestamped_files}")
        # TODO(topher): re-enable this when RSS feed is implemented
        # logger.info(
        #     f"📻 RSS feed: {rss_files[0]} ({rss_files[0].stat().st_size} bytes)"
        # )
        # logger.info(f"☁️  RSS S3 objects: {rss_files_s3}")
        logger.info(f"🎧 Listen with: mpv {mixed_files[0]}")
        logger.info("Complete pipeline with RSS feed test completed successfully!")
        logger.info(f"Dropbox files: {versioned_files}")
        logger.info(f"S3 objects: {timestamped_files}")
