"""Network utilities for SSH Tunnel Manager."""

import socket
from typing import List, Optional, Tuple

from src.utils.constants import CONNECTION_TEST_TIMEOUT, PORT_CHECK_TIMEOUT


def test_connectivity(host: str, port: int, timeout: int = CONNECTION_TEST_TIMEOUT) -> Tuple[bool, Optional[str]]:
    """
    Test network connectivity to a host and port.

    Args:
        host: Hostname or IP address
        port: Port number
        timeout: Connection timeout in seconds

    Returns:
        Tuple of (is_reachable, error_message)
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)

    try:
        sock.connect((host, port))
        sock.close()
        return True, None
    except socket.timeout:
        return False, f"Connection timed out after {timeout} seconds"
    except socket.gaierror as e:
        return False, f"DNS resolution failed: {e}"
    except ConnectionRefusedError:
        return False, "Connection refused"
    except OSError as e:
        return False, f"Connection error: {e}"
    finally:
        try:
            sock.close()
        except Exception:
            pass


def is_port_in_use(port: int, bind_address: str = "127.0.0.1") -> bool:
    """
    Check if a port is already in use.

    Args:
        port: Port number to check
        bind_address: Address to check

    Returns:
        True if port is in use, False otherwise
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind_address, port))
        sock.close()
        return False
    except OSError:
        return True


def find_available_port(
    start_port: int = 10000,
    end_port: int = 20000,
    bind_address: str = "127.0.0.1",
) -> Optional[int]:
    """
    Find an available port in the given range.

    Args:
        start_port: Starting port number
        end_port: Ending port number
        bind_address: Address to bind to

    Returns:
        Available port number, or None if no port available
    """
    for port in range(start_port, end_port + 1):
        if not is_port_in_use(port, bind_address):
            return port
    return None


def scan_ports(
    host: str,
    ports: List[int],
    timeout: float = PORT_CHECK_TIMEOUT,
) -> List[int]:
    """
    Scan multiple ports on a host.

    Args:
        host: Hostname or IP address
        ports: List of port numbers to scan
        timeout: Timeout for each port check

    Returns:
        List of open ports
    """
    open_ports = []

    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        try:
            result = sock.connect_ex((host, port))
            if result == 0:
                open_ports.append(port)
        except (socket.error, socket.timeout):
            pass
        finally:
            sock.close()

    return open_ports


def get_local_ip() -> str:
    """
    Get the local IP address.

    Returns:
        Local IP address as string
    """
    try:
        # Create a socket and connect to an external address
        # This doesn't actually send data
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        local_ip = sock.getsockname()[0]
        sock.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


def resolve_hostname(hostname: str) -> Optional[str]:
    """
    Resolve hostname to IP address.

    Args:
        hostname: Hostname to resolve

    Returns:
        IP address as string, or None if resolution fails
    """
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None


def get_hostname() -> str:
    """
    Get the local hostname.

    Returns:
        Local hostname as string
    """
    try:
        return socket.gethostname()
    except Exception:
        return "localhost"
