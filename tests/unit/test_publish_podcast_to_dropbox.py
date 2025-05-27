import os
import re
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestPublishScript:
    """Test the publish.sh shell script functionality."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            podcast_dir = temp_path / "data" / "podcast"
            dropbox_dir = temp_path / "dropbox-output"

            podcast_dir.mkdir(parents=True)
            dropbox_dir.mkdir(parents=True)

            yield {
                "temp_dir": temp_path,
                "podcast_dir": podcast_dir,
                "dropbox_dir": dropbox_dir,
            }

    @pytest.fixture
    def mock_audio_file(self, temp_dirs):
        """Create a mock audio file for testing."""
        audio_file = temp_dirs["podcast_dir"] / "voice_memo_mix.mp3"
        audio_file.write_text("fake audio content")
        return audio_file

    def run_publish_script(self, temp_dir, env_vars=None):
        """Helper to run the publish script with custom environment."""
        script_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "publish-podcast-to-dropbox"
            / "publish.sh"
        )

        # Set up environment variables
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        # Run the script from the temp directory
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            env=env,
        )

        return result

    def test_successful_publish_first_file(self, temp_dirs, mock_audio_file):
        """Test publishing when no previous files exist."""
        result = self.run_publish_script(temp_dirs["temp_dir"])

        assert result.returncode == 0
        assert "Publishing podcast to Dropbox..." in result.stdout
        assert "Podcast published successfully to Dropbox!" in result.stdout

        # Check that file was created with correct naming
        output_files = list(temp_dirs["dropbox_dir"].glob("*.mp3"))
        assert len(output_files) == 1

        # Should start with 0001
        assert output_files[0].name.startswith("0001-")

    def test_successful_publish_increments_prefix(self, temp_dirs, mock_audio_file):
        """Test that prefix increments correctly when previous files exist."""
        # Create existing files
        existing_file1 = temp_dirs["dropbox_dir"] / "0001-January 01, 2025.mp3"
        existing_file2 = temp_dirs["dropbox_dir"] / "0002-January 02, 2025.mp3"
        existing_file1.write_text("existing content")
        existing_file2.write_text("existing content")

        result = self.run_publish_script(temp_dirs["temp_dir"])

        assert result.returncode == 0

        # Check that new file has incremented prefix
        output_files = list(temp_dirs["dropbox_dir"].glob("0003-*.mp3"))
        assert len(output_files) == 1

    def test_missing_input_file_error(self, temp_dirs):
        """Test error handling when input file doesn't exist."""
        # Don't create the mock audio file
        result = self.run_publish_script(temp_dirs["temp_dir"])

        assert result.returncode == 1
        assert (
            "Error: Input file data/podcast/voice_memo_mix.mp3 not found"
            in result.stdout
        )

    def test_file_naming_with_date(self, temp_dirs, mock_audio_file):
        """Test that files are named with current date."""
        result = self.run_publish_script(temp_dirs["temp_dir"])

        assert result.returncode == 0

        # Check that file was created and contains a date pattern
        output_files = list(temp_dirs["dropbox_dir"].glob("*.mp3"))
        assert len(output_files) == 1

        # File should have format like "0001-January 01, 2025.mp3"
        filename = output_files[0].name
        assert filename.startswith("0001-")
        # Should contain month name and year
        date_pattern = (
            r"\d{4}-(January|February|March|April|May|June|July|August|September|"
            r"October|November|December) \d{1,2}, \d{4}\.mp3"
        )
        assert re.match(date_pattern, filename)

    def test_creates_output_directory(self, temp_dirs, mock_audio_file):
        """Test that script creates output directory if it doesn't exist."""
        # Remove the dropbox directory
        temp_dirs["dropbox_dir"].rmdir()

        result = self.run_publish_script(temp_dirs["temp_dir"])

        assert result.returncode == 0
        assert temp_dirs["dropbox_dir"].exists()

    def test_handles_no_existing_files(self, temp_dirs, mock_audio_file):
        """Test behavior when dropbox directory exists but has no MP3 files."""
        # Create some non-MP3 files
        (temp_dirs["dropbox_dir"] / "readme.txt").write_text("some text")
        (temp_dirs["dropbox_dir"] / "image.jpg").write_text("fake image")

        result = self.run_publish_script(temp_dirs["temp_dir"])

        assert result.returncode == 0

        # Should start with 0001 since no MP3 files existed
        output_files = list(temp_dirs["dropbox_dir"].glob("0001-*.mp3"))
        assert len(output_files) == 1

    def test_preserves_original_file(self, temp_dirs, mock_audio_file):
        """Test that original file is preserved (copied, not moved)."""
        original_content = mock_audio_file.read_text()

        result = self.run_publish_script(temp_dirs["temp_dir"])

        assert result.returncode == 0

        # Original file should still exist with same content
        assert mock_audio_file.exists()
        assert mock_audio_file.read_text() == original_content

        # New file should exist in dropbox directory
        output_files = list(temp_dirs["dropbox_dir"].glob("*.mp3"))
        assert len(output_files) == 1
        assert output_files[0].read_text() == original_content


class TestPublishIntegration:
    """Integration tests for the publish functionality."""

    def test_script_exists_and_executable(self):
        """Test that the publish script exists and is executable."""
        script_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "publish-podcast-to-dropbox"
            / "publish.sh"
        )
        assert script_path.exists()
        assert os.access(script_path, os.X_OK)

    def test_script_has_shebang(self):
        """Test that script has proper shebang."""
        script_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "publish-podcast-to-dropbox"
            / "publish.sh"
        )
        with open(script_path, "r") as f:
            first_line = f.readline().strip()
        assert first_line == "#!/bin/bash"

    def test_script_has_error_handling(self):
        """Test that script has 'set -e' for error handling."""
        script_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "publish-podcast-to-dropbox"
            / "publish.sh"
        )
        content = script_path.read_text()
        assert "set -e" in content

    def test_script_uses_correct_paths(self):
        """Test that script uses the expected file paths."""
        script_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "publish-podcast-to-dropbox"
            / "publish.sh"
        )
        content = script_path.read_text()

        assert 'INPUT_FILE="data/podcast/voice_memo_mix.mp3"' in content
        assert 'OUTPUT_DIR="dropbox-output"' in content
