"""Custom exceptions for SSH Tunnel Manager."""

from src.exceptions.custom_exceptions import (
    AuthenticationError,
    ConfigError,
    ConnectionError,
    PortConflictError,
    ProfileError,
    SSHTunnelError,
    TunnelError,
    ValidationError,
)

__all__ = [
    "SSHTunnelError",
    "ConnectionError",
    "AuthenticationError",
    "TunnelError",
    "PortConflictError",
    "ProfileError",
    "ConfigError",
    "ValidationError",
]
