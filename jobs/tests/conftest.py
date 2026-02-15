"""Pytest configuration for jobs tests.

Adds the jobs root to sys.path so that runner and grader are importable
as packages (e.g. ``from runner.run import _validate``).

Provides shared fixtures for GCS integration tests against fake-gcs-server.
"""

import sys
from pathlib import Path

import pytest
from google.cloud import storage as gcs

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

_BUCKET_NAME = "codette-test"


@pytest.fixture(scope="session")
def gcs_bucket() -> gcs.Bucket:
    """Ensure the test bucket exists in fake-gcs-server (session-scoped)."""
    client = gcs.Client()
    bucket = client.bucket(_BUCKET_NAME)
    if not bucket.exists():
        client.create_bucket(bucket)
    return bucket
