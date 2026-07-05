"""
Pytest configuration and shared fixtures.

ARCHITECTURAL DECISION: Fixtures for testability
-------------------------------------------------
We use pytest fixtures to:
1. Provide mock credentials for testing without real OAuth
2. Create test instances of our classes
3. Set up temporary directories for file operations

This allows tests to run without:
- Network access
- Real Google credentials
- Side effects on production data
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from google.oauth2.credentials import Credentials

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_credentials() -> Credentials:
    """
    Create mock credentials for testing.

    Design decision: This mock mimics real Credentials enough
    for googleapiclient to work, but doesn't make API calls.
    """
    return Credentials(
        token="mock-access-token",
        refresh_token="mock-refresh-token",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="mock-client-id.apps.googleusercontent.com",
        client_secret="mock-client-secret",
        scopes=["https://www.googleapis.com/auth/blogger"],
    )


@pytest.fixture
def temp_credentials_file(mock_credentials: Credentials) -> Path:
    """Create a temporary credentials file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(mock_credentials.to_authorized_user_info(), f)
        yield Path(f.name)
    # Cleanup happens automatically with delete=True on some systems


@pytest.fixture
def mock_blogger_service():
    """
    Create a mock Blogger API service.

    Design decision: We mock at the service level to test our
    wrapper methods without making real API calls.
    """
    mock_service = MagicMock()
    mock_posts = MagicMock()
    mock_service.posts.return_value = mock_posts
    return mock_service


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Configure logging for tests to avoid output noise."""
    # Import here to avoid circular imports
    from config import setup_logging

    setup_logging(level="DEBUG", log_format="plain")