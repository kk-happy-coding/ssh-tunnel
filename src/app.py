"""Application class for SSH Tunnel Manager."""

import logging
from typing import Optional

from src.core.ssh_manager import SSHManager
from src.core.tunnel_manager import TunnelManager
from src.core.tunnel_monitor import TunnelMonitor
from src.models.connection import Connection
from src.models.profile import Profile
from src.services.config_service import ConfigService
from src.services.profile_service import ProfileService
from src.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


class Application:
    """Main application class (non-GUI)."""

    def __init__(self) -> None:
        """Initialize application."""
        # Setup logging
        setup_logging(log_level=logging.INFO)

        # Services
        self.config_service = ConfigService()
        self.profile_service = ProfileService()

        # Connection state
        self.ssh_manager: Optional[SSHManager] = None
        self.tunnel_manager: Optional[TunnelManager] = None
        self.tunnel_monitor = TunnelMonitor()

        self.current_profile: Optional[Profile] = None

        logger.info("Application initialized")

    def connect(self, connection: Connection) -> None:
        """
        Connect to SSH server.

        Args:
            connection: Connection configuration
        """
        if self.ssh_manager and self.ssh_manager.is_connected():
            logger.warning("Already connected, disconnecting first")
            self.disconnect()

        logger.info(f"Connecting to {connection.get_connection_string()}")

        self.ssh_manager = SSHManager(connection)
        self.ssh_manager.connect()

        # Create tunnel manager
        transport = self.ssh_manager.get_transport()
        if transport:
            self.tunnel_manager = TunnelManager(transport)
            logger.info("Tunnel manager created")

        # Start monitoring
        self.tunnel_monitor.start_monitoring()

    def disconnect(self) -> None:
        """Disconnect from SSH server."""
        if not self.ssh_manager:
            logger.warning("Not connected")
            return

        logger.info("Disconnecting...")

        # Stop tunnels
        if self.tunnel_manager:
            self.tunnel_manager.stop_all_tunnels()

        # Stop monitoring
        self.tunnel_monitor.stop_monitoring()

        # Disconnect SSH
        self.ssh_manager.disconnect()
        self.ssh_manager = None
        self.tunnel_manager = None

        logger.info("Disconnected")

    def is_connected(self) -> bool:
        """
        Check if connected.

        Returns:
            True if connected, False otherwise
        """
        return self.ssh_manager is not None and self.ssh_manager.is_connected()

    def load_profile(self, profile_name: str) -> Profile:
        """
        Load profile.

        Args:
            profile_name: Profile name

        Returns:
            Loaded profile
        """
        logger.info(f"Loading profile: {profile_name}")
        profile = self.profile_service.load_profile(profile_name)
        self.current_profile = profile
        return profile

    def save_profile(self, profile: Profile) -> None:
        """
        Save profile.

        Args:
            profile: Profile to save
        """
        logger.info(f"Saving profile: {profile.name}")
        self.profile_service.save_profile(profile)
        self.current_profile = profile

    def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up...")

        try:
            self.disconnect()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

        logger.info("Cleanup complete")
