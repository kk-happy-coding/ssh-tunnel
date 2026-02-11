"""Tunnel monitoring and auto-reconnect for SSH Tunnel Manager."""

import threading
import time
from typing import Callable, Dict, Optional

from src.models.tunnel import Tunnel
from src.utils.constants import (
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_MAX_RECONNECT_ATTEMPTS,
    DEFAULT_RECONNECT_DELAY,
    MAX_RECONNECT_BACKOFF,
    TunnelStatus,
)
from src.utils.logger import get_logger
from src.utils.network import test_connectivity

logger = get_logger(__name__)


class TunnelMonitor:
    """Monitor SSH tunnels and handle auto-reconnect."""

    def __init__(
        self,
        heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL,
        max_reconnect_attempts: int = DEFAULT_MAX_RECONNECT_ATTEMPTS,
        reconnect_delay: int = DEFAULT_RECONNECT_DELAY,
    ) -> None:
        """
        Initialize tunnel monitor.

        Args:
            heartbeat_interval: Interval between heartbeat checks (seconds)
            max_reconnect_attempts: Maximum number of reconnection attempts
            reconnect_delay: Base delay between reconnection attempts (seconds)
        """
        self.heartbeat_interval = heartbeat_interval
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay

        self.tunnels: Dict[str, Tunnel] = {}
        self.reconnect_callbacks: Dict[str, Callable] = {}

        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_running = False
        self._lock = threading.Lock()

    def start_monitoring(self) -> None:
        """Start monitoring thread."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.warning("Monitor thread is already running")
            return

        self._monitor_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Tunnel monitor started")

    def stop_monitoring(self) -> None:
        """Stop monitoring thread."""
        self._monitor_running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None
        logger.info("Tunnel monitor stopped")

    def register_tunnel(
        self,
        tunnel: Tunnel,
        reconnect_callback: Optional[Callable] = None,
    ) -> None:
        """
        Register tunnel for monitoring.

        Args:
            tunnel: Tunnel to monitor
            reconnect_callback: Callback function to call for reconnection
        """
        with self._lock:
            tunnel_id = self._get_tunnel_id(tunnel)
            self.tunnels[tunnel_id] = tunnel
            if reconnect_callback:
                self.reconnect_callbacks[tunnel_id] = reconnect_callback
            logger.debug(f"Registered tunnel for monitoring: {tunnel.name}")

    def unregister_tunnel(self, tunnel: Tunnel) -> None:
        """
        Unregister tunnel from monitoring.

        Args:
            tunnel: Tunnel to unregister
        """
        with self._lock:
            tunnel_id = self._get_tunnel_id(tunnel)
            if tunnel_id in self.tunnels:
                del self.tunnels[tunnel_id]
            if tunnel_id in self.reconnect_callbacks:
                del self.reconnect_callbacks[tunnel_id]
            logger.debug(f"Unregistered tunnel from monitoring: {tunnel.name}")

    def check_tunnel_health(self, tunnel: Tunnel) -> bool:
        """
        Check if tunnel is healthy.

        Args:
            tunnel: Tunnel to check

        Returns:
            True if healthy, False otherwise
        """
        # Check if tunnel status is active
        if tunnel.status != TunnelStatus.ACTIVE:
            return False

        # For local tunnels, check if local port is accessible
        from src.utils.network import is_port_in_use

        if not is_port_in_use(tunnel.local_port, tunnel.bind_address):
            logger.warning(f"Tunnel {tunnel.name} local port is not bound")
            return False

        return True

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitor_running:
            try:
                time.sleep(self.heartbeat_interval)

                if not self._monitor_running:
                    break

                # Check all registered tunnels
                with self._lock:
                    tunnels_to_check = list(self.tunnels.items())

                for tunnel_id, tunnel in tunnels_to_check:
                    try:
                        self._check_and_handle_tunnel(tunnel_id, tunnel)
                    except Exception as e:
                        logger.error(f"Error checking tunnel {tunnel.name}: {e}")

            except Exception as e:
                logger.error(f"Monitor loop error: {e}")

    def _check_and_handle_tunnel(self, tunnel_id: str, tunnel: Tunnel) -> None:
        """
        Check tunnel and handle reconnection if needed.

        Args:
            tunnel_id: Tunnel identifier
            tunnel: Tunnel object
        """
        # Skip if tunnel is not active
        if tunnel.status not in (TunnelStatus.ACTIVE, TunnelStatus.ERROR):
            return

        # Check tunnel health
        is_healthy = self.check_tunnel_health(tunnel)

        if not is_healthy and tunnel.status == TunnelStatus.ACTIVE:
            logger.warning(f"Tunnel {tunnel.name} is not healthy")
            tunnel.status = TunnelStatus.ERROR
            tunnel.error_message = "Tunnel health check failed"

            # Attempt reconnection if callback is available
            if tunnel_id in self.reconnect_callbacks:
                self._attempt_reconnection(tunnel_id, tunnel)

    def _attempt_reconnection(self, tunnel_id: str, tunnel: Tunnel) -> None:
        """
        Attempt to reconnect tunnel.

        Args:
            tunnel_id: Tunnel identifier
            tunnel: Tunnel object
        """
        callback = self.reconnect_callbacks.get(tunnel_id)
        if not callback:
            return

        logger.info(f"Attempting to reconnect tunnel: {tunnel.name}")
        tunnel.status = TunnelStatus.RECONNECTING

        for attempt in range(self.max_reconnect_attempts):
            if not self._monitor_running:
                break

            # Calculate backoff delay
            delay = min(
                self.reconnect_delay * (2 ** attempt),
                MAX_RECONNECT_BACKOFF,
            )

            logger.debug(
                f"Reconnection attempt {attempt + 1}/{self.max_reconnect_attempts} "
                f"for tunnel {tunnel.name} (delay: {delay}s)"
            )

            # Wait before attempting reconnection
            time.sleep(delay)

            try:
                # Call reconnection callback
                callback(tunnel)

                # Check if reconnection was successful
                if tunnel.status == TunnelStatus.ACTIVE:
                    logger.info(f"Successfully reconnected tunnel: {tunnel.name}")
                    tunnel.reconnect_count += 1
                    return

            except Exception as e:
                logger.error(f"Reconnection attempt failed for tunnel {tunnel.name}: {e}")
                tunnel.error_message = f"Reconnection failed: {e}"

        # All reconnection attempts failed
        logger.error(
            f"Failed to reconnect tunnel {tunnel.name} after "
            f"{self.max_reconnect_attempts} attempts"
        )
        tunnel.status = TunnelStatus.ERROR
        tunnel.error_message = f"Reconnection failed after {self.max_reconnect_attempts} attempts"

    def _get_tunnel_id(self, tunnel: Tunnel) -> str:
        """
        Get unique tunnel ID.

        Args:
            tunnel: Tunnel object

        Returns:
            Unique tunnel identifier
        """
        return f"{tunnel.tunnel_type.value}:{tunnel.local_port}:{tunnel.remote_host}:{tunnel.remote_port}"

    def get_statistics(self) -> dict:
        """
        Get monitoring statistics.

        Returns:
            Dictionary with statistics
        """
        with self._lock:
            total_tunnels = len(self.tunnels)
            active_tunnels = sum(
                1 for t in self.tunnels.values() if t.status == TunnelStatus.ACTIVE
            )
            error_tunnels = sum(
                1 for t in self.tunnels.values() if t.status == TunnelStatus.ERROR
            )
            reconnecting_tunnels = sum(
                1 for t in self.tunnels.values() if t.status == TunnelStatus.RECONNECTING
            )

            return {
                "total_tunnels": total_tunnels,
                "active_tunnels": active_tunnels,
                "error_tunnels": error_tunnels,
                "reconnecting_tunnels": reconnecting_tunnels,
                "monitor_running": self._monitor_running,
            }

    def __del__(self) -> None:
        """Cleanup on deletion."""
        try:
            self.stop_monitoring()
        except Exception:
            pass
