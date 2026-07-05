"""
Google OAuth authentication using modern google-auth library.

ARCHITECTURAL DECISION: Migration from oauth2client
---------------------------------------------------
Your existing bloggerApi.py uses oauth2client which Google deprecated in 2018.
This module migrates to the modern authentication stack:

OLD (deprecated):
    - oauth2client.client
    - oauth2client.file.Storage
    - httplib2

NEW (recommended):
    - google.auth.credentials.Credentials
    - google_auth_oauthlib.flow.InstalledAppFlow
    - google.auth.transport.requests.Request
    - google.api-python-client (in blogger_client.py)

Trade-offs of this approach:
- PROS: Official Google recommendation, actively maintained, better security
- CONS: Migration effort, slightly different API

SECURITY NOTE:
Credentials are stored in plain JSON. In production, consider encrypting them
or using a secrets manager. For this desktop OAuth flow, the default storage
is acceptable but should never be committed to version control (.gitignore handles this).
"""

import json
from pathlib import Path
from typing import List, Optional

from google.auth import exceptions as google_auth_exceptions
from google.oauth2.credentials import Credentials
from google.auth.transport import requests as google_auth_requests
from google_auth_oauthlib.flow import InstalledAppFlow

from config import get_settings, get_logger
from core.exceptions import AuthenticationError, ConfigurationError

logger = get_logger("core", "auth")


class Authenticator:
    """
    Handles Google OAuth 2.0 authentication for Blogger API.

    ARCHITECTURAL DECISION: Service class vs module-level functions
    --------------------------------------------------------------
    We use a class because:
    1. It encapsulates state (credentials) with methods
    2. Easier to mock in tests
    3. Allows future extension (multiple accounts, token refresh)
    4. Follows the Service pattern from clean architecture

    The authenticator handles:
    - Loading existing credentials from storage
    - Running OAuth flow if no valid credentials exist
    - Refreshing expired access tokens automatically
    - Validating credentials before use
    """

    def __init__(
        self,
        client_secret_path: Optional[Path] = None,
        credentials_path: Optional[Path] = None,
        scopes: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize authenticator with paths.

        Args:
            client_secret_path: Path to OAuth client secrets JSON
            credentials_path: Path to store/retrieve credentials
            scopes: OAuth scopes to request (defaults from settings)

        Raises:
            ConfigurationError: If paths don't exist or are invalid
        """
        settings = get_settings()
        self._client_secret_path = (
            Path(client_secret_path) if client_secret_path else Path(settings.google_client_secret_path)
        )
        self._credentials_path = (
            Path(credentials_path) if credentials_path else Path(settings.google_credentials_storage_path)
        )
        self._scopes = scopes or settings.get_scopes()

        self._validate_client_secret_exists()
        logger.debug(
            "Authenticator initialized",
            client_secret=str(self._client_secret_path),
            credentials=str(self._credentials_path),
        )

    def _validate_client_secret_exists(self) -> None:
        """Validate that client_secret.json exists and is readable."""
        if not self._client_secret_path.exists():
            raise ConfigurationError(
                "Google client_secret.json not found",
                details={"path": str(self._client_secret_path)},
            )

    def load_credentials(self) -> Credentials:
        """
        Load credentials from storage or run OAuth flow.

        Design decision: Credentials are stored as plain JSON for the
        InstalledAppFlow, unlike oauth2client's custom format.

        Returns:
            Valid, authorized Credentials object

        Raises:
            AuthenticationError: If OAuth flow fails
        """
        credentials = self._load_from_file()

        # Refresh if expired, or run OAuth flow if no credentials
        if credentials and credentials.expired:
            logger.info("Refreshing expired credentials")
            credentials = self._refresh_credentials(credentials)

        if credentials is None or not credentials.valid:
            credentials = self._run_oauth_flow()

        return credentials

    def _load_from_file(self) -> Optional[Credentials]:
        """Load credentials from the storage file if it exists."""
        if not self._credentials_path.exists():
            logger.debug("No credentials file found", path=str(self._credentials_path))
            return None

        try:
            credentials = Credentials.from_authorized_user_file(
                str(self._credentials_path), scopes=self._scopes
            )
            logger.debug("Loaded credentials from file", valid=credentials.valid if credentials else None)
            return credentials
        except Exception as e:
            logger.warning("Failed to load credentials", error=str(e))
            return None

    def _refresh_credentials(self, credentials: Credentials) -> Credentials:
        """
        Refresh expired credentials using refresh token.

        Design decision: We use google.auth.transport.requests.Request
        instead of httplib2 for lighter weight HTTP handling.
        """
        try:
            request = google_auth_requests.Request()
            credentials.refresh(request)
            self._save_credentials(credentials)
            logger.info("Credentials refreshed successfully")
            return credentials
        except google_auth_exceptions.RefreshError as e:
            logger.error("Failed to refresh credentials", error=str(e))
            # Fall through to OAuth flow
            return self._run_oauth_flow()

    def _run_oauth_flow(self) -> Credentials:
        """
        Run the OAuth 2.0 flow to get new credentials.

        Design decision: Uses InstalledAppFlow for console applications.
        This opens a browser for the user to authenticate.

        For headless operation (Phase 7 dashboard), we'll add
        a device flow alternative.
        """
        logger.info("Starting OAuth flow")

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self._client_secret_path),
                scopes=self._scopes,
            )
            credentials = flow.run_local_server(port=0)
            self._save_credentials(credentials)
            logger.info("OAuth flow completed successfully")
            return credentials
        except Exception as e:
            raise AuthenticationError(
                "OAuth authentication failed",
                details={"error": str(e), "path": str(self._client_secret_path)},
            ) from e

    def _save_credentials(self, credentials: Credentials) -> None:
        """
        Save credentials to the storage file.

        Design decision: Uses Google's standard JSON format for
        Credentials, which is compatible with future google-auth features.
        """
        self._credentials_path.parent.mkdir(parents=True, exist_ok=True)
        self._credentials_path.write_text(
            credentials.to_json()
        )
        logger.debug("Credentials saved", path=str(self._credentials_path))

    def get_authorized_session(self) -> google_auth_requests.Request:
        """
        Get an authorized HTTP session for API calls.

        Returns:
            Authorized Request object for use with googleapiclient

        This is a convenience method that combines credential loading
        and authorization in one step.
        """
        credentials = self.load_credentials()
        return google_auth_requests.Request()

    def validate_credentials(self) -> bool:
        """
        Validate that current credentials are valid and not expired.

        Returns:
            True if credentials are valid and not expired
        """
        try:
            credentials = self.load_credentials()
            return credentials.valid and not credentials.expired
        except Exception as e:
            logger.error("Credential validation failed", error=str(e))
            return False