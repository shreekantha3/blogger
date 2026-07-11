"""
Multi-account management for Blogger API.

ARCHITECTURAL DECISION: Account Manager Pattern
----------------------------------------------
Instead of hardcoding a single account, we use an AccountManager that:
1. Loads account profiles from config/accounts.yaml
2. Manages multiple credential files
3. Provides per-account BloggerClient instances
4. Supports account switching via CLI

This allows:
- Separate credentials per account (already supported by OAuth flow)
- Easy switching between blogs
- Account-specific defaults (labels, etc.)

Design pattern: Factory + Registry
- Factory creates clients per account
- Registry keeps track of available accounts
"""

from pathlib import Path
from typing import Dict, List, Optional

import yaml

from config import get_logger
from config.settings import AccountProfile, get_settings
from core.auth import Authenticator
from core.blogger_client import BloggerClient
from core.exceptions import ConfigurationError

logger = get_logger("core", "accounts")


class AccountManager:
    """
    Manages multiple Blogger account profiles and credentials.

    Usage:
        manager = AccountManager()
        client = manager.get_client("work")  # Get client for specific account
        client = manager.get_default_client()  # Get client for default account
        accounts = manager.list_accounts()  # List all accounts
    """

    def __init__(self, accounts_config_path: Optional[str] = None) -> None:
        """
        Initialize account manager.

        Args:
            accounts_config_path: Path to accounts.yaml config file
        """
        self._config_path = Path(accounts_config_path) if accounts_config_path else Path("config/accounts.yaml")
        self._accounts: Dict[str, AccountProfile] = {}
        self._client_cache: Dict[str, BloggerClient] = {}
        self._settings = None  # Lazy load settings
        self._load_accounts()

    def _load_accounts(self) -> None:
        """Load account profiles from config file."""
        if not self._config_path.exists():
            logger.debug(
                "No accounts.yaml found, using default account only",
                path=str(self._config_path),
            )
            return

        try:
            content = self._config_path.read_text()
            data = yaml.safe_load(content) or {}

            for acc in data.get("accounts", []):
                profile = AccountProfile(
                    name=acc["name"],
                    blog_id=acc["blog_id"],
                    credentials_path=acc.get("credentials_path", "credentials.storage"),
                    labels=acc.get("labels", []),
                )
                self._accounts[profile.name] = profile
                logger.debug("Loaded account profile", name=profile.name, blog_id=profile.blog_id)

        except Exception as e:
            logger.warning("Failed to load accounts config", error=str(e))

    def add_account(
        self,
        name: str,
        blog_id: str,
        credentials_path: str = "credentials.storage",
        labels: Optional[List[str]] = None,
    ) -> None:
        """
        Add an account profile programmatically.

        Args:
            name: Unique account identifier
            blog_id: Blogger blog ID
            credentials_path: Path to credentials file
            labels: Default labels for this account
        """
        profile = AccountProfile(
            name=name,
            blog_id=blog_id,
            credentials_path=credentials_path,
            labels=labels or [],
        )
        self._accounts[name] = profile
        logger.info("Added account profile", name=name, blog_id=blog_id)

    def list_accounts(self) -> List[AccountProfile]:
        """
        List all configured account profiles.

        Returns:
            List of AccountProfile objects
        """
        profiles = list(self._accounts.values())

        # Try to add default account if settings are available
        try:
            settings = get_settings()
            if not any(p.name == "default" for p in profiles):
                profiles.insert(0, AccountProfile(
                    name="default",
                    blog_id=settings.blogger_blog_id,
                    credentials_path=settings.google_credentials_storage_path,
                ))
        except Exception:
            # Settings not available (testing scenario)
            if not any(p.name == "default" for p in profiles):
                profiles.insert(0, AccountProfile(
                    name="default",
                    blog_id="",
                    credentials_path="credentials.storage",
                ))

        return profiles

    def get_client(self, account_name: str = "default") -> BloggerClient:
        """
        Get a BloggerClient for the specified account.

        Args:
            account_name: Name of the account profile

        Returns:
            Configured BloggerClient for the account

        Raises:
            ConfigurationError: If account not found
        """
        # Return cached client if available
        if account_name in self._client_cache:
            return self._client_cache[account_name]

        settings = get_settings()

        if account_name == "default":
            # Use default configuration
            credentials_path = Path(settings.google_credentials_storage_path)
            blog_id = settings.blogger_blog_id
        elif account_name in self._accounts:
            profile = self._accounts[account_name]
            credentials_path = Path(profile.credentials_path)
            blog_id = profile.blog_id
        else:
            raise ConfigurationError(
                f"Unknown account: {account_name}",
                details={"available_accounts": list(self._accounts.keys()) + ["default"]},
            )

        # Load credentials for this account
        authenticator = Authenticator(credentials_path=credentials_path)
        credentials = authenticator.load_credentials()

        # Create and cache client
        client = BloggerClient(blog_id=blog_id, credentials=credentials)
        self._client_cache[account_name] = client

        logger.info("Created BloggerClient for account", account=account_name, blog_id=blog_id)
        return client

    def get_active_client(self) -> BloggerClient:
        """
        Get the currently active account's BloggerClient.

        Uses settings.active_account to determine which account to use.
        Falls back to 'default' if not set.

        Returns:
            BloggerClient for active account
        """
        settings = get_settings()
        account_name = getattr(settings, "active_account", "default")
        return self.get_client(account_name)

    def validate_account(self, account_name: str) -> bool:
        """
        Validate that credentials exist for an account.

        Args:
            account_name: Account to validate

        Returns:
            True if account has valid credentials
        """
        settings = get_settings()

        if account_name == "default":
            credentials_path = Path(settings.google_credentials_storage_path)
        elif account_name in self._accounts:
            profile = self._accounts[account_name]
            credentials_path = Path(profile.credentials_path)
        else:
            return False

        if not credentials_path.exists():
            return False

        try:
            authenticator = Authenticator(credentials_path=credentials_path)
            return authenticator.validate_credentials()
        except Exception:
            return False