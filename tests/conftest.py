"""Shared fixtures for SSH Tunnel Manager tests."""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path
import tempfile
import shutil

from src.models.connection import Connection
from src.models.tunnel import Tunnel
from src.models.profile import Profile
from src.utils.constants import AuthMethod, TunnelType


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_connection():
    """Create sample SSH connection."""
    return Connection(
        host="example.com",
        port=22,
        username="testuser",
        password="testpass",
        auth_method=AuthMethod.PASSWORD,
    )


@pytest.fixture
def sample_tunnel_local():
    """Create sample local tunnel."""
    return Tunnel(
        tunnel_type=TunnelType.LOCAL,
        local_port=8080,
        remote_host="localhost",
        remote_port=80,
    )


@pytest.fixture
def sample_tunnel_remote():
    """Create sample remote tunnel."""
    return Tunnel(
        tunnel_type=TunnelType.REMOTE,
        local_port=3000,
        remote_host="localhost",
        remote_port=8080,
    )


@pytest.fixture
def sample_tunnel_dynamic():
    """Create sample dynamic tunnel."""
    return Tunnel(
        tunnel_type=TunnelType.DYNAMIC,
        local_port=1080,
        remote_host="localhost",
        remote_port=0,
    )


@pytest.fixture
def sample_profile(sample_connection, sample_tunnel_local):
    """Create sample profile."""
    return Profile(
        name="test_profile",
        connection=sample_connection,
        tunnels=[sample_tunnel_local],
    )


@pytest.fixture
def mock_ssh_client():
    """Create mock SSH client."""
    mock_client = MagicMock()
    mock_client.connect = Mock()
    mock_client.close = Mock()
    mock_client.get_transport = Mock(return_value=MagicMock())
    return mock_client


@pytest.fixture
def mock_transport():
    """Create mock SSH transport."""
    mock_trans = MagicMock()
    mock_trans.is_active = Mock(return_value=True)
    mock_trans.open_channel = Mock()
    mock_trans.request_port_forward = Mock()
    mock_trans.cancel_port_forward = Mock()
    return mock_trans


@pytest.fixture
def mock_paramiko(monkeypatch, mock_ssh_client):
    """Mock paramiko module."""
    mock_paramiko_module = MagicMock()
    mock_paramiko_module.SSHClient = Mock(return_value=mock_ssh_client)
    mock_paramiko_module.AutoAddPolicy = MagicMock
    monkeypatch.setattr("src.core.ssh_manager.paramiko", mock_paramiko_module)
    return mock_paramiko_module
