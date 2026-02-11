"""Connection model for SSH Tunnel Manager."""

from dataclasses import dataclass, field
from typing import Optional

from src.utils.constants import (
    DEFAULT_CONNECTION_TIMEOUT,
    DEFAULT_KEEPALIVE_INTERVAL,
    DEFAULT_SSH_PORT,
    AuthMethod,
    ConnectionStatus,
)
from src.utils.validators import (
    validate_host,
    validate_key_file,
    validate_password,
    validate_port,
    validate_username,
)


@dataclass
class Connection:
    """SSH connection configuration."""

    host: str
    port: int = DEFAULT_SSH_PORT
    username: str = ""
    password: Optional[str] = None
    key_file: Optional[str] = None
    passphrase: Optional[str] = None
    auth_method: AuthMethod = AuthMethod.PASSWORD
    timeout: int = DEFAULT_CONNECTION_TIMEOUT
    keepalive_interval: int = DEFAULT_KEEPALIVE_INTERVAL
    use_ssh_agent: bool = False
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    server_fingerprint: Optional[str] = None
    server_banner: Optional[str] = None
    connection_time: Optional[float] = None

    def __post_init__(self) -> None:
        """Validate connection parameters after initialization."""
        # Validate host
        is_valid, error = validate_host(self.host)
        if not is_valid:
            raise ValueError(f"Invalid host: {error}")

        # Validate port
        is_valid, error = validate_port(self.port)
        if not is_valid:
            raise ValueError(f"Invalid port: {error}")

        # Validate username
        if self.username:
            is_valid, error = validate_username(self.username)
            if not is_valid:
                raise ValueError(f"Invalid username: {error}")

        # Validate authentication based on method
        if self.auth_method == AuthMethod.PASSWORD:
            if not self.password:
                raise ValueError("Password is required for password authentication")
            is_valid, error = validate_password(self.password)
            if not is_valid:
                raise ValueError(f"Invalid password: {error}")

        elif self.auth_method in (AuthMethod.KEY_FILE, AuthMethod.KEY_WITH_PASSPHRASE):
            if not self.key_file:
                raise ValueError("Key file is required for key-based authentication")
            is_valid, error = validate_key_file(self.key_file)
            if not is_valid:
                raise ValueError(f"Invalid key file: {error}")

            if self.auth_method == AuthMethod.KEY_WITH_PASSPHRASE and not self.passphrase:
                raise ValueError("Passphrase is required for key with passphrase authentication")

    def to_dict(self) -> dict:
        """
        Convert connection to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "auth_method": self.auth_method.value,
            "key_file": self.key_file,
            "timeout": self.timeout,
            "keepalive_interval": self.keepalive_interval,
            "use_ssh_agent": self.use_ssh_agent,
            "server_fingerprint": self.server_fingerprint,
            "server_banner": self.server_banner,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Connection":
        """
        Create connection from dictionary.

        Args:
            data: Dictionary containing connection data

        Returns:
            Connection instance
        """
        # Convert auth_method string to enum
        if "auth_method" in data and isinstance(data["auth_method"], str):
            data["auth_method"] = AuthMethod(data["auth_method"])

        # Filter out password and passphrase (loaded separately from credential store)
        filtered_data = {k: v for k, v in data.items() if k not in ("password", "passphrase")}

        return cls(**filtered_data)

    def get_connection_string(self) -> str:
        """
        Get connection string representation.

        Returns:
            Connection string (e.g., "user@host:port")
        """
        if self.username:
            return f"{self.username}@{self.host}:{self.port}"
        return f"{self.host}:{self.port}"

    def __str__(self) -> str:
        """String representation of connection."""
        return self.get_connection_string()

    def __eq__(self, other: object) -> bool:
        """Check equality based on host, port, and username."""
        if not isinstance(other, Connection):
            return False
        return (
            self.host == other.host
            and self.port == other.port
            and self.username == other.username
        )

    def __hash__(self) -> int:
        """Hash based on host, port, and username."""
        return hash((self.host, self.port, self.username))
