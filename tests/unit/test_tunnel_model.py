"""Unit tests for Tunnel model."""

import pytest

from src.models.tunnel import Tunnel
from src.utils.constants import TunnelType, TunnelStatus


@pytest.mark.unit
class TestTunnelModel:
    """Tests for Tunnel dataclass."""

    def test_create_local_tunnel(self):
        """Test creating local tunnel."""
        tunnel = Tunnel(
            tunnel_type=TunnelType.LOCAL,
            local_port=8080,
            remote_host="localhost",
            remote_port=80,
        )

        assert tunnel.tunnel_type == TunnelType.LOCAL
        assert tunnel.local_port == 8080
        assert tunnel.remote_host == "localhost"
        assert tunnel.remote_port == 80

    def test_create_remote_tunnel(self):
        """Test creating remote tunnel."""
        tunnel = Tunnel(
            tunnel_type=TunnelType.REMOTE,
            local_port=3000,
            remote_host="localhost",
            remote_port=8080,
        )

        assert tunnel.tunnel_type == TunnelType.REMOTE
        assert tunnel.local_port == 3000
        assert tunnel.remote_port == 8080

    def test_create_dynamic_tunnel(self):
        """Test creating dynamic tunnel (SOCKS5)."""
        tunnel = Tunnel(
            tunnel_type=TunnelType.DYNAMIC,
            local_port=1080,
            remote_host="localhost",
            remote_port=0,
        )

        assert tunnel.tunnel_type == TunnelType.DYNAMIC
        assert tunnel.local_port == 1080

    def test_create_tunnel_invalid_port(self):
        """Test creating tunnel with invalid port."""
        with pytest.raises(ValueError):
            Tunnel(
                tunnel_type=TunnelType.LOCAL,
                local_port=0,
                remote_host="localhost",
                remote_port=80,
            )

    def test_create_tunnel_missing_remote_port(self):
        """Test creating local/remote tunnel without remote port."""
        with pytest.raises(ValueError):
            Tunnel(
                tunnel_type=TunnelType.LOCAL,
                local_port=8080,
                remote_host="localhost",
                remote_port=0,
            )

    def test_tunnel_default_name_generation(self, sample_tunnel_local):
        """Test automatic generation of tunnel name."""
        assert sample_tunnel_local.name
        assert str(sample_tunnel_local.local_port) in sample_tunnel_local.name

    def test_tunnel_to_dict(self, sample_tunnel_local):
        """Test converting tunnel to dictionary."""
        tunnel_dict = sample_tunnel_local.to_dict()

        assert tunnel_dict["tunnel_type"] == sample_tunnel_local.tunnel_type.value
        assert tunnel_dict["local_port"] == sample_tunnel_local.local_port
        assert tunnel_dict["remote_host"] == sample_tunnel_local.remote_host
        assert tunnel_dict["remote_port"] == sample_tunnel_local.remote_port

    def test_tunnel_from_dict(self):
        """Test creating tunnel from dictionary."""
        data = {
            "tunnel_type": "local",
            "local_port": 8080,
            "remote_host": "localhost",
            "remote_port": 80,
            "name": "test_tunnel",
        }

        tunnel = Tunnel.from_dict(data)

        assert tunnel.tunnel_type == TunnelType.LOCAL
        assert tunnel.local_port == 8080
        assert tunnel.remote_host == "localhost"
        assert tunnel.remote_port == 80
        assert tunnel.name == "test_tunnel"

    def test_tunnel_get_ssh_command_args_local(self, sample_tunnel_local):
        """Test getting SSH command arguments for local tunnel."""
        args = sample_tunnel_local.get_ssh_command_args()

        assert "-L" in args
        assert str(sample_tunnel_local.local_port) in args
        assert str(sample_tunnel_local.remote_port) in args

    def test_tunnel_get_ssh_command_args_remote(self, sample_tunnel_remote):
        """Test getting SSH command arguments for remote tunnel."""
        args = sample_tunnel_remote.get_ssh_command_args()

        assert "-R" in args
        assert str(sample_tunnel_remote.remote_port) in args

    def test_tunnel_get_ssh_command_args_dynamic(self, sample_tunnel_dynamic):
        """Test getting SSH command arguments for dynamic tunnel."""
        args = sample_tunnel_dynamic.get_ssh_command_args()

        assert "-D" in args
        assert str(sample_tunnel_dynamic.local_port) in args

    def test_tunnel_uptime_not_started(self, sample_tunnel_local):
        """Test getting uptime when tunnel not started."""
        uptime = sample_tunnel_local.get_uptime()
        assert uptime is None

    def test_tunnel_uptime_started(self, sample_tunnel_local):
        """Test getting uptime when tunnel is started."""
        import time

        sample_tunnel_local.start_time = time.time()
        uptime = sample_tunnel_local.get_uptime()

        assert uptime is not None
        assert uptime >= 0

    def test_tunnel_uptime_string(self, sample_tunnel_local):
        """Test getting formatted uptime string."""
        import time

        sample_tunnel_local.start_time = time.time() - 3665  # 1 hour, 1 minute, 5 seconds
        uptime_str = sample_tunnel_local.get_uptime_string()

        assert "h" in uptime_str or "m" in uptime_str or "s" in uptime_str

    def test_tunnel_format_bytes(self, sample_tunnel_local):
        """Test formatting byte counts."""
        assert "B" in sample_tunnel_local.format_bytes(100)
        assert "KB" in sample_tunnel_local.format_bytes(1024)
        assert "MB" in sample_tunnel_local.format_bytes(1024 * 1024)

    def test_tunnel_equality(self):
        """Test tunnel equality comparison."""
        tunnel1 = Tunnel(
            tunnel_type=TunnelType.LOCAL,
            local_port=8080,
            remote_host="localhost",
            remote_port=80,
        )

        tunnel2 = Tunnel(
            tunnel_type=TunnelType.LOCAL,
            local_port=8080,
            remote_host="localhost",
            remote_port=80,
            name="different_name",
        )

        assert tunnel1 == tunnel2

    def test_tunnel_inequality(self):
        """Test tunnel inequality comparison."""
        tunnel1 = Tunnel(
            tunnel_type=TunnelType.LOCAL,
            local_port=8080,
            remote_host="localhost",
            remote_port=80,
        )

        tunnel2 = Tunnel(
            tunnel_type=TunnelType.LOCAL,
            local_port=9090,
            remote_host="localhost",
            remote_port=80,
        )

        assert tunnel1 != tunnel2
