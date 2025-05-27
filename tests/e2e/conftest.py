"""Pytest configuration and fixtures for e2e tests."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import pytest

from tests.e2e.utils.audio_downloader import download_and_cache_audio, verify_audio_file
from tests.e2e.utils.docker_helpers import DockerComposeTestManager
from tests.e2e.utils.minio_helpers import MinIOTestClient

logger = logging.getLogger(__name__)

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
CACHE_DIR = PROJECT_ROOT / "tests" / "cache"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Provide the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def cache_dir() -> Path:
    """Provide the test cache directory."""
    CACHE_DIR.mkdir(exist_ok=True)
    return CACHE_DIR


@pytest.fixture(scope="session")
def test_audio_config() -> Dict[str, Any]:
    """Load test audio configuration from JSON file."""
    config_path = FIXTURES_DIR / "test_audio_urls.json"
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def test_audio_files(
    test_audio_config: Dict[str, Any], cache_dir: Path
) -> List[Dict[str, Any]]:
    """Download and cache test audio files, returning the file configurations."""
    logger.info("Setting up test audio files...")

    voice_memos_dir = cache_dir / "voice-memos"
    voice_memos_dir.mkdir(exist_ok=True)

    files = test_audio_config["test_files"]

    for file_config in files:
        url = file_config["url"]
        filename = file_config["filename"]
        cache_path = voice_memos_dir / filename

        # Download and cache the file
        success = download_and_cache_audio(url, cache_path)
        if not success:
            pytest.fail(f"Failed to download test audio file: {url}")

        # Verify the file
        if not verify_audio_file(cache_path):
            pytest.fail(f"Downloaded audio file failed verification: {cache_path}")

        # Add the local path to the config for convenience
        file_config["local_path"] = cache_path

    logger.info(f"Successfully set up {len(files)} test audio files")
    return files


@pytest.fixture(scope="session")
def test_background_music(
    test_audio_config: Dict[str, Any], cache_dir: Path
) -> List[Dict[str, Any]]:
    """Download and cache background music files, returning the file configurations."""
    logger.info("Setting up test background music...")

    background_music_dir = cache_dir / "background-music"
    background_music_dir.mkdir(exist_ok=True)

    music_files = test_audio_config.get("background_music", [])

    for music_config in music_files:
        url = music_config["url"]
        filename = music_config["filename"]
        music_path = background_music_dir / filename

        # Download and cache the file
        success = download_and_cache_audio(url, music_path)
        if not success:
            pytest.fail(f"Failed to download background music file: {url}")

        # Verify the file
        if not verify_audio_file(music_path):
            pytest.fail(
                f"Downloaded background music file failed verification: {music_path}"
            )

        # Add the local path to the config for convenience
        music_config["local_path"] = music_path

    logger.info(f"Successfully set up {len(music_files)} background music files")
    return music_files


@pytest.fixture(scope="function")
def docker_manager(project_root: Path) -> DockerComposeTestManager:
    """Provide a Docker Compose test manager."""
    return DockerComposeTestManager(project_root)


@pytest.fixture(scope="function")
def clean_docker_environment(docker_manager: DockerComposeTestManager):
    """Ensure a clean Docker environment for each test."""
    # Clean up before test
    docker_manager.cleanup_test_environment()

    yield

    # Clean up after test
    docker_manager.cleanup_test_environment()


@pytest.fixture(scope="function")
def minio_client(docker_manager: DockerComposeTestManager) -> MinIOTestClient:
    """Provide a MinIO test client and ensure MinIO is running."""
    # Start MinIO service
    logger.info("Starting MinIO service...")
    result = docker_manager._run_compose_command(["up", "-d", "minio"])
    if result.returncode != 0:
        pytest.fail(f"Failed to start MinIO: {result.stderr}")

    # Create client and wait for MinIO to be ready
    client = MinIOTestClient()
    if not client.wait_for_minio_ready():
        pytest.fail("MinIO failed to become ready")

    return client


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Configure logging for tests."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


@pytest.fixture(scope="function")
def temp_output_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for test outputs."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(exist_ok=True)
    return output_dir
