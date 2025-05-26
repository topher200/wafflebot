"""Docker utilities for e2e testing."""

import logging
import subprocess
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class DockerComposeTestManager:
    """Manages Docker Compose operations for testing."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.base_compose_file = project_root / "docker-compose.yml"
        self.test_compose_file = project_root / "docker-compose.test.yml"

    def _run_compose_command(
        self, command: List[str], capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """Run a docker compose command with the test configuration."""
        full_command = [
            "docker",
            "compose",
            "-f",
            str(self.base_compose_file),
            "-f",
            str(self.test_compose_file),
        ] + command

        logger.info(f"Running: {' '.join(full_command)}")

        result = subprocess.run(
            full_command,
            capture_output=capture_output,
            text=True,
            cwd=self.project_root,
        )

        if result.returncode != 0:
            logger.error(f"Command failed with exit code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")

        return result

    def cleanup_test_environment(self) -> bool:
        """Clean up test volumes and containers."""
        logger.info("Cleaning up test environment...")
        result = self._run_compose_command(["down", "-v", "--remove-orphans"])
        return result.returncode == 0

    def run_service(
        self, service_name: str, remove: bool = True
    ) -> subprocess.CompletedProcess:
        """Run a specific service in the test environment."""
        command = ["run"]
        if remove:
            command.append("--rm")
        command.append(service_name)

        return self._run_compose_command(command)

    def build_services(self, services: Optional[List[str]] = None) -> bool:
        """Build the specified services (or all if none specified)."""
        command = ["build"]
        if services:
            command.extend(services)

        result = self._run_compose_command(command)
        return result.returncode == 0

    def get_volume_contents(
        self, volume_name: str, path: str = "/data"
    ) -> Optional[List[str]]:
        """Get the contents of a Docker volume."""
        try:
            # Docker Compose prefixes volume names with project name
            full_volume_name = f"wafflebot_{volume_name}"

            # Create a temporary container to inspect the volume
            result = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--platform",
                    "linux/amd64",
                    "-v",
                    f"{full_volume_name}:/data",
                    "alpine",
                    "ls",
                    "-la",
                    path,
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return result.stdout.strip().split("\n")
            else:
                logger.error(
                    f"Failed to inspect volume {full_volume_name}: {result.stderr}"
                )
                return None

        except Exception as e:
            logger.error(f"Error inspecting volume {volume_name}: {e}")
            return None

    def copy_from_volume(
        self, volume_name: str, source_path: str, dest_path: Path
    ) -> bool:
        """Copy a file from a Docker volume to the local filesystem."""
        try:
            # Docker Compose prefixes volume names with project name
            full_volume_name = f"wafflebot_{volume_name}"

            # Create a temporary container to copy from the volume
            container_name = f"temp_copy_{volume_name.replace('-', '_')}"

            # Create container
            create_result = subprocess.run(
                [
                    "docker",
                    "create",
                    "--platform",
                    "linux/amd64",
                    "--name",
                    container_name,
                    "-v",
                    f"{full_volume_name}:/volume_data",
                    "alpine",
                ],
                capture_output=True,
                text=True,
            )

            if create_result.returncode != 0:
                logger.error(f"Failed to create temp container: {create_result.stderr}")
                return False

            try:
                # Copy file from container
                copy_result = subprocess.run(
                    [
                        "docker",
                        "cp",
                        f"{container_name}:/volume_data/{source_path}",
                        str(dest_path),
                    ],
                    capture_output=True,
                    text=True,
                )

                success = copy_result.returncode == 0
                if not success:
                    logger.error(f"Failed to copy from volume: {copy_result.stderr}")

                return success

            finally:
                # Clean up temp container
                subprocess.run(["docker", "rm", container_name], capture_output=True)

        except Exception as e:
            logger.error(f"Error copying from volume {volume_name}: {e}")
            return False


def wait_for_service_completion(
    manager: DockerComposeTestManager, service_name: str, timeout: int = 300
) -> bool:
    """
    Wait for a service to complete successfully.

    Args:
        manager: DockerComposeTestManager instance
        service_name: Name of the service to wait for
        timeout: Maximum time to wait in seconds

    Returns:
        True if service completed successfully, False otherwise
    """
    logger.info(f"Waiting for service {service_name} to complete...")

    result = manager.run_service(service_name)

    if result.returncode == 0:
        logger.info(f"Service {service_name} completed successfully")
        return True
    else:
        logger.error(
            f"Service {service_name} failed with exit code {result.returncode}"
        )
        logger.error(f"STDOUT: {result.stdout}")
        logger.error(f"STDERR: {result.stderr}")
        return False
