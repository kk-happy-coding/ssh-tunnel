"""SSH connection management for SSH Tunnel Manager."""

import hashlib
import os
import socket
import threading
import time
from pathlib import Path
from typing import Optional

import paramiko

from src.exceptions.custom_exceptions import AuthenticationError, ConnectionError, TimeoutError
from src.models.connection import Connection
from src.utils.constants import (
    KNOWN_HOSTS_FILE,
    AuthMethod,
    ConnectionStatus,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SSHManager:
    """Manager for SSH connections using Paramiko."""

    def __init__(self, connection: Connection) -> None:
        """
        Initialize SSH manager.

        Args:
            connection: Connection configuration
        """
        self.connection = connection
        self.client: Optional[paramiko.SSHClient] = None
        self.transport: Optional[paramiko.Transport] = None
        self._lock = threading.Lock()
        self._keepalive_thread: Optional[threading.Thread] = None
        self._keepalive_running = False

    def connect(self) -> None:
        """
        Establish SSH connection.

        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
            TimeoutError: If connection times out
        """
        with self._lock:
            if self.is_connected():
                logger.warning("Already connected")
                return

            logger.info(f"Connecting to {self.connection.get_connection_string()}")
            self.connection.status = ConnectionStatus.CONNECTING

            try:
                # Create SSH client
                self.client = paramiko.SSHClient()

                # Load system host keys
                try:
                    self.client.load_system_host_keys()
                except Exception as e:
                    logger.debug(f"Could not load system host keys: {e}")

                # Load known hosts file
                if KNOWN_HOSTS_FILE.exists():
                    try:
                        self.client.load_host_keys(str(KNOWN_HOSTS_FILE))
                    except Exception as e:
                        logger.debug(f"Could not load known hosts file: {e}")

                # Set policy for unknown hosts
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # Prepare connection parameters
                connect_kwargs = {
                    "hostname": self.connection.host,
                    "port": self.connection.port,
                    "username": self.connection.username,
                    "timeout": self.connection.timeout,
                    "allow_agent": self.connection.use_ssh_agent,
                    "look_for_keys": self.connection.use_ssh_agent,
                }

                # Add authentication based on method
                if self.connection.auth_method == AuthMethod.PASSWORD:
                    connect_kwargs["password"] = self.connection.password

                elif self.connection.auth_method == AuthMethod.KEY_FILE:
                    connect_kwargs["key_filename"] = self.connection.key_file
                    connect_kwargs["allow_agent"] = False
                    connect_kwargs["look_for_keys"] = False

                elif self.connection.auth_method == AuthMethod.KEY_WITH_PASSPHRASE:
                    connect_kwargs["key_filename"] = self.connection.key_file
                    connect_kwargs["passphrase"] = self.connection.passphrase
                    connect_kwargs["allow_agent"] = False
                    connect_kwargs["look_for_keys"] = False

                elif self.connection.auth_method == AuthMethod.SSH_AGENT:
                    connect_kwargs["allow_agent"] = True
                    connect_kwargs["look_for_keys"] = True

                # Connect
                self.client.connect(**connect_kwargs)

                # Get transport
                self.transport = self.client.get_transport()
                if self.transport is None:
                    raise ConnectionError("Failed to get transport from SSH client")

                # Get server info
                self.connection.server_banner = self.transport.remote_version
                server_key = self.transport.get_remote_server_key()
                key_bytes = server_key.get_fingerprint()
                self.connection.server_fingerprint = hashlib.sha256(key_bytes).hexdigest()

                # Set keepalive
                self.transport.set_keepalive(self.connection.keepalive_interval)

                # Start keepalive thread
                self._start_keepalive_thread()

                # Update connection status
                self.connection.status = ConnectionStatus.CONNECTED
                self.connection.connection_time = time.time()

                logger.info(f"Successfully connected to {self.connection.get_connection_string()}")
                logger.debug(f"Server banner: {self.connection.server_banner}")
                logger.debug(f"Server fingerprint: {self.connection.server_fingerprint}")

                # Save host key
                self._save_host_key()

            except paramiko.AuthenticationException as e:
                self.connection.status = ConnectionStatus.ERROR
                logger.error(f"Authentication failed: {e}")
                raise AuthenticationError(f"Authentication failed: {e}") from e

            except socket.timeout as e:
                self.connection.status = ConnectionStatus.ERROR
                logger.error(f"Connection timed out: {e}")
                raise TimeoutError(f"Connection timed out after {self.connection.timeout}s") from e

            except socket.gaierror as e:
                self.connection.status = ConnectionStatus.ERROR
                logger.error(f"DNS resolution failed: {e}")
                raise ConnectionError(f"Could not resolve hostname: {e}") from e

            except paramiko.SSHException as e:
                self.connection.status = ConnectionStatus.ERROR
                logger.error(f"SSH error: {e}")
                raise ConnectionError(f"SSH connection failed: {e}") from e

            except Exception as e:
                self.connection.status = ConnectionStatus.ERROR
                logger.error(f"Connection failed: {e}")
                raise ConnectionError(f"Connection failed: {e}") from e

    def disconnect(self) -> None:
        """Disconnect SSH connection."""
        with self._lock:
            if not self.is_connected():
                logger.debug("Not connected, nothing to disconnect")
                return

            logger.info(f"Disconnecting from {self.connection.get_connection_string()}")

            # Stop keepalive thread
            self._stop_keepalive_thread()

            # Close client
            try:
                if self.client:
                    self.client.close()
                    self.client = None
                self.transport = None
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")

            self.connection.status = ConnectionStatus.DISCONNECTED
            self.connection.connection_time = None

            logger.info("Disconnected successfully")

    def is_connected(self) -> bool:
        """
        Check if SSH connection is active.

        Returns:
            True if connected, False otherwise
        """
        if self.client is None or self.transport is None:
            return False

        try:
            return self.transport.is_active()
        except Exception:
            return False

    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Test SSH connection without establishing full connection.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Create temporary client
            test_client = paramiko.SSHClient()
            test_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Prepare connection parameters
            connect_kwargs = {
                "hostname": self.connection.host,
                "port": self.connection.port,
                "username": self.connection.username,
                "timeout": self.connection.timeout,
                "allow_agent": False,
                "look_for_keys": False,
            }

            # Add authentication
            if self.connection.auth_method == AuthMethod.PASSWORD:
                connect_kwargs["password"] = self.connection.password
            elif self.connection.auth_method in (AuthMethod.KEY_FILE, AuthMethod.KEY_WITH_PASSPHRASE):
                connect_kwargs["key_filename"] = self.connection.key_file
                if self.connection.passphrase:
                    connect_kwargs["passphrase"] = self.connection.passphrase

            # Test connection
            test_client.connect(**connect_kwargs)

            # Get server info
            transport = test_client.get_transport()
            if transport:
                banner = transport.remote_version
                server_key = transport.get_remote_server_key()
                key_bytes = server_key.get_fingerprint()
                fingerprint = hashlib.sha256(key_bytes).hexdigest()
                logger.info(f"Connection test successful. Server: {banner}, Fingerprint: {fingerprint[:16]}...")
            else:
                logger.info("Connection test successful")

            test_client.close()
            return True, None

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False, str(e)

    def get_transport(self) -> Optional[paramiko.Transport]:
        """
        Get SSH transport.

        Returns:
            Paramiko Transport object, or None if not connected
        """
        return self.transport

    def _start_keepalive_thread(self) -> None:
        """Start keepalive thread."""
        if self._keepalive_thread and self._keepalive_thread.is_alive():
            return

        self._keepalive_running = True
        self._keepalive_thread = threading.Thread(target=self._keepalive_loop, daemon=True)
        self._keepalive_thread.start()
        logger.debug("Keepalive thread started")

    def _stop_keepalive_thread(self) -> None:
        """Stop keepalive thread."""
        self._keepalive_running = False
        if self._keepalive_thread:
            self._keepalive_thread.join(timeout=2.0)
            self._keepalive_thread = None
        logger.debug("Keepalive thread stopped")

    def _keepalive_loop(self) -> None:
        """Keepalive loop to detect connection drops."""
        while self._keepalive_running:
            try:
                time.sleep(self.connection.keepalive_interval)

                if not self._keepalive_running:
                    break

                if self.transport and self.transport.is_active():
                    # Send keepalive packet
                    self.transport.send_ignore()
                else:
                    logger.warning("Connection lost in keepalive check")
                    self.connection.status = ConnectionStatus.ERROR
                    break

            except Exception as e:
                logger.error(f"Keepalive error: {e}")
                self.connection.status = ConnectionStatus.ERROR
                break

    def _save_host_key(self) -> None:
        """Save host key to known hosts file."""
        try:
            if not self.client or not self.transport:
                return

            # Create directory if it doesn't exist
            KNOWN_HOSTS_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Save host keys
            self.client.save_host_keys(str(KNOWN_HOSTS_FILE))
            logger.debug(f"Saved host key to {KNOWN_HOSTS_FILE}")

        except Exception as e:
            logger.warning(f"Could not save host key: {e}")

    def __enter__(self) -> "SSHManager":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[object]) -> None:
        """Context manager exit."""
        self.disconnect()

    def __del__(self) -> None:
        """Cleanup on deletion."""
        try:
            self.disconnect()
        except Exception:
            pass


# Import Tuple for type hints
from typing import Tuple
