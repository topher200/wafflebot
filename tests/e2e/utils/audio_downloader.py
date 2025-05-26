"""Utility for downloading and caching test audio files."""

import hashlib
import logging
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)


def download_and_cache_audio(
    url: str, cache_path: Path, force_download: bool = False
) -> bool:
    """
    Download audio file from URL and cache it locally.

    Args:
        url: URL to download the audio file from
        cache_path: Local path where the file should be cached
        force_download: If True, download even if file already exists

    Returns:
        True if file was downloaded or already exists, False if download failed
    """
    if cache_path.exists() and not force_download:
        logger.info(f"Audio file already cached: {cache_path}")
        return True

    logger.info(f"Downloading audio file from {url} to {cache_path}")

    try:
        # Create cache directory if it doesn't exist
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Download the file
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Write to cache
        with open(cache_path, "wb") as f:
            f.write(response.content)

        logger.info(f"Successfully downloaded and cached: {cache_path}")
        return True

    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False
    except IOError as e:
        logger.error(f"Failed to write to {cache_path}: {e}")
        return False


def get_cache_path_for_url(
    url: str, cache_dir: Path, filename: Optional[str] = None
) -> Path:
    """
    Generate a cache path for a given URL.

    Args:
        url: The URL to generate a cache path for
        cache_dir: Directory where cached files are stored
        filename: Optional specific filename to use, otherwise derive from URL

    Returns:
        Path where the file should be cached
    """
    if filename:
        return cache_dir / filename

    # Generate filename from URL hash if not provided
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    url_path = Path(url)
    extension = url_path.suffix or ".bin"
    return cache_dir / f"{url_hash}{extension}"


def verify_audio_file(file_path: Path) -> bool:
    """
    Basic verification that a file exists and has content.

    Args:
        file_path: Path to the audio file to verify

    Returns:
        True if file exists and has content, False otherwise
    """
    if not file_path.exists():
        logger.error(f"Audio file does not exist: {file_path}")
        return False

    if file_path.stat().st_size == 0:
        logger.error(f"Audio file is empty: {file_path}")
        return False

    logger.info(f"Audio file verified: {file_path} ({file_path.stat().st_size} bytes)")
    return True
