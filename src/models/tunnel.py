"""Tunnel model for SSH Tunnel Manager."""

import time
from dataclasses import dataclass, field
from typing import Optional

from src.utils.constants import DEFAULT_BIND_ADDRESS, TunnelStatus, TunnelType
from src.utils.validators import validate_host, validate_port, validate_tunnel_name


@dataclass
class Tunnel:
    """SSH tunnel configuration."""

    tunnel_type: TunnelType
    local_port: int
    remote_host: str = "localhost"
    remote_port: int = 0
    bind_address: str = DEFAULT_BIND_ADDRESS
    name: str = ""
    status: TunnelStatus = TunnelStatus.IDLE
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    bytes_sent: int = 0
    bytes_received: int = 0
    reconnect_count: int = 0

    def __post_init__(self) -> None:
        """Validate tunnel parameters after initialization."""
        # Validate local port
        is_valid, error = validate_port(self.local_port)
        if not is_valid:
            raise ValueError(f"Invalid local port: {error}")

        # Validate remote port for local and remote tunnels
        if self.tunnel_type in (TunnelType.LOCAL, TunnelType.REMOTE):
            if self.remote_port == 0:
                raise ValueError("Remote port is required for local/remote tunnels")
            is_valid, error = validate_port(self.remote_port)
            if not is_valid:
                raise ValueError(f"Invalid remote port: {error}")

        # Validate remote host
        if self.tunnel_type == TunnelType.LOCAL:
            is_valid, error = validate_host(self.remote_host)
            if not is_valid:
                raise ValueError(f"Invalid remote host: {error}")

        # Validate bind address
        if self.bind_address:
            is_valid, error = validate_host(self.bind_address)
            if not is_valid:
                raise ValueError(f"Invalid bind address: {error}")

        # Validate tunnel name
        if self.name:
            is_valid, error = validate_tunnel_name(self.name)
            if not is_valid:
                raise ValueError(f"Invalid tunnel name: {error}")

        # Generate default name if not provided
        if not self.name:
            self.name = self._generate_default_name()

    def _generate_default_name(self) -> str:
        """
        Generate default tunnel name.

        Returns:
            Generated tunnel name
        """
        if self.tunnel_type == TunnelType.LOCAL:
            return f"Local {self.local_port}→{self.remote_host}:{self.remote_port}"
        elif self.tunnel_type == TunnelType.REMOTE:
            return f"Remote {self.remote_port}→{self.remote_host}:{self.local_port}"
        else:  # DYNAMIC
            return f"SOCKS5 :{self.local_port}"

    def to_dict(self) -> dict:
        """
        Convert tunnel to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "tunnel_type": self.tunnel_type.value,
            "local_port": self.local_port,
            "remote_host": self.remote_host,
            "remote_port": self.remote_port,
            "bind_address": self.bind_address,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tunnel":
        """
        Create tunnel from dictionary.

        Args:
            data: Dictionary containing tunnel data

        Returns:
            Tunnel instance
        """
        # Convert tunnel_type string to enum
        if "tunnel_type" in data and isinstance(data["tunnel_type"], str):
            data["tunnel_type"] = TunnelType(data["tunnel_type"])

        return cls(**data)

    def get_ssh_command_args(self) -> str:
        """
        Get SSH command arguments for this tunnel.

        Returns:
            SSH command arguments (e.g., "-L 8080:localhost:80")
        """
        if self.tunnel_type == TunnelType.LOCAL:
            return f"-L {self.bind_address}:{self.local_port}:{self.remote_host}:{self.remote_port}"
        elif self.tunnel_type == TunnelType.REMOTE:
            return f"-R {self.remote_port}:{self.remote_host}:{self.local_port}"
        else:  # DYNAMIC
            return f"-D {self.bind_address}:{self.local_port}"

    def get_uptime(self) -> Optional[float]:
        """
        Get tunnel uptime in seconds.

        Returns:
            Uptime in seconds, or None if not started
        """
        if self.start_time is None:
            return None
        return time.time() - self.start_time

    def get_uptime_string(self) -> str:
        """
        Get formatted uptime string.

        Returns:
            Formatted uptime (e.g., "1h 23m 45s")
        """
        uptime = self.get_uptime()
        if uptime is None:
            return "N/A"

        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)

        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")

        return " ".join(parts)

    def format_bytes(self, bytes_count: int) -> str:
        """
        Format byte count to human-readable string.

        Args:
            bytes_count: Number of bytes

        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} PB"

    def get_bytes_sent_string(self) -> str:
        """Get formatted bytes sent string."""
        return self.format_bytes(self.bytes_sent)

    def get_bytes_received_string(self) -> str:
        """Get formatted bytes received string."""
        return self.format_bytes(self.bytes_received)

    def __str__(self) -> str:
        """String representation of tunnel."""
        return self.name

    def __eq__(self, other: object) -> bool:
        """Check equality based on tunnel configuration."""
        if not isinstance(other, Tunnel):
            return False
        return (
            self.tunnel_type == other.tunnel_type
            and self.local_port == other.local_port
            and self.remote_host == other.remote_host
            and self.remote_port == other.remote_port
        )

    def __hash__(self) -> int:
        """Hash based on tunnel configuration."""
        return hash((self.tunnel_type, self.local_port, self.remote_host, self.remote_port))
