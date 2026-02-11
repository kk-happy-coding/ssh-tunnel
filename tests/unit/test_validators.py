"""Unit tests for validators module.

Tests cover all validation functions with valid, boundary, and invalid inputs
to ensure proper input sanitization and security.
"""

import pytest
from pathlib import Path
import tempfile

from src.utils.validators import (
    validate_host,
    validate_port,
    validate_username,
    validate_password,
    validate_key_file,
    validate_profile_name,
    validate_tunnel_name,
    validate_ip_address,
    is_port_available,
)


class TestValidateHost:
    """Tests for host validation."""

    def test_valid_hostname(self):
        """Test validation of valid hostname."""
        is_valid, error = validate_host("example.com")
        assert is_valid is True
        assert error is None

    def test_valid_ipv4(self):
        """Test validation of valid IPv4 address."""
        is_valid, error = validate_host("192.168.1.1")
        assert is_valid is True
        assert error is None

    def test_valid_ipv6(self):
        """Test validation of valid IPv6 address."""
        is_valid, error = validate_host("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        assert is_valid is True
        assert error is None

    def test_empty_host(self):
        """Test validation of empty host."""
        is_valid, error = validate_host("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_host_with_whitespace(self):
        """Test validation of host with whitespace."""
        is_valid, error = validate_host("example .com")
        assert is_valid is False
        assert "whitespace" in error.lower()

    def test_host_with_shell_metacharacters(self):
        """Test validation of host with shell metacharacters."""
        dangerous_chars = [";", "&", "|", "`", "$", "(", ")"]
        for char in dangerous_chars:
            is_valid, error = validate_host(f"example{char}com")
            assert is_valid is False
            assert "invalid" in error.lower()

    def test_host_exceeds_max_length(self):
        """Test validation of host exceeding maximum length."""
        long_host = "a" * 300
        is_valid, error = validate_host(long_host)
        assert is_valid is False
        assert "maximum length" in error.lower()

    def test_invalid_hostname_format(self):
        """Test validation of invalid hostname format."""
        is_valid, error = validate_host("invalid..hostname")
        assert is_valid is False

    @pytest.mark.parametrize("host", [
        "localhost",
        "example.com",
        "sub.domain.example.com",
        "192.168.1.1",
        "10.0.0.1",
    ])
    def test_various_valid_hosts(self, host):
        """Test various valid host formats."""
        is_valid, error = validate_host(host)
        assert is_valid is True


class TestValidatePort:
    """Tests for port validation."""

    def test_valid_port(self):
        """Test validation of valid port."""
        is_valid, error = validate_port(8080)
        assert is_valid is True
        assert error is None

    def test_port_minimum_boundary(self):
        """Test validation of minimum port boundary."""
        is_valid, error = validate_port(1)
        assert is_valid is True

    def test_port_maximum_boundary(self):
        """Test validation of maximum port boundary."""
        is_valid, error = validate_port(65535)
        assert is_valid is True

    def test_port_zero(self):
        """Test validation of port zero."""
        is_valid, error = validate_port(0)
        assert is_valid is False
        assert "between" in error.lower()

    def test_negative_port(self):
        """Test validation of negative port."""
        is_valid, error = validate_port(-1)
        assert is_valid is False

    def test_port_exceeds_maximum(self):
        """Test validation of port exceeding maximum."""
        is_valid, error = validate_port(65536)
        assert is_valid is False

    def test_port_extremely_large(self):
        """Test validation of extremely large port."""
        is_valid, error = validate_port(99999)
        assert is_valid is False

    def test_port_not_integer(self):
        """Test validation of non-integer port."""
        is_valid, error = validate_port("8080")  # type: ignore
        assert is_valid is False

    @pytest.mark.parametrize("port", [22, 80, 443, 3000, 8080, 9000])
    def test_common_ports(self, port):
        """Test validation of common ports."""
        is_valid, error = validate_port(port)
        assert is_valid is True


class TestValidateUsername:
    """Tests for username validation."""

    def test_valid_username(self):
        """Test validation of valid username."""
        is_valid, error = validate_username("testuser")
        assert is_valid is True
        assert error is None

    def test_username_with_underscore(self):
        """Test validation of username with underscore."""
        is_valid, error = validate_username("test_user")
        assert is_valid is True

    def test_username_with_dash(self):
        """Test validation of username with dash."""
        is_valid, error = validate_username("test-user")
        assert is_valid is True

    def test_username_with_dot(self):
        """Test validation of username with dot."""
        is_valid, error = validate_username("test.user")
        assert is_valid is True

    def test_empty_username(self):
        """Test validation of empty username."""
        is_valid, error = validate_username("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_username_with_space(self):
        """Test validation of username with space."""
        is_valid, error = validate_username("test user")
        assert is_valid is False

    def test_username_with_shell_metacharacters(self):
        """Test validation of username with shell metacharacters."""
        dangerous_chars = [";", "&", "|", "`", "$", "(", ")"]
        for char in dangerous_chars:
            is_valid, error = validate_username(f"test{char}user")
            assert is_valid is False

    def test_username_exceeds_max_length(self):
        """Test validation of username exceeding maximum length."""
        long_username = "a" * 50
        is_valid, error = validate_username(long_username)
        assert is_valid is False

    def test_username_with_unicode(self):
        """Test validation of username with unicode characters."""
        is_valid, error = validate_username("test\u00e9user")
        assert is_valid is False


class TestValidatePassword:
    """Tests for password validation."""

    def test_valid_password(self):
        """Test validation of valid password."""
        is_valid, error = validate_password("password123")
        assert is_valid is True
        assert error is None

    def test_empty_password(self):
        """Test validation of empty password."""
        is_valid, error = validate_password("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_password_with_special_chars(self):
        """Test validation of password with special characters."""
        is_valid, error = validate_password("P@ssw0rd!#$%")
        assert is_valid is True

    def test_password_exceeds_max_length(self):
        """Test validation of password exceeding maximum length."""
        long_password = "a" * 300
        is_valid, error = validate_password(long_password)
        assert is_valid is False

    def test_password_with_unicode(self):
        """Test validation of password with unicode."""
        is_valid, error = validate_password("p\u00e9ssword")
        assert is_valid is True


class TestValidateKeyFile:
    """Tests for key file validation."""

    def test_valid_key_file(self, temp_dir):
        """Test validation of valid key file."""
        key_file = temp_dir / "test_key.pem"
        key_file.write_text("-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----\n")

        is_valid, error = validate_key_file(str(key_file))
        assert is_valid is True
        assert error is None

    def test_empty_key_path(self):
        """Test validation of empty key path."""
        is_valid, error = validate_key_file("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_nonexistent_key_file(self):
        """Test validation of nonexistent key file."""
        is_valid, error = validate_key_file("/nonexistent/key.pem")
        assert is_valid is False
        assert "not exist" in error.lower()

    def test_path_traversal_attempt(self):
        """Test validation of path traversal attempt."""
        is_valid, error = validate_key_file("../../../etc/passwd")
        assert is_valid is False
        assert "traversal" in error.lower()

    def test_key_file_is_directory(self, temp_dir):
        """Test validation when key file path is a directory."""
        is_valid, error = validate_key_file(str(temp_dir))
        assert is_valid is False

    def test_empty_key_file(self, temp_dir):
        """Test validation of empty key file."""
        key_file = temp_dir / "empty_key.pem"
        key_file.touch()

        is_valid, error = validate_key_file(str(key_file))
        assert is_valid is False
        assert "empty" in error.lower()

    def test_key_file_too_large(self, temp_dir):
        """Test validation of key file exceeding size limit."""
        key_file = temp_dir / "large_key.pem"
        # Create file larger than 10MB
        with open(key_file, "wb") as f:
            f.write(b"0" * (11 * 1024 * 1024))

        is_valid, error = validate_key_file(str(key_file))
        assert is_valid is False
        assert "exceeds" in error.lower()

    def test_invalid_key_format(self, temp_dir):
        """Test validation of invalid key file format."""
        key_file = temp_dir / "invalid_key.txt"
        key_file.write_text("This is not a valid key file")

        is_valid, error = validate_key_file(str(key_file))
        assert is_valid is False
        assert "invalid" in error.lower() or "format" in error.lower()


class TestValidateProfileName:
    """Tests for profile name validation."""

    def test_valid_profile_name(self):
        """Test validation of valid profile name."""
        is_valid, error = validate_profile_name("my_profile")
        assert is_valid is True
        assert error is None

    def test_empty_profile_name(self):
        """Test validation of empty profile name."""
        is_valid, error = validate_profile_name("")
        assert is_valid is False

    def test_profile_name_with_space(self):
        """Test validation of profile name with space."""
        is_valid, error = validate_profile_name("my profile")
        assert is_valid is True

    def test_profile_name_exceeds_max_length(self):
        """Test validation of profile name exceeding maximum length."""
        long_name = "a" * 100
        is_valid, error = validate_profile_name(long_name)
        assert is_valid is False

    def test_profile_name_with_special_chars(self):
        """Test validation of profile name with invalid special characters."""
        is_valid, error = validate_profile_name("profile@#$")
        assert is_valid is False

    def test_reserved_windows_name(self):
        """Test validation of reserved Windows filename."""
        reserved_names = ["CON", "PRN", "AUX", "NUL"]
        for name in reserved_names:
            is_valid, error = validate_profile_name(name)
            assert is_valid is False
            assert "reserved" in error.lower()


class TestValidateTunnelName:
    """Tests for tunnel name validation."""

    def test_valid_tunnel_name(self):
        """Test validation of valid tunnel name."""
        is_valid, error = validate_tunnel_name("tunnel_1")
        assert is_valid is True
        assert error is None

    def test_empty_tunnel_name(self):
        """Test validation of empty tunnel name (should be valid as it's optional)."""
        is_valid, error = validate_tunnel_name("")
        assert is_valid is True

    def test_tunnel_name_exceeds_max_length(self):
        """Test validation of tunnel name exceeding maximum length."""
        long_name = "a" * 50
        is_valid, error = validate_tunnel_name(long_name)
        assert is_valid is False

    def test_tunnel_name_with_special_chars(self):
        """Test validation of tunnel name with invalid special characters."""
        is_valid, error = validate_tunnel_name("tunnel@#")
        assert is_valid is False


class TestValidateIPAddress:
    """Tests for IP address validation."""

    def test_valid_ipv4(self):
        """Test validation of valid IPv4 address."""
        is_valid, error = validate_ip_address("192.168.1.1")
        assert is_valid is True

    def test_valid_ipv6(self):
        """Test validation of valid IPv6 address."""
        is_valid, error = validate_ip_address("2001:db8::1")
        assert is_valid is True

    def test_empty_ip(self):
        """Test validation of empty IP address."""
        is_valid, error = validate_ip_address("")
        assert is_valid is False

    def test_invalid_ip_format(self):
        """Test validation of invalid IP format."""
        is_valid, error = validate_ip_address("999.999.999.999")
        assert is_valid is False


@pytest.mark.unit
class TestPortAvailability:
    """Tests for port availability checking."""

    def test_is_port_available_free_port(self):
        """Test checking availability of a free port."""
        # Port 0 will be assigned by OS
        import socket
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()

        # Port should now be available
        assert is_port_available(port) is True

    def test_is_port_available_used_port(self):
        """Test checking availability of a port in use."""
        import socket
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

        # Port is in use
        assert is_port_available(port) is False

        sock.close()
