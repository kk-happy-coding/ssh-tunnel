"""Profile management service for SSH Tunnel Manager."""

import json
from pathlib import Path
from typing import List, Optional

from src.exceptions.custom_exceptions import ProfileError
from src.models.profile import Profile
from src.services.credential_store import CredentialStore
from src.utils.constants import PROFILES_DIR
from src.utils.crypto import CryptoManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ProfileService:
    """Service for managing connection profiles."""

    def __init__(self, encryption_password: Optional[str] = None) -> None:
        """
        Initialize profile service.

        Args:
            encryption_password: Password for encrypting profiles (optional)
        """
        self.profiles_dir = PROFILES_DIR
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

        self.credential_store = CredentialStore()
        self.crypto_manager: Optional[CryptoManager] = None

        if encryption_password:
            self.crypto_manager = CryptoManager(encryption_password)

    def save_profile(self, profile: Profile) -> None:
        """
        Save profile to disk.

        Args:
            profile: Profile to save

        Raises:
            ProfileError: If save fails
        """
        try:
            # Save credentials separately in secure storage
            if profile.connection.password:
                self.credential_store.store_password(
                    profile.connection.username,
                    profile.connection.host,
                    profile.connection.password,
                )

            if profile.connection.passphrase and profile.connection.key_file:
                self.credential_store.store_passphrase(
                    profile.connection.key_file,
                    profile.connection.passphrase,
                )

            # Get profile file path
            file_path = self._get_profile_path(profile.name)

            # Convert to JSON
            profile_json = profile.to_json()

            # Encrypt if crypto manager is available
            if self.crypto_manager:
                profile_json = self.crypto_manager.encrypt(profile_json)

            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(profile_json)

            logger.info(f"Saved profile: {profile.name}")

        except Exception as e:
            logger.error(f"Failed to save profile {profile.name}: {e}")
            raise ProfileError(f"Failed to save profile: {e}") from e

    def load_profile(self, name: str) -> Profile:
        """
        Load profile from disk.

        Args:
            name: Profile name

        Returns:
            Loaded profile

        Raises:
            ProfileError: If load fails
        """
        try:
            file_path = self._get_profile_path(name)

            if not file_path.exists():
                raise ProfileError(f"Profile '{name}' not found")

            # Read from file
            with open(file_path, "r", encoding="utf-8") as f:
                profile_data = f.read()

            # Decrypt if crypto manager is available
            if self.crypto_manager:
                try:
                    profile_data = self.crypto_manager.decrypt(profile_data)
                except Exception as e:
                    logger.error(f"Failed to decrypt profile: {e}")
                    raise ProfileError(f"Failed to decrypt profile (wrong password?): {e}") from e

            # Parse JSON
            profile = Profile.from_json(profile_data)

            # Load credentials from secure storage
            password = self.credential_store.retrieve_password(
                profile.connection.username,
                profile.connection.host,
            )
            if password:
                profile.connection.password = password

            if profile.connection.key_file:
                passphrase = self.credential_store.retrieve_passphrase(
                    profile.connection.key_file
                )
                if passphrase:
                    profile.connection.passphrase = passphrase

            logger.info(f"Loaded profile: {profile.name}")
            return profile

        except ProfileError:
            raise
        except Exception as e:
            logger.error(f"Failed to load profile {name}: {e}")
            raise ProfileError(f"Failed to load profile: {e}") from e

    def delete_profile(self, name: str) -> None:
        """
        Delete profile from disk.

        Args:
            name: Profile name

        Raises:
            ProfileError: If delete fails
        """
        try:
            file_path = self._get_profile_path(name)

            if not file_path.exists():
                raise ProfileError(f"Profile '{name}' not found")

            # Load profile to get credentials info
            try:
                profile = self.load_profile(name)
                # Delete stored credentials
                self.credential_store.delete_password(
                    profile.connection.username,
                    profile.connection.host,
                )
                if profile.connection.key_file:
                    self.credential_store.delete_passphrase(profile.connection.key_file)
            except Exception as e:
                logger.warning(f"Could not delete credentials for profile: {e}")

            # Delete file
            file_path.unlink()

            logger.info(f"Deleted profile: {name}")

        except ProfileError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete profile {name}: {e}")
            raise ProfileError(f"Failed to delete profile: {e}") from e

    def list_profiles(self) -> List[str]:
        """
        List all available profile names.

        Returns:
            List of profile names
        """
        try:
            profile_files = list(self.profiles_dir.glob("*.json"))
            return [f.stem for f in profile_files]
        except Exception as e:
            logger.error(f"Failed to list profiles: {e}")
            return []

    def profile_exists(self, name: str) -> bool:
        """
        Check if profile exists.

        Args:
            name: Profile name

        Returns:
            True if profile exists, False otherwise
        """
        file_path = self._get_profile_path(name)
        return file_path.exists()

    def export_profile(self, name: str, export_path: Path, include_credentials: bool = False) -> None:
        """
        Export profile to external file.

        Args:
            name: Profile name
            export_path: Path to export to
            include_credentials: Whether to include credentials

        Raises:
            ProfileError: If export fails
        """
        try:
            profile = self.load_profile(name)

            # Remove credentials if not included
            if not include_credentials:
                profile.connection.password = None
                profile.connection.passphrase = None

            # Save to export path
            export_path.parent.mkdir(parents=True, exist_ok=True)
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(profile.to_json())

            logger.info(f"Exported profile {name} to {export_path}")

        except Exception as e:
            logger.error(f"Failed to export profile: {e}")
            raise ProfileError(f"Failed to export profile: {e}") from e

    def import_profile(self, import_path: Path, new_name: Optional[str] = None) -> Profile:
        """
        Import profile from external file.

        Args:
            import_path: Path to import from
            new_name: New name for imported profile (optional)

        Returns:
            Imported profile

        Raises:
            ProfileError: If import fails
        """
        try:
            if not import_path.exists():
                raise ProfileError(f"Import file not found: {import_path}")

            # Load profile from file
            with open(import_path, "r", encoding="utf-8") as f:
                profile_json = f.read()

            profile = Profile.from_json(profile_json)

            # Rename if requested
            if new_name:
                profile.name = new_name

            # Check for name conflicts
            if self.profile_exists(profile.name):
                raise ProfileError(f"Profile '{profile.name}' already exists")

            # Save imported profile
            self.save_profile(profile)

            logger.info(f"Imported profile: {profile.name}")
            return profile

        except ProfileError:
            raise
        except Exception as e:
            logger.error(f"Failed to import profile: {e}")
            raise ProfileError(f"Failed to import profile: {e}") from e

    def _get_profile_path(self, name: str) -> Path:
        """
        Get file path for profile.

        Args:
            name: Profile name

        Returns:
            Path to profile file
        """
        # Sanitize name for filesystem
        safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-", "."))
        return self.profiles_dir / f"{safe_name}.json"
