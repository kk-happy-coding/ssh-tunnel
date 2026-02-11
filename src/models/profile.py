"""Profile model for SSH Tunnel Manager."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from src.models.connection import Connection
from src.models.tunnel import Tunnel
from src.utils.validators import validate_profile_name


@dataclass
class Profile:
    """Profile containing connection and tunnel configurations."""

    name: str
    connection: Connection
    tunnels: List[Tunnel] = field(default_factory=list)
    auto_connect: bool = False
    auto_reconnect: bool = True
    created_at: Optional[float] = None
    modified_at: Optional[float] = None

    def __post_init__(self) -> None:
        """Validate profile after initialization."""
        # Validate profile name
        is_valid, error = validate_profile_name(self.name)
        if not is_valid:
            raise ValueError(f"Invalid profile name: {error}")

        # Set timestamps if not provided
        if self.created_at is None:
            import time
            self.created_at = time.time()
        if self.modified_at is None:
            self.modified_at = self.created_at

    def to_dict(self) -> dict:
        """
        Convert profile to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "connection": self.connection.to_dict(),
            "tunnels": [tunnel.to_dict() for tunnel in self.tunnels],
            "auto_connect": self.auto_connect,
            "auto_reconnect": self.auto_reconnect,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        """
        Create profile from dictionary.

        Args:
            data: Dictionary containing profile data

        Returns:
            Profile instance
        """
        # Convert connection
        connection_data = data.get("connection", {})
        connection = Connection.from_dict(connection_data)

        # Convert tunnels
        tunnels_data = data.get("tunnels", [])
        tunnels = [Tunnel.from_dict(tunnel_data) for tunnel_data in tunnels_data]

        return cls(
            name=data["name"],
            connection=connection,
            tunnels=tunnels,
            auto_connect=data.get("auto_connect", False),
            auto_reconnect=data.get("auto_reconnect", True),
            created_at=data.get("created_at"),
            modified_at=data.get("modified_at"),
        )

    def to_json(self) -> str:
        """
        Convert profile to JSON string.

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Profile":
        """
        Create profile from JSON string.

        Args:
            json_str: JSON string containing profile data

        Returns:
            Profile instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save(self, file_path: Path) -> None:
        """
        Save profile to file.

        Args:
            file_path: Path to save profile to
        """
        import time

        self.modified_at = time.time()

        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, file_path: Path) -> "Profile":
        """
        Load profile from file.

        Args:
            file_path: Path to load profile from

        Returns:
            Profile instance
        """
        with open(file_path, "r", encoding="utf-8") as f:
            json_str = f.read()
        return cls.from_json(json_str)

    def add_tunnel(self, tunnel: Tunnel) -> None:
        """
        Add tunnel to profile.

        Args:
            tunnel: Tunnel to add
        """
        if tunnel not in self.tunnels:
            self.tunnels.append(tunnel)
            import time
            self.modified_at = time.time()

    def remove_tunnel(self, tunnel: Tunnel) -> bool:
        """
        Remove tunnel from profile.

        Args:
            tunnel: Tunnel to remove

        Returns:
            True if tunnel was removed, False if not found
        """
        try:
            self.tunnels.remove(tunnel)
            import time
            self.modified_at = time.time()
            return True
        except ValueError:
            return False

    def get_tunnel_by_name(self, name: str) -> Optional[Tunnel]:
        """
        Get tunnel by name.

        Args:
            name: Tunnel name to search for

        Returns:
            Tunnel if found, None otherwise
        """
        for tunnel in self.tunnels:
            if tunnel.name == name:
                return tunnel
        return None

    def __str__(self) -> str:
        """String representation of profile."""
        tunnel_count = len(self.tunnels)
        return f"{self.name} ({self.connection.get_connection_string()}, {tunnel_count} tunnels)"

    def __eq__(self, other: object) -> bool:
        """Check equality based on profile name."""
        if not isinstance(other, Profile):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        """Hash based on profile name."""
        return hash(self.name)
