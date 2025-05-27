"""MinIO utilities for e2e testing."""

import logging
import subprocess
import time
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class MinIOTestClient:
    """Client for interacting with MinIO during tests."""

    def __init__(
        self,
        endpoint: str = "http://localhost:9100",
        access_key: str = "testuser",
        secret_key: str = "testpassword",
    ):
        self.endpoint = endpoint  # For health checks from host
        self.container_endpoint = "http://minio:9000"  # For AWS CLI from containers
        self.access_key = access_key
        self.secret_key = secret_key

    def wait_for_minio_ready(self, timeout: int = 60) -> bool:
        """Wait for MinIO to be ready to accept connections."""
        logger.info("Waiting for MinIO to be ready...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Health check from host uses localhost:9100
                response = requests.get(f"{self.endpoint}/minio/health/live", timeout=5)
                if response.status_code == 200:
                    logger.info("MinIO is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass

            time.sleep(2)

        logger.error(f"MinIO not ready after {timeout} seconds")
        return False

    def _run_aws_cli_in_container(self, args: List[str]) -> subprocess.CompletedProcess:
        docker_cmd = [
            "docker", "run", "--rm",
            "--network=wafflebot_default",
            "-e", f"AWS_ACCESS_KEY_ID={self.access_key}",
            "-e", f"AWS_SECRET_ACCESS_KEY={self.secret_key}",
            "-e", "AWS_DEFAULT_REGION=us-east-1",
            "amazon/aws-cli:2.13.14"
        ] + args
        return subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True
        )

    def list_bucket_objects(self, bucket_name: str, prefix: str = "") -> List[str]:
        """List objects in a bucket using AWS CLI (in a container)."""
        try:
            cmd = [
                "s3", "ls", f"s3://{bucket_name}/{prefix}",
                "--endpoint-url", self.container_endpoint,
                "--recursive"
            ]
            result = self._run_aws_cli_in_container(cmd)
            if result.returncode == 0:
                objects = []
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            objects.append(' '.join(parts[3:]))
                return objects
            else:
                logger.error(f"Failed to list objects: {result.stderr}")
                return []
        except Exception as e:
            logger.error(f"Error listing bucket objects: {e}")
            return []

    def object_exists(self, bucket_name: str, object_key: str) -> bool:
        """Check if an object exists in the bucket (in a container)."""
        try:
            cmd = [
                "s3", "ls", f"s3://{bucket_name}/{object_key}",
                "--endpoint-url", self.container_endpoint
            ]
            result = self._run_aws_cli_in_container(cmd)
            return result.returncode == 0 and object_key in result.stdout
        except Exception as e:
            logger.error(f"Error checking object existence: {e}")
            return False

    def get_object_info(
        self, bucket_name: str, object_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get information about an object (in a container)."""
        try:
            cmd = [
                "s3api", "head-object",
                "--bucket", bucket_name,
                "--key", object_key,
                "--endpoint-url", self.container_endpoint
            ]
            result = self._run_aws_cli_in_container(cmd)
            if result.returncode == 0:
                import json
                return json.loads(result.stdout)
            else:
                logger.error(f"Failed to get object info: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Error getting object info: {e}")
            return None
