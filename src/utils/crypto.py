"""Cryptographic utilities for SSH Tunnel Manager."""

import base64
import os
from typing import Union

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


class CryptoManager:
    """Manager for encryption and decryption operations."""

    def __init__(self, password: str) -> None:
        """
        Initialize crypto manager with a password.

        Args:
            password: Password for encryption/decryption
        """
        self.password = password.encode()
        self._fernet: Union[Fernet, None] = None

    def _get_fernet(self, salt: bytes) -> Fernet:
        """
        Get Fernet instance with derived key.

        Args:
            salt: Salt for key derivation

        Returns:
            Fernet instance
        """
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password))
        return Fernet(key)

    def encrypt(self, data: str) -> str:
        """
        Encrypt data.

        Args:
            data: Plain text data to encrypt

        Returns:
            Base64-encoded encrypted data with salt
        """
        # Generate random salt
        salt = os.urandom(16)

        # Get Fernet instance
        fernet = self._get_fernet(salt)

        # Encrypt data
        encrypted = fernet.encrypt(data.encode())

        # Combine salt and encrypted data
        result = base64.b64encode(salt + encrypted).decode()

        return result

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data.

        Args:
            encrypted_data: Base64-encoded encrypted data with salt

        Returns:
            Decrypted plain text

        Raises:
            ValueError: If decryption fails
        """
        try:
            # Decode from base64
            combined = base64.b64decode(encrypted_data.encode())

            # Extract salt and encrypted data
            salt = combined[:16]
            encrypted = combined[16:]

            # Get Fernet instance
            fernet = self._get_fernet(salt)

            # Decrypt data
            decrypted = fernet.decrypt(encrypted)

            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}") from e

    def __del__(self) -> None:
        """Clean up sensitive data from memory."""
        if hasattr(self, "password"):
            # Overwrite password in memory
            self.password = b"\x00" * len(self.password)


def generate_key() -> str:
    """
    Generate a random encryption key.

    Returns:
        Base64-encoded key
    """
    return Fernet.generate_key().decode()


def hash_password(password: str, salt: Union[bytes, None] = None) -> Tuple[str, str]:
    """
    Hash a password using PBKDF2.

    Args:
        password: Password to hash
        salt: Salt for hashing (generated if None)

    Returns:
        Tuple of (hash, salt) as base64-encoded strings
    """
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend(),
    )

    key = kdf.derive(password.encode())

    return base64.b64encode(key).decode(), base64.b64encode(salt).decode()


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        password: Password to verify
        password_hash: Expected password hash (base64-encoded)
        salt: Salt used for hashing (base64-encoded)

    Returns:
        True if password matches, False otherwise
    """
    try:
        salt_bytes = base64.b64decode(salt.encode())
        computed_hash, _ = hash_password(password, salt_bytes)
        return computed_hash == password_hash
    except Exception:
        return False


# Import Tuple for type hint
from typing import Tuple
