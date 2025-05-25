"""End-to-end tests for the complete audio processing pipeline."""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List

from tests.e2e.utils.docker_helpers import (
    DockerComposeTestManager,
    wait_for_service_completion,
)

logger = logging.getLogger(__name__)


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
        test_audio_files: List[Dict[str, Any]],
        test_background_music: List[Dict[str, Any]],
        docker_manager: DockerComposeTestManager,
        clean_docker_environment,
        temp_output_dir: Path,
    ):
        """Test that the publish script creates properly versioned files."""
        logger.info("Testing publish-to-dropbox with versioned naming...")

        # First run audio mixer to create input for publish script
        assert docker_manager.build_services(
            ["audio-mixer"]
        ), "Failed to build audio-mixer service"

        mixer_result = docker_manager.run_service("audio-mixer")
        assert (
            mixer_result.returncode == 0
        ), f"Audio mixer failed: {mixer_result.stderr}"

        # Now build and run the publish service
        assert docker_manager.build_services(
            ["publish-to-dropbox"]
        ), "Failed to build publish-to-dropbox service"

        publish_result = docker_manager.run_service("publish-to-dropbox")
        assert (
            publish_result.returncode == 0
        ), f"Publish script failed: {publish_result.stderr}"

        # Verify that a versioned file was created in the dropbox output volume
        volume_contents = docker_manager.get_volume_contents(
            "test-dropbox-output", "/data"
        )
        assert (
            volume_contents is not None
        ), "Could not inspect test-dropbox-output volume"

        # Look for files matching the expected pattern: "0001-Month Day, Year.mp3"
        mp3_files = [line for line in volume_contents if line.endswith(".mp3")]
        assert len(mp3_files) > 0, "No MP3 files found in dropbox output volume"

        # Check that at least one file matches the expected naming pattern
        version_pattern = re.compile(r"\d{4}-\w+ \d{1,2}, \d{4}\.mp3")
        versioned_files = [f for f in mp3_files if version_pattern.search(f)]
        assert (
            len(versioned_files) > 0
        ), f"No properly versioned files found. Files: {mp3_files}"

        logger.info("Publish script test completed successfully")

    def test_complete_pipeline_end_to_end(
        self,
        test_audio_files: List[Dict[str, Any]],
        test_background_music: List[Dict[str, Any]],
        docker_manager: DockerComposeTestManager,
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

        # Step 2: Run publish script
        logger.info("Step 2: Running publish script...")
        publish_success = wait_for_service_completion(
            docker_manager, "publish-to-dropbox"
        )
        assert publish_success, "Publish script step failed"

        # Verify final output exists
        dropbox_volume_contents = docker_manager.get_volume_contents(
            "test-dropbox-output", "/data"
        )
        assert (
            dropbox_volume_contents is not None
        ), "Could not inspect dropbox output volume"

        published_files = [
            line for line in dropbox_volume_contents if line.endswith(".mp3")
        ]
        assert len(published_files) > 0, "No published files found in final output"

        # Verify the published file has the correct naming pattern
        version_pattern = re.compile(r"\d{4}-\w+ \d{1,2}, \d{4}\.mp3")
        versioned_files = [f for f in published_files if version_pattern.search(f)]
        assert (
            len(versioned_files) > 0
        ), f"Published file doesn't match expected pattern. Files: {published_files}"

        logger.info("Complete end-to-end pipeline test completed successfully!")
        logger.info(f"Final published files: {versioned_files}")
