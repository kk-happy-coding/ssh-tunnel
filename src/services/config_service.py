"""Configuration service for SSH Tunnel Manager."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from src.exceptions.custom_exceptions import ConfigError
from src.utils.constants import (
    CONFIG_DIR,
    DEFAULT_CONNECTION_TIMEOUT,
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_KEEPALIVE_INTERVAL,
    DEFAULT_MAX_RECONNECT_ATTEMPTS,
    DEFAULT_RECONNECT_DELAY,
    MAX_RECENT_CONNECTIONS,
    Theme,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigService:
    """Service for managing application configuration."""

    DEFAULT_CONFIG = {
        "theme": Theme.LIGHT.value,
        "auto_connect_on_startup": False,
        "remember_window_position": True,
        "remember_window_size": True,
        "window_x": 100,
        "window_y": 100,
        "window_width": 1200,
        "window_height": 800,
        "log_level": "INFO",
        "max_recent_connections": MAX_RECENT_CONNECTIONS,
        "recent_connections": [],
        "connection_timeout": DEFAULT_CONNECTION_TIMEOUT,
        "keepalive_interval": DEFAULT_KEEPALIVE_INTERVAL,
        "heartbeat_interval": DEFAULT_HEARTBEAT_INTERVAL,
        "max_reconnect_attempts": DEFAULT_MAX_RECONNECT_ATTEMPTS,
        "reconnect_delay": DEFAULT_RECONNECT_DELAY,
        "auto_reconnect": True,
        "show_notifications": True,
        "minimize_to_tray": True,
        "start_minimized": False,
        "confirm_on_exit": True,
        "check_for_updates": True,
        "last_update_check": None,
    }

    def __init__(self, config_file: Optional[Path] = None) -> None:
        """
        Initialize configuration service.

        Args:
            config_file: Path to config file (optional, uses default if not provided)
        """
        if config_file is None:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            config_file = CONFIG_DIR / "config.json"

        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)

                # Merge with defaults (in case new config keys were added)
                self.config = self.DEFAULT_CONFIG.copy()
                self.config.update(loaded_config)

                logger.info(f"Loaded configuration from {self.config_file}")
            else:
                # Use defaults
                self.config = self.DEFAULT_CONFIG.copy()
                logger.info("Using default configuration")
                # Save defaults
                self.save()

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self.config = self.DEFAULT_CONFIG.copy()

    def save(self) -> None:
        """
        Save configuration to file.

        Raises:
            ConfigError: If save fails
        """
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)

            logger.debug("Saved configuration")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise ConfigError(f"Failed to save configuration: {e}") from e

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
        logger.debug(f"Set config: {key} = {value}")

    def get_theme(self) -> Theme:
        """
        Get application theme.

        Returns:
            Theme enum
        """
        theme_value = self.get("theme", Theme.LIGHT.value)
        try:
            return Theme(theme_value)
        except ValueError:
            return Theme.LIGHT

    def set_theme(self, theme: Theme) -> None:
        """
        Set application theme.

        Args:
            theme: Theme enum
        """
        self.set("theme", theme.value)

    def add_recent_connection(self, connection_string: str) -> None:
        """
        Add connection to recent connections list.

        Args:
            connection_string: Connection string (user@host:port)
        """
        recent = self.get("recent_connections", [])

        # Remove if already exists
        if connection_string in recent:
            recent.remove(connection_string)

        # Add to front
        recent.insert(0, connection_string)

        # Limit size
        max_recent = self.get("max_recent_connections", MAX_RECENT_CONNECTIONS)
        recent = recent[:max_recent]

        self.set("recent_connections", recent)

    def get_recent_connections(self) -> list:
        """
        Get recent connections list.

        Returns:
            List of recent connection strings
        """
        return self.get("recent_connections", [])

    def clear_recent_connections(self) -> None:
        """Clear recent connections list."""
        self.set("recent_connections", [])

    def get_window_geometry(self) -> tuple:
        """
        Get saved window geometry.

        Returns:
            Tuple of (x, y, width, height)
        """
        x = self.get("window_x", 100)
        y = self.get("window_y", 100)
        width = self.get("window_width", 1200)
        height = self.get("window_height", 800)
        return (x, y, width, height)

    def set_window_geometry(self, x: int, y: int, width: int, height: int) -> None:
        """
        Save window geometry.

        Args:
            x: Window x position
            y: Window y position
            width: Window width
            height: Window height
        """
        if self.get("remember_window_position"):
            self.set("window_x", x)
            self.set("window_y", y)

        if self.get("remember_window_size"):
            self.set("window_width", width)
            self.set("window_height", height)

    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
        logger.info("Reset configuration to defaults")

    def export_config(self, export_path: Path) -> None:
        """
        Export configuration to file.

        Args:
            export_path: Path to export to

        Raises:
            ConfigError: If export fails
        """
        try:
            export_path.parent.mkdir(parents=True, exist_ok=True)

            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)

            logger.info(f"Exported configuration to {export_path}")

        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            raise ConfigError(f"Failed to export configuration: {e}") from e

    def import_config(self, import_path: Path) -> None:
        """
        Import configuration from file.

        Args:
            import_path: Path to import from

        Raises:
            ConfigError: If import fails
        """
        try:
            if not import_path.exists():
                raise ConfigError(f"Import file not found: {import_path}")

            with open(import_path, "r", encoding="utf-8") as f:
                imported_config = json.load(f)

            # Merge with defaults
            self.config = self.DEFAULT_CONFIG.copy()
            self.config.update(imported_config)

            self.save()

            logger.info(f"Imported configuration from {import_path}")

        except ConfigError:
            raise
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            raise ConfigError(f"Failed to import configuration: {e}") from e
