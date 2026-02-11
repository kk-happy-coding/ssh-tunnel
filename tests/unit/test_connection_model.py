"""Unit tests for Connection model.

Tests cover dataclass creation, validation, serialization/deserialization,
and equality operations.
"""

import pytest

from src.models.connection import Connection
from src.utils.constants import AuthMethod, ConnectionStatus


@pytest.mark.unit
class TestConnectionModel:
    """Tests for Connection dataclass."""

    def test_create_connection_with_password(self):
        """Test creating connection with password authentication."""
        conn = Connection(
            host="example.com",
            port=22,
            username="testuser",
            password="testpass",
            auth_method=AuthMethod.PASSWORD,
        )

        assert conn.host == "example.com"
        assert conn.port == 22
        assert conn.username == "testuser"
        assert conn.password == "testpass"
        assert conn.auth_method == AuthMethod.PASSWORD

    def test_create_connection_with_key_file(self, temp_dir):
        """Test creating connection with key file authentication."""
        key_file = temp_dir / "test.pem"
        key_file.write_text("-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----\n")

        conn = Connection(
            host="example.com",
            port=22,
            username="testuser",
            key_file=str(key_file),
            auth_method=AuthMethod.KEY_FILE,
        )

        assert conn.key_file == str(key_file)
        assert conn.auth_method == AuthMethod.KEY_FILE

    def test_create_connection_invalid_host(self):
        """Test creating connection with invalid host."""
        with pytest.raises(ValueError) as exc_info:
            Connection(
                host="",
                port=22,
                username="testuser",
                password="testpass",
                auth_method=AuthMethod.PASSWORD,
            )

        assert "host" in str(exc_info.value).lower()

    def test_create_connection_invalid_port(self):
        """Test creating connection with invalid port."""
        with pytest.raises(ValueError):
            Connection(
                host="example.com",
                port=0,
                username="testuser",
                password="testpass",
                auth_method=AuthMethod.PASSWORD,
            )

    def test_create_connection_invalid_username(self):
        """Test creating connection with invalid username."""
        with pytest.raises(ValueError):
            Connection(
                host="example.com",
                port=22,
                username="user@#$",
                password="testpass",
                auth_method=AuthMethod.PASSWORD,
            )

    def test_create_connection_missing_password(self):
        """Test creating connection without required password."""
        with pytest.raises(ValueError) as exc_info:
            Connection(
                host="example.com",
                port=22,
                username="testuser",
                auth_method=AuthMethod.PASSWORD,
            )

        assert "password" in str(exc_info.value).lower()

    def test_connection_to_dict(self, sample_connection):
        """Test converting connection to dictionary."""
        conn_dict = sample_connection.to_dict()

        assert conn_dict["host"] == sample_connection.host
        assert conn_dict["port"] == sample_connection.port
        assert conn_dict["username"] == sample_connection.username
        assert "password" not in conn_dict  # Passwords not included in dict

    def test_connection_from_dict(self, temp_dir):
        """Test creating connection from dictionary."""
        # Create temp key file
        key_file = temp_dir / "test_key.pem"
        key_file.write_text("-----BEGIN RSA PRIVATE KEY-----\ntest\n-----END RSA PRIVATE KEY-----\n")

        data = {
            "host": "example.com",
            "port": 22,
            "username": "testuser",
            "auth_method": "key_file",
            "key_file": str(key_file),
            "timeout": 10,
        }

        conn = Connection.from_dict(data)

        assert conn.host == data["host"]
        assert conn.port == data["port"]
        assert conn.username == data["username"]
        assert conn.auth_method == AuthMethod.KEY_FILE

    def test_connection_get_connection_string(self, sample_connection):
        """Test getting connection string representation."""
        conn_str = sample_connection.get_connection_string()

        assert sample_connection.username in conn_str
        assert sample_connection.host in conn_str
        assert str(sample_connection.port) in conn_str

    def test_connection_equality(self):
        """Test connection equality comparison."""
        conn1 = Connection(
            host="example.com",
            port=22,
            username="testuser",
            password="pass1",
            auth_method=AuthMethod.PASSWORD,
        )

        conn2 = Connection(
            host="example.com",
            port=22,
            username="testuser",
            password="pass2",
            auth_method=AuthMethod.PASSWORD,
        )

        assert conn1 == conn2  # Same host, port, username

    def test_connection_inequality(self):
        """Test connection inequality comparison."""
        conn1 = Connection(
            host="example1.com",
            port=22,
            username="testuser",
            password="pass",
            auth_method=AuthMethod.PASSWORD,
        )

        conn2 = Connection(
            host="example2.com",
            port=22,
            username="testuser",
            password="pass",
            auth_method=AuthMethod.PASSWORD,
        )

        assert conn1 != conn2

    def test_connection_hash(self):
        """Test connection hashing for use in sets/dicts."""
        conn1 = Connection(
            host="example.com",
            port=22,
            username="testuser",
            password="pass",
            auth_method=AuthMethod.PASSWORD,
        )

        conn2 = Connection(
            host="example.com",
            port=22,
            username="testuser",
            password="differentpass",
            auth_method=AuthMethod.PASSWORD,
        )

        # Same host, port, username should have same hash
        assert hash(conn1) == hash(conn2)

        # Can be used in set
        conn_set = {conn1, conn2}
        assert len(conn_set) == 1

    def test_connection_str(self, sample_connection):
        """Test string representation of connection."""
        conn_str = str(sample_connection)
        assert isinstance(conn_str, str)
        assert len(conn_str) > 0
