"""Pytest configuration for jobs tests.

Adds job source directories to sys.path and provides shared
fixtures for GCS integration tests against fake-gcs-server.
"""

import sys
from pathlib import Path

import pytest
from google.cloud import storage as gcs

_jobs_dir = Path(__file__).parent.parent
sys.path.insert(0, str(_jobs_dir / "runner"))
sys.path.insert(0, str(_jobs_dir / "grader"))

_BUCKET_NAME = "codette-test"


@pytest.fixture(scope="session")
def gcs_bucket() -> gcs.Bucket:
    """Ensure the test bucket exists in fake-gcs-server (session-scoped)."""
    client = gcs.Client()
    bucket = client.bucket(_BUCKET_NAME)
    if not bucket.exists():
        client.create_bucket(bucket)
    return bucket
