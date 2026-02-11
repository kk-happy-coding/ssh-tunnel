"""Custom exception classes for SSH Tunnel Manager."""


class SSHTunnelError(Exception):
    """Base exception for SSH Tunnel Manager."""

    pass


class ConnectionError(SSHTunnelError):
    """Exception raised for SSH connection errors."""

    pass


class AuthenticationError(SSHTunnelError):
    """Exception raised for SSH authentication failures."""

    pass


class TunnelError(SSHTunnelError):
    """Exception raised for tunnel operation errors."""

    pass


class PortConflictError(TunnelError):
    """Exception raised when a port is already in use."""

    def __init__(self, port: int, message: str = "") -> None:
        """
        Initialize port conflict error.

        Args:
            port: Port number that is in conflict
            message: Additional error message
        """
        self.port = port
        if not message:
            message = f"Port {port} is already in use"
        super().__init__(message)


class ProfileError(SSHTunnelError):
    """Exception raised for profile operation errors."""

    pass


class ConfigError(SSHTunnelError):
    """Exception raised for configuration errors."""

    pass


class ValidationError(SSHTunnelError):
    """Exception raised for input validation errors."""

    def __init__(self, field: str, message: str) -> None:
        """
        Initialize validation error.

        Args:
            field: Field name that failed validation
            message: Validation error message
        """
        self.field = field
        super().__init__(f"{field}: {message}")


class KeyFileError(AuthenticationError):
    """Exception raised for key file errors."""

    pass


class TimeoutError(ConnectionError):
    """Exception raised for connection timeout."""

    pass


class NetworkError(ConnectionError):
    """Exception raised for network-related errors."""

    pass
