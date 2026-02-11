"""Input validation utilities for SSH Tunnel Manager."""

import re
import socket
from pathlib import Path
from typing import Optional, Tuple

from src.utils.constants import (
    MAX_HOSTNAME_LENGTH,
    MAX_KEY_FILE_SIZE,
    MAX_PASSWORD_LENGTH,
    MAX_PORT,
    MAX_PROFILE_NAME_LENGTH,
    MAX_TUNNEL_NAME_LENGTH,
    MAX_USERNAME_LENGTH,
    MIN_PORT,
)


class ValidationError(Exception):
    """Exception raised for validation errors."""

    pass


def validate_host(host: str) -> Tuple[bool, Optional[str]]:
    """
    Validate hostname or IP address.

    Args:
        host: Hostname or IP address to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not host or not host.strip():
        return False, "Host cannot be empty"

    host = host.strip()

    if len(host) > MAX_HOSTNAME_LENGTH:
        return False, f"Host exceeds maximum length of {MAX_HOSTNAME_LENGTH} characters"

    # Check for shell metacharacters
    dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
    if any(char in host for char in dangerous_chars):
        return False, "Host contains invalid characters"

    # Check for whitespace
    if " " in host or "\t" in host:
        return False, "Host cannot contain whitespace"

    # Try to validate as IPv4
    try:
        socket.inet_aton(host)
        return True, None
    except socket.error:
        pass

    # Try to validate as IPv6
    try:
        socket.inet_pton(socket.AF_INET6, host)
        return True, None
    except (socket.error, OSError):
        pass

    # Validate as hostname
    # Allow alphanumeric, dots, and hyphens (common for hostnames)
    hostname_pattern = re.compile(
        r"^(?!-)(?:[a-zA-Z0-9-]{1,63}(?<!-)\.)*[a-zA-Z0-9-]{1,63}(?<!-)$"
    )
    if not hostname_pattern.match(host):
        return False, "Invalid hostname format"

    return True, None


def validate_port(port: int, check_available: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate port number.

    Args:
        port: Port number to validate
        check_available: Whether to check if port is available

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(port, int):
        return False, "Port must be an integer"

    if port < MIN_PORT or port > MAX_PORT:
        return False, f"Port must be between {MIN_PORT} and {MAX_PORT}"

    if check_available:
        # Try to bind to the port to check availability
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", port))
            sock.close()
        except OSError as e:
            return False, f"Port {port} is already in use"

    return True, None


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Validate SSH username.

    Args:
        username: Username to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username or not username.strip():
        return False, "Username cannot be empty"

    username = username.strip()

    if len(username) > MAX_USERNAME_LENGTH:
        return False, f"Username exceeds maximum length of {MAX_USERNAME_LENGTH} characters"

    # Check for shell metacharacters
    dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r", " ", "\t"]
    if any(char in username for char in dangerous_chars):
        return False, "Username contains invalid characters"

    # Valid username pattern: alphanumeric + underscore, dot, dash
    username_pattern = re.compile(r"^[a-zA-Z0-9._-]+$")
    if not username_pattern.match(username):
        return False, "Username can only contain letters, numbers, dots, underscores, and dashes"

    return True, None


def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate SSH password.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password cannot be empty"

    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"Password exceeds maximum length of {MAX_PASSWORD_LENGTH} characters"

    return True, None


def validate_key_file(key_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate SSH private key file.

    Args:
        key_path: Path to key file

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not key_path or not key_path.strip():
        return False, "Key file path cannot be empty"

    key_path = key_path.strip()

    # Check for path traversal
    try:
        resolved_path = Path(key_path).resolve()
    except (ValueError, OSError) as e:
        return False, f"Invalid file path: {e}"

    # Ensure it's not a path traversal attempt
    if ".." in key_path:
        return False, "Path traversal not allowed"

    # Check if file exists
    if not resolved_path.exists():
        return False, "Key file does not exist"

    # Check if it's a file
    if not resolved_path.is_file():
        return False, "Path is not a file"

    # Check if readable
    if not resolved_path.is_file():
        return False, "Key file is not readable"

    # Check file size
    try:
        file_size = resolved_path.stat().st_size
        if file_size > MAX_KEY_FILE_SIZE:
            return False, f"Key file exceeds maximum size of {MAX_KEY_FILE_SIZE} bytes"
        if file_size == 0:
            return False, "Key file is empty"
    except OSError as e:
        return False, f"Cannot read key file: {e}"

    # Validate key file format (check for PEM or OpenSSH headers)
    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            valid_headers = [
                "-----BEGIN RSA PRIVATE KEY-----",
                "-----BEGIN DSA PRIVATE KEY-----",
                "-----BEGIN EC PRIVATE KEY-----",
                "-----BEGIN OPENSSH PRIVATE KEY-----",
                "-----BEGIN PRIVATE KEY-----",
                "-----BEGIN ENCRYPTED PRIVATE KEY-----",
            ]
            if not any(first_line.startswith(header) for header in valid_headers):
                return False, "Invalid key file format (missing valid PEM/OpenSSH header)"
    except UnicodeDecodeError:
        return False, "Key file is not a valid text file"
    except OSError as e:
        return False, f"Cannot read key file: {e}"

    return True, None


def validate_profile_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate profile name.

    Args:
        name: Profile name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Profile name cannot be empty"

    name = name.strip()

    if len(name) > MAX_PROFILE_NAME_LENGTH:
        return False, f"Profile name exceeds maximum length of {MAX_PROFILE_NAME_LENGTH} characters"

    # Filesystem-safe characters only
    profile_pattern = re.compile(r"^[a-zA-Z0-9._\-\s]+$")
    if not profile_pattern.match(name):
        return False, "Profile name can only contain letters, numbers, spaces, dots, dashes, and underscores"

    # Check for reserved names (Windows)
    reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
                      "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4",
                      "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]
    if name.upper() in reserved_names:
        return False, "Profile name is a reserved system name"

    return True, None


def validate_tunnel_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate tunnel name.

    Args:
        name: Tunnel name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return True, None  # Tunnel name is optional

    name = name.strip()

    if len(name) > MAX_TUNNEL_NAME_LENGTH:
        return False, f"Tunnel name exceeds maximum length of {MAX_TUNNEL_NAME_LENGTH} characters"

    # Alphanumeric, spaces, underscore, dash
    tunnel_pattern = re.compile(r"^[a-zA-Z0-9_\-\s]+$")
    if not tunnel_pattern.match(name):
        return False, "Tunnel name can only contain letters, numbers, spaces, dashes, and underscores"

    return True, None


def validate_ip_address(ip: str) -> Tuple[bool, Optional[str]]:
    """
    Validate IP address (IPv4 or IPv6).

    Args:
        ip: IP address to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not ip or not ip.strip():
        return False, "IP address cannot be empty"

    ip = ip.strip()

    # Try IPv4
    try:
        socket.inet_aton(ip)
        return True, None
    except socket.error:
        pass

    # Try IPv6
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        return True, None
    except (socket.error, OSError):
        pass

    return False, "Invalid IP address format"


def is_port_available(port: int, bind_address: str = "127.0.0.1") -> bool:
    """
    Check if a port is available for binding.

    Args:
        port: Port number to check
        bind_address: Address to bind to

    Returns:
        True if port is available, False otherwise
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind_address, port))
        sock.close()
        return True
    except OSError:
        return False


def get_process_using_port(port: int) -> Optional[int]:
    """
    Get PID of process using a specific port (Windows only).

    Args:
        port: Port number to check

    Returns:
        PID of process using the port, or None if not found
    """
    import subprocess
    import sys

    if sys.platform != "win32":
        return None

    try:
        output = subprocess.check_output(
            ["netstat", "-ano"], universal_newlines=True
        )
        for line in output.split("\n"):
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if parts:
                    return int(parts[-1])
    except (subprocess.CalledProcessError, ValueError, IndexError):
        pass

    return None
