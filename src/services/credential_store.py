"""Secure credential storage using Windows Credential Manager."""

from typing import Optional

try:
    import keyring
    from keyring.errors import KeyringError

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    KeyringError = Exception  # type: ignore

from src.exceptions.custom_exceptions import ConfigError
from src.utils.constants import CREDENTIAL_SERVICE_NAME
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CredentialStore:
    """Manager for secure credential storage."""

    def __init__(self) -> None:
        """Initialize credential store."""
        if not KEYRING_AVAILABLE:
            logger.warning("Keyring library not available, credentials will not be stored securely")

        self.service_name = CREDENTIAL_SERVICE_NAME

    def store_password(self, username: str, host: str, password: str) -> None:
        """
        Store password securely.

        Args:
            username: SSH username
            host: SSH host
            password: Password to store

        Raises:
            ConfigError: If storage fails
        """
        if not KEYRING_AVAILABLE:
            logger.warning("Cannot store password securely: keyring not available")
            return

        key = self._make_key(username, host)

        try:
            keyring.set_password(self.service_name, key, password)
            logger.debug(f"Stored password for {username}@{host}")
        except KeyringError as e:
            logger.error(f"Failed to store password: {e}")
            raise ConfigError(f"Failed to store password: {e}") from e

    def retrieve_password(self, username: str, host: str) -> Optional[str]:
        """
        Retrieve stored password.

        Args:
            username: SSH username
            host: SSH host

        Returns:
            Stored password, or None if not found
        """
        if not KEYRING_AVAILABLE:
            logger.warning("Cannot retrieve password: keyring not available")
            return None

        key = self._make_key(username, host)

        try:
            password = keyring.get_password(self.service_name, key)
            if password:
                logger.debug(f"Retrieved password for {username}@{host}")
            return password
        except KeyringError as e:
            logger.error(f"Failed to retrieve password: {e}")
            return None

    def delete_password(self, username: str, host: str) -> None:
        """
        Delete stored password.

        Args:
            username: SSH username
            host: SSH host
        """
        if not KEYRING_AVAILABLE:
            return

        key = self._make_key(username, host)

        try:
            keyring.delete_password(self.service_name, key)
            logger.debug(f"Deleted password for {username}@{host}")
        except KeyringError as e:
            logger.debug(f"Could not delete password (may not exist): {e}")

    def store_passphrase(self, key_file: str, passphrase: str) -> None:
        """
        Store key file passphrase securely.

        Args:
            key_file: Path to key file
            passphrase: Passphrase to store

        Raises:
            ConfigError: If storage fails
        """
        if not KEYRING_AVAILABLE:
            logger.warning("Cannot store passphrase securely: keyring not available")
            return

        key = f"keyfile:{key_file}"

        try:
            keyring.set_password(self.service_name, key, passphrase)
            logger.debug(f"Stored passphrase for key file")
        except KeyringError as e:
            logger.error(f"Failed to store passphrase: {e}")
            raise ConfigError(f"Failed to store passphrase: {e}") from e

    def retrieve_passphrase(self, key_file: str) -> Optional[str]:
        """
        Retrieve stored passphrase.

        Args:
            key_file: Path to key file

        Returns:
            Stored passphrase, or None if not found
        """
        if not KEYRING_AVAILABLE:
            logger.warning("Cannot retrieve passphrase: keyring not available")
            return None

        key = f"keyfile:{key_file}"

        try:
            passphrase = keyring.get_password(self.service_name, key)
            if passphrase:
                logger.debug(f"Retrieved passphrase for key file")
            return passphrase
        except KeyringError as e:
            logger.error(f"Failed to retrieve passphrase: {e}")
            return None

    def delete_passphrase(self, key_file: str) -> None:
        """
        Delete stored passphrase.

        Args:
            key_file: Path to key file
        """
        if not KEYRING_AVAILABLE:
            return

        key = f"keyfile:{key_file}"

        try:
            keyring.delete_password(self.service_name, key)
            logger.debug(f"Deleted passphrase for key file")
        except KeyringError as e:
            logger.debug(f"Could not delete passphrase (may not exist): {e}")

    def clear_all_credentials(self) -> None:
        """Clear all stored credentials (for cleanup/testing)."""
        logger.warning("Clearing all stored credentials")
        # Note: keyring doesn't provide a way to list all keys,
        # so we can't implement a complete clear operation

    def _make_key(self, username: str, host: str) -> str:
        """
        Create credential key.

        Args:
            username: SSH username
            host: SSH host

        Returns:
            Credential key
        """
        return f"{username}@{host}"

    def is_available(self) -> bool:
        """
        Check if credential store is available.

        Returns:
            True if keyring is available, False otherwise
        """
        return KEYRING_AVAILABLE

    def __del__(self) -> None:
        """Cleanup on deletion."""
        # Credentials are securely stored in system keyring, no cleanup needed
        pass
