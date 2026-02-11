"""Constants and enumerations for SSH Tunnel Manager."""

from enum import Enum
from pathlib import Path
from typing import Final

# Application metadata
APP_NAME: Final[str] = "SSH Tunnel Manager"
APP_VERSION: Final[str] = "1.0.0"

# Directory paths
CONFIG_DIR: Final[Path] = Path.home() / ".ssh-tunnel-manager"
LOG_DIR: Final[Path] = CONFIG_DIR / "logs"
PROFILES_DIR: Final[Path] = CONFIG_DIR / "profiles"
KNOWN_HOSTS_FILE: Final[Path] = CONFIG_DIR / "known_hosts"

# Default values
DEFAULT_SSH_PORT: Final[int] = 22
DEFAULT_CONNECTION_TIMEOUT: Final[int] = 10
DEFAULT_KEEPALIVE_INTERVAL: Final[int] = 30
DEFAULT_RECONNECT_DELAY: Final[int] = 1
DEFAULT_MAX_RECONNECT_ATTEMPTS: Final[int] = 5
DEFAULT_HEARTBEAT_INTERVAL: Final[int] = 15
DEFAULT_BIND_ADDRESS: Final[str] = "127.0.0.1"

# Limits and constraints
MAX_PORT: Final[int] = 65535
MIN_PORT: Final[int] = 1
MAX_HOSTNAME_LENGTH: Final[int] = 253
MAX_USERNAME_LENGTH: Final[int] = 32
MAX_PASSWORD_LENGTH: Final[int] = 256
MAX_PROFILE_NAME_LENGTH: Final[int] = 64
MAX_TUNNEL_NAME_LENGTH: Final[int] = 32
MAX_KEY_FILE_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB
MAX_RECENT_CONNECTIONS: Final[int] = 10

# Logging
LOG_FILE_MAX_BYTES: Final[int] = 5 * 1024 * 1024  # 5MB
LOG_FILE_BACKUP_COUNT: Final[int] = 5
LOG_FORMAT: Final[str] = "[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s"
LOG_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

# Security
CREDENTIAL_SERVICE_NAME: Final[str] = "ssh-tunnel-manager"
PASSWORD_REDACTED: Final[str] = "***REDACTED***"

# GUI
WINDOW_MIN_WIDTH: Final[int] = 1000
WINDOW_MIN_HEIGHT: Final[int] = 700
WINDOW_DEFAULT_WIDTH: Final[int] = 1200
WINDOW_DEFAULT_HEIGHT: Final[int] = 800

# Network timeouts
CONNECTION_TEST_TIMEOUT: Final[int] = 5
PORT_CHECK_TIMEOUT: Final[int] = 1

# Retry configuration
MAX_RECONNECT_BACKOFF: Final[int] = 60  # seconds


class ConnectionStatus(Enum):
    """SSH connection status enumeration."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class TunnelStatus(Enum):
    """SSH tunnel status enumeration."""

    IDLE = "idle"
    CONNECTING = "connecting"
    ACTIVE = "active"
    ERROR = "error"
    RECONNECTING = "reconnecting"
    STOPPED = "stopped"


class TunnelType(Enum):
    """SSH tunnel type enumeration."""

    LOCAL = "local"
    REMOTE = "remote"
    DYNAMIC = "dynamic"


class AuthMethod(Enum):
    """SSH authentication method enumeration."""

    PASSWORD = "password"
    KEY_FILE = "key_file"
    KEY_WITH_PASSPHRASE = "key_with_passphrase"
    SSH_AGENT = "ssh_agent"


class Theme(Enum):
    """Application theme enumeration."""

    LIGHT = "light"
    DARK = "dark"
