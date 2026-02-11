"""Port validation and availability checking for SSH Tunnel Manager."""

import socket
from typing import List, Optional, Tuple

from src.exceptions.custom_exceptions import PortConflictError
from src.utils.constants import MAX_PORT, MIN_PORT
from src.utils.logger import get_logger
from src.utils.validators import get_process_using_port, is_port_available

logger = get_logger(__name__)


class PortValidator:
    """Validator for port numbers and availability."""

    @staticmethod
    def validate_port_range(port: int) -> Tuple[bool, Optional[str]]:
        """
        Validate that port is in valid range.

        Args:
            port: Port number to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(port, int):
            return False, "Port must be an integer"

        if port < MIN_PORT or port > MAX_PORT:
            return False, f"Port must be between {MIN_PORT} and {MAX_PORT}"

        return True, None

    @staticmethod
    def check_port_available(port: int, bind_address: str = "127.0.0.1") -> Tuple[bool, Optional[str]]:
        """
        Check if port is available for binding.

        Args:
            port: Port number to check
            bind_address: Address to bind to

        Returns:
            Tuple of (is_available, error_message)
        """
        # First validate port range
        is_valid, error = PortValidator.validate_port_range(port)
        if not is_valid:
            return False, error

        # Check if port is available
        if not is_port_available(port, bind_address):
            pid = get_process_using_port(port)
            if pid:
                return False, f"Port {port} is already in use by process {pid}"
            return False, f"Port {port} is already in use"

        return True, None

    @staticmethod
    def find_available_port(start_port: int = 10000, end_port: int = 20000) -> Optional[int]:
        """
        Find an available port in the given range.

        Args:
            start_port: Starting port number
            end_port: Ending port number

        Returns:
            Available port number, or None if no port found
        """
        for port in range(start_port, end_port + 1):
            is_available, _ = PortValidator.check_port_available(port)
            if is_available:
                logger.debug(f"Found available port: {port}")
                return port

        logger.warning(f"No available ports found in range {start_port}-{end_port}")
        return None

    @staticmethod
    def check_ports_batch(ports: List[int], bind_address: str = "127.0.0.1") -> dict:
        """
        Check availability of multiple ports.

        Args:
            ports: List of port numbers to check
            bind_address: Address to bind to

        Returns:
            Dictionary mapping port to (is_available, error_message)
        """
        results = {}
        for port in ports:
            results[port] = PortValidator.check_port_available(port, bind_address)
        return results

    @staticmethod
    def validate_or_raise(port: int, bind_address: str = "127.0.0.1") -> None:
        """
        Validate port and raise exception if not available.

        Args:
            port: Port number to validate
            bind_address: Address to bind to

        Raises:
            PortConflictError: If port is not available
            ValueError: If port is out of range
        """
        is_available, error = PortValidator.check_port_available(port, bind_address)
        if not is_available:
            if "in use" in error.lower():
                raise PortConflictError(port, error)
            raise ValueError(error)
