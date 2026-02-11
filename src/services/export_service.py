"""Export service for generating SSH commands and scripts."""

from pathlib import Path
from typing import List

from src.models.connection import Connection
from src.models.tunnel import Tunnel
from src.utils.constants import TunnelType
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExportService:
    """Service for exporting tunnels as commands and scripts."""

    @staticmethod
    def generate_ssh_command(connection: Connection, tunnels: List[Tunnel]) -> str:
        """
        Generate SSH command for tunnels.

        Args:
            connection: SSH connection
            tunnels: List of tunnels

        Returns:
            SSH command string
        """
        parts = ["ssh"]

        # Add tunnel arguments
        for tunnel in tunnels:
            parts.append(tunnel.get_ssh_command_args())

        # Add connection details
        if connection.port != 22:
            parts.extend(["-p", str(connection.port)])

        # Add key file if using key authentication
        if connection.key_file:
            parts.extend(["-i", f'"{connection.key_file}"'])

        # Add user@host
        if connection.username:
            parts.append(f"{connection.username}@{connection.host}")
        else:
            parts.append(connection.host)

        # Add options
        parts.extend(["-N", "-v"])  # No command execution, verbose

        return " ".join(parts)

    @staticmethod
    def generate_batch_script(connection: Connection, tunnels: List[Tunnel]) -> str:
        """
        Generate Windows batch script.

        Args:
            connection: SSH connection
            tunnels: List of tunnels

        Returns:
            Batch script content
        """
        script_lines = [
            "@echo off",
            "REM SSH Tunnel Manager - Generated Batch Script",
            f"REM Connection: {connection.get_connection_string()}",
            f"REM Generated: {ExportService._get_timestamp()}",
            "",
            "echo Starting SSH tunnels...",
            "echo.",
        ]

        # Generate SSH command
        ssh_command = ExportService.generate_ssh_command(connection, tunnels)

        # Add tunnels info
        for tunnel in tunnels:
            script_lines.append(f"REM Tunnel: {tunnel.name}")

        script_lines.extend([
            "",
            "REM Execute SSH command",
            ssh_command,
            "",
            "if errorlevel 1 (",
            "    echo.",
            "    echo ERROR: SSH connection failed!",
            "    pause",
            "    exit /b 1",
            ")",
            "",
            "echo.",
            "echo Tunnels established successfully",
            "echo Press Ctrl+C to stop...",
            "pause",
        ])

        return "\n".join(script_lines)

    @staticmethod
    def generate_powershell_script(connection: Connection, tunnels: List[Tunnel]) -> str:
        """
        Generate PowerShell script.

        Args:
            connection: SSH connection
            tunnels: List of tunnels

        Returns:
            PowerShell script content
        """
        script_lines = [
            "# SSH Tunnel Manager - Generated PowerShell Script",
            f"# Connection: {connection.get_connection_string()}",
            f"# Generated: {ExportService._get_timestamp()}",
            "",
            "$ErrorActionPreference = 'Stop'",
            "",
            "Write-Host 'Starting SSH tunnels...' -ForegroundColor Green",
            "Write-Host ''",
        ]

        # Add tunnels info
        for i, tunnel in enumerate(tunnels, 1):
            script_lines.append(f"Write-Host 'Tunnel {i}: {tunnel.name}' -ForegroundColor Cyan")

        # Generate SSH command
        ssh_command = ExportService.generate_ssh_command(connection, tunnels)

        script_lines.extend([
            "",
            "# Execute SSH command",
            "try {",
            f"    & {ssh_command}",
            "}",
            "catch {",
            "    Write-Host ''",
            "    Write-Host 'ERROR: SSH connection failed!' -ForegroundColor Red",
            "    Write-Host $_.Exception.Message -ForegroundColor Red",
            "    Read-Host -Prompt 'Press Enter to exit'",
            "    exit 1",
            "}",
            "",
            "Write-Host ''",
            "Write-Host 'Tunnels established successfully' -ForegroundColor Green",
            "Write-Host 'Press Ctrl+C to stop...' -ForegroundColor Yellow",
            "Read-Host -Prompt 'Press Enter to exit'",
        ])

        return "\n".join(script_lines)

    @staticmethod
    def generate_ssh_config(connection: Connection, tunnels: List[Tunnel], config_name: str) -> str:
        """
        Generate SSH config file entry.

        Args:
            connection: SSH connection
            tunnels: List of tunnels
            config_name: Name for the config entry

        Returns:
            SSH config content
        """
        config_lines = [
            f"# SSH Tunnel Manager - Generated SSH Config",
            f"# Generated: {ExportService._get_timestamp()}",
            "",
            f"Host {config_name}",
            f"    HostName {connection.host}",
            f"    Port {connection.port}",
        ]

        if connection.username:
            config_lines.append(f"    User {connection.username}")

        if connection.key_file:
            config_lines.append(f"    IdentityFile {connection.key_file}")

        # Add tunnel forwards
        for tunnel in tunnels:
            if tunnel.tunnel_type == TunnelType.LOCAL:
                config_lines.append(
                    f"    LocalForward {tunnel.bind_address}:{tunnel.local_port} "
                    f"{tunnel.remote_host}:{tunnel.remote_port}"
                )
            elif tunnel.tunnel_type == TunnelType.REMOTE:
                config_lines.append(
                    f"    RemoteForward {tunnel.remote_port} "
                    f"{tunnel.remote_host}:{tunnel.local_port}"
                )
            elif tunnel.tunnel_type == TunnelType.DYNAMIC:
                config_lines.append(f"    DynamicForward {tunnel.bind_address}:{tunnel.local_port}")

        config_lines.extend([
            "    ServerAliveInterval 30",
            "    ServerAliveCountMax 3",
            "    ExitOnForwardFailure yes",
            "",
        ])

        return "\n".join(config_lines)

    @staticmethod
    def export_to_file(content: str, file_path: Path) -> None:
        """
        Export content to file.

        Args:
            content: Content to export
            file_path: Path to export to
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Exported to {file_path}")

        except Exception as e:
            logger.error(f"Failed to export to file: {e}")
            raise

    @staticmethod
    def export_ssh_command(connection: Connection, tunnels: List[Tunnel], file_path: Path) -> None:
        """
        Export SSH command to file.

        Args:
            connection: SSH connection
            tunnels: List of tunnels
            file_path: Path to export to
        """
        command = ExportService.generate_ssh_command(connection, tunnels)

        content = [
            "# SSH Tunnel Manager - Generated SSH Command",
            f"# Connection: {connection.get_connection_string()}",
            f"# Generated: {ExportService._get_timestamp()}",
            "",
            command,
        ]

        ExportService.export_to_file("\n".join(content), file_path)

    @staticmethod
    def export_batch_script(connection: Connection, tunnels: List[Tunnel], file_path: Path) -> None:
        """
        Export batch script to file.

        Args:
            connection: SSH connection
            tunnels: List of tunnels
            file_path: Path to export to
        """
        script = ExportService.generate_batch_script(connection, tunnels)
        ExportService.export_to_file(script, file_path)

    @staticmethod
    def export_powershell_script(connection: Connection, tunnels: List[Tunnel], file_path: Path) -> None:
        """
        Export PowerShell script to file.

        Args:
            connection: SSH connection
            tunnels: List of tunnels
            file_path: Path to export to
        """
        script = ExportService.generate_powershell_script(connection, tunnels)
        ExportService.export_to_file(script, file_path)

    @staticmethod
    def export_ssh_config(
        connection: Connection,
        tunnels: List[Tunnel],
        file_path: Path,
        config_name: str,
    ) -> None:
        """
        Export SSH config to file.

        Args:
            connection: SSH connection
            tunnels: List of tunnels
            file_path: Path to export to
            config_name: Name for the config entry
        """
        config = ExportService.generate_ssh_config(connection, tunnels, config_name)
        ExportService.export_to_file(config, file_path)

    @staticmethod
    def _get_timestamp() -> str:
        """
        Get current timestamp string.

        Returns:
            Formatted timestamp
        """
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def escape_shell_arg(arg: str) -> str:
        """
        Escape shell argument for safe use in commands.

        Args:
            arg: Argument to escape

        Returns:
            Escaped argument
        """
        # Simple escaping for common cases
        if " " in arg or '"' in arg or "'" in arg:
            return f'"{arg.replace('"', '\\"')}"'
        return arg
