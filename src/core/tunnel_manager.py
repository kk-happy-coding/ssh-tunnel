"""Tunnel management for SSH Tunnel Manager."""

import select
import socket
import threading
import time
from typing import Dict, Optional

import paramiko

from src.core.port_validator import PortValidator
from src.exceptions.custom_exceptions import PortConflictError, TunnelError
from src.models.tunnel import Tunnel
from src.utils.constants import TunnelStatus, TunnelType
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TunnelManager:
    """Manager for SSH tunnels."""

    def __init__(self, transport: paramiko.Transport) -> None:
        """
        Initialize tunnel manager.

        Args:
            transport: Paramiko Transport object
        """
        self.transport = transport
        self.tunnels: Dict[str, Tunnel] = {}
        self.tunnel_threads: Dict[str, threading.Thread] = {}
        self.tunnel_stop_events: Dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def start_tunnel(self, tunnel: Tunnel) -> None:
        """
        Start an SSH tunnel.

        Args:
            tunnel: Tunnel configuration

        Raises:
            TunnelError: If tunnel fails to start
            PortConflictError: If port is already in use
        """
        with self._lock:
            tunnel_id = self._get_tunnel_id(tunnel)

            if tunnel_id in self.tunnels:
                logger.warning(f"Tunnel {tunnel.name} is already running")
                return

            # Validate port availability
            try:
                PortValidator.validate_or_raise(tunnel.local_port, tunnel.bind_address)
            except PortConflictError as e:
                tunnel.status = TunnelStatus.ERROR
                tunnel.error_message = str(e)
                raise

            logger.info(f"Starting tunnel: {tunnel.name} ({tunnel.tunnel_type.value})")
            tunnel.status = TunnelStatus.CONNECTING

            try:
                # Create stop event
                stop_event = threading.Event()
                self.tunnel_stop_events[tunnel_id] = stop_event

                # Start tunnel based on type
                if tunnel.tunnel_type == TunnelType.LOCAL:
                    thread = threading.Thread(
                        target=self._local_forward_handler,
                        args=(tunnel, stop_event),
                        daemon=True,
                    )
                elif tunnel.tunnel_type == TunnelType.REMOTE:
                    thread = threading.Thread(
                        target=self._remote_forward_handler,
                        args=(tunnel, stop_event),
                        daemon=True,
                    )
                elif tunnel.tunnel_type == TunnelType.DYNAMIC:
                    thread = threading.Thread(
                        target=self._dynamic_forward_handler,
                        args=(tunnel, stop_event),
                        daemon=True,
                    )
                else:
                    raise TunnelError(f"Unknown tunnel type: {tunnel.tunnel_type}")

                thread.start()
                self.tunnel_threads[tunnel_id] = thread

                # Store tunnel
                self.tunnels[tunnel_id] = tunnel
                tunnel.start_time = time.time()
                tunnel.status = TunnelStatus.ACTIVE

                logger.info(f"Tunnel {tunnel.name} started successfully")

            except Exception as e:
                tunnel.status = TunnelStatus.ERROR
                tunnel.error_message = str(e)
                logger.error(f"Failed to start tunnel {tunnel.name}: {e}")
                raise TunnelError(f"Failed to start tunnel: {e}") from e

    def stop_tunnel(self, tunnel: Tunnel) -> None:
        """
        Stop an SSH tunnel.

        Args:
            tunnel: Tunnel to stop
        """
        with self._lock:
            tunnel_id = self._get_tunnel_id(tunnel)

            if tunnel_id not in self.tunnels:
                logger.warning(f"Tunnel {tunnel.name} is not running")
                return

            logger.info(f"Stopping tunnel: {tunnel.name}")

            # Signal stop event
            if tunnel_id in self.tunnel_stop_events:
                self.tunnel_stop_events[tunnel_id].set()

            # Wait for thread to finish
            if tunnel_id in self.tunnel_threads:
                thread = self.tunnel_threads[tunnel_id]
                thread.join(timeout=5.0)
                del self.tunnel_threads[tunnel_id]

            # Clean up
            if tunnel_id in self.tunnel_stop_events:
                del self.tunnel_stop_events[tunnel_id]

            if tunnel_id in self.tunnels:
                del self.tunnels[tunnel_id]

            tunnel.status = TunnelStatus.STOPPED
            tunnel.start_time = None

            logger.info(f"Tunnel {tunnel.name} stopped")

    def stop_all_tunnels(self) -> None:
        """Stop all tunnels."""
        tunnel_list = list(self.tunnels.values())
        for tunnel in tunnel_list:
            try:
                self.stop_tunnel(tunnel)
            except Exception as e:
                logger.error(f"Error stopping tunnel {tunnel.name}: {e}")

    def get_active_tunnels(self) -> list:
        """
        Get list of active tunnels.

        Returns:
            List of active tunnel objects
        """
        with self._lock:
            return list(self.tunnels.values())

    def is_tunnel_active(self, tunnel: Tunnel) -> bool:
        """
        Check if tunnel is active.

        Args:
            tunnel: Tunnel to check

        Returns:
            True if active, False otherwise
        """
        tunnel_id = self._get_tunnel_id(tunnel)
        return tunnel_id in self.tunnels

    def _get_tunnel_id(self, tunnel: Tunnel) -> str:
        """
        Get unique tunnel ID.

        Args:
            tunnel: Tunnel object

        Returns:
            Unique tunnel identifier
        """
        return f"{tunnel.tunnel_type.value}:{tunnel.local_port}:{tunnel.remote_host}:{tunnel.remote_port}"

    def _local_forward_handler(self, tunnel: Tunnel, stop_event: threading.Event) -> None:
        """
        Handle local port forwarding.

        Args:
            tunnel: Tunnel configuration
            stop_event: Event to signal stop
        """
        server_socket = None
        try:
            # Create server socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((tunnel.bind_address, tunnel.local_port))
            server_socket.listen(5)
            server_socket.settimeout(1.0)  # Timeout for accept()

            logger.debug(f"Local forward listening on {tunnel.bind_address}:{tunnel.local_port}")

            while not stop_event.is_set():
                try:
                    client_socket, client_addr = server_socket.accept()
                    logger.debug(f"Accepted connection from {client_addr}")

                    # Handle connection in separate thread
                    handler_thread = threading.Thread(
                        target=self._handle_local_forward_connection,
                        args=(client_socket, tunnel),
                        daemon=True,
                    )
                    handler_thread.start()

                except socket.timeout:
                    continue
                except Exception as e:
                    if not stop_event.is_set():
                        logger.error(f"Error accepting connection: {e}")

        except Exception as e:
            logger.error(f"Local forward handler error: {e}")
            tunnel.status = TunnelStatus.ERROR
            tunnel.error_message = str(e)

        finally:
            if server_socket:
                try:
                    server_socket.close()
                except Exception:
                    pass

    def _handle_local_forward_connection(self, client_socket: socket.socket, tunnel: Tunnel) -> None:
        """
        Handle a single local forward connection.

        Args:
            client_socket: Client socket
            tunnel: Tunnel configuration
        """
        channel = None
        try:
            # Open channel to remote host
            channel = self.transport.open_channel(
                "direct-tcpip",
                (tunnel.remote_host, tunnel.remote_port),
                client_socket.getpeername(),
            )

            # Forward data bidirectionally
            while True:
                r, w, x = select.select([client_socket, channel], [], [], 1.0)

                if client_socket in r:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    channel.send(data)
                    tunnel.bytes_sent += len(data)

                if channel in r:
                    data = channel.recv(4096)
                    if not data:
                        break
                    client_socket.send(data)
                    tunnel.bytes_received += len(data)

        except Exception as e:
            logger.debug(f"Connection handler error: {e}")

        finally:
            if channel:
                try:
                    channel.close()
                except Exception:
                    pass
            try:
                client_socket.close()
            except Exception:
                pass

    def _remote_forward_handler(self, tunnel: Tunnel, stop_event: threading.Event) -> None:
        """
        Handle remote port forwarding.

        Args:
            tunnel: Tunnel configuration
            stop_event: Event to signal stop
        """
        try:
            # Request remote port forwarding
            self.transport.request_port_forward(
                "", tunnel.remote_port
            )

            logger.debug(f"Remote forward established on remote port {tunnel.remote_port}")

            # Wait for connections
            while not stop_event.is_set():
                channel = self.transport.accept(timeout=1.0)
                if channel is None:
                    continue

                logger.debug("Accepted remote forward connection")

                # Handle connection in separate thread
                handler_thread = threading.Thread(
                    target=self._handle_remote_forward_connection,
                    args=(channel, tunnel),
                    daemon=True,
                )
                handler_thread.start()

        except Exception as e:
            logger.error(f"Remote forward handler error: {e}")
            tunnel.status = TunnelStatus.ERROR
            tunnel.error_message = str(e)

        finally:
            try:
                self.transport.cancel_port_forward("", tunnel.remote_port)
            except Exception:
                pass

    def _handle_remote_forward_connection(self, channel: paramiko.Channel, tunnel: Tunnel) -> None:
        """
        Handle a single remote forward connection.

        Args:
            channel: SSH channel
            tunnel: Tunnel configuration
        """
        local_socket = None
        try:
            # Connect to local host
            local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            local_socket.connect((tunnel.remote_host, tunnel.local_port))

            # Forward data bidirectionally
            while True:
                r, w, x = select.select([local_socket, channel], [], [], 1.0)

                if local_socket in r:
                    data = local_socket.recv(4096)
                    if not data:
                        break
                    channel.send(data)
                    tunnel.bytes_sent += len(data)

                if channel in r:
                    data = channel.recv(4096)
                    if not data:
                        break
                    local_socket.send(data)
                    tunnel.bytes_received += len(data)

        except Exception as e:
            logger.debug(f"Remote connection handler error: {e}")

        finally:
            if local_socket:
                try:
                    local_socket.close()
                except Exception:
                    pass
            try:
                channel.close()
            except Exception:
                pass

    def _dynamic_forward_handler(self, tunnel: Tunnel, stop_event: threading.Event) -> None:
        """
        Handle dynamic port forwarding (SOCKS5 proxy).

        Args:
            tunnel: Tunnel configuration
            stop_event: Event to signal stop
        """
        server_socket = None
        try:
            # Create server socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((tunnel.bind_address, tunnel.local_port))
            server_socket.listen(5)
            server_socket.settimeout(1.0)

            logger.debug(f"SOCKS5 proxy listening on {tunnel.bind_address}:{tunnel.local_port}")

            while not stop_event.is_set():
                try:
                    client_socket, client_addr = server_socket.accept()
                    logger.debug(f"Accepted SOCKS5 connection from {client_addr}")

                    # Handle SOCKS5 connection in separate thread
                    handler_thread = threading.Thread(
                        target=self._handle_socks5_connection,
                        args=(client_socket, tunnel),
                        daemon=True,
                    )
                    handler_thread.start()

                except socket.timeout:
                    continue
                except Exception as e:
                    if not stop_event.is_set():
                        logger.error(f"Error accepting SOCKS5 connection: {e}")

        except Exception as e:
            logger.error(f"Dynamic forward handler error: {e}")
            tunnel.status = TunnelStatus.ERROR
            tunnel.error_message = str(e)

        finally:
            if server_socket:
                try:
                    server_socket.close()
                except Exception:
                    pass

    def _handle_socks5_connection(self, client_socket: socket.socket, tunnel: Tunnel) -> None:
        """
        Handle a SOCKS5 connection (simplified implementation).

        Args:
            client_socket: Client socket
            tunnel: Tunnel configuration
        """
        channel = None
        try:
            # SOCKS5 handshake
            # Read version and number of auth methods
            data = client_socket.recv(2)
            if len(data) < 2 or data[0] != 5:
                return

            # Read auth methods
            num_methods = data[1]
            methods = client_socket.recv(num_methods)

            # Send auth method (no authentication)
            client_socket.send(b"\x05\x00")

            # Read connection request
            data = client_socket.recv(4)
            if len(data) < 4 or data[0] != 5 or data[1] != 1:
                return

            # Read address type
            addr_type = data[3]

            # Parse destination address
            if addr_type == 1:  # IPv4
                addr_data = client_socket.recv(4)
                dest_addr = socket.inet_ntoa(addr_data)
            elif addr_type == 3:  # Domain name
                addr_len = client_socket.recv(1)[0]
                dest_addr = client_socket.recv(addr_len).decode()
            else:
                # Unsupported address type
                client_socket.send(b"\x05\x08\x00\x01\x00\x00\x00\x00\x00\x00")
                return

            # Read destination port
            port_data = client_socket.recv(2)
            dest_port = int.from_bytes(port_data, "big")

            logger.debug(f"SOCKS5 request to {dest_addr}:{dest_port}")

            # Open SSH channel
            channel = self.transport.open_channel(
                "direct-tcpip",
                (dest_addr, dest_port),
                client_socket.getpeername(),
            )

            # Send success response
            client_socket.send(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")

            # Forward data bidirectionally
            while True:
                r, w, x = select.select([client_socket, channel], [], [], 1.0)

                if client_socket in r:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    channel.send(data)
                    tunnel.bytes_sent += len(data)

                if channel in r:
                    data = channel.recv(4096)
                    if not data:
                        break
                    client_socket.send(data)
                    tunnel.bytes_received += len(data)

        except Exception as e:
            logger.debug(f"SOCKS5 connection handler error: {e}")

        finally:
            if channel:
                try:
                    channel.close()
                except Exception:
                    pass
            try:
                client_socket.close()
            except Exception:
                pass
