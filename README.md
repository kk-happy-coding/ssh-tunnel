# SSH Tunnel Manager

Enterprise-grade SSH Port Forwarding GUI for Windows

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Features

### Core Functionality
- **Complete SSH Support**: Password, private key (RSA/Ed25519/ECDSA), key with passphrase, and SSH agent authentication
- **All Tunnel Types**: Local (-L), Remote (-R), and Dynamic (-D SOCKS5) port forwarding
- **Connection Management**: Full lifecycle with keepalive, timeout configuration, and auto-reconnect
- **Profile Management**: Save, load, and manage connection profiles with encrypted credential storage
- **Real-time Monitoring**: Tunnel health checks, bandwidth tracking, uptime display, and status indicators

### Security Features
- **Encrypted Storage**: AES-256 encryption for profiles at rest
- **Secure Credentials**: Windows Credential Manager integration via keyring
- **Input Validation**: Comprehensive validation to prevent injection attacks
- **Host Key Verification**: SSH fingerprint verification and known_hosts management
- **Memory Protection**: Sensitive data cleared from memory after use

### User Interface
- **Modern GUI**: Clean, responsive Tkinter-based interface with dark/light themes
- **Real-time Logs**: Color-coded log console with filtering and export capabilities
- **Status Indicators**: Visual connection and tunnel status with detailed information
- **Keyboard Shortcuts**: Productivity shortcuts for common operations
- **System Tray**: Minimize to tray with quick access menu

### DevOps & Export
- **SSH Command Export**: Copy-ready SSH command strings
- **Script Generation**: Export as Windows Batch (.bat) or PowerShell (.ps1) scripts
- **SSH Config Export**: Generate ~/.ssh/config entries
- **Profile Import/Export**: Share profiles across machines

## Installation

### Requirements
- Python 3.10 or higher
- Windows 10/11
- SSH client (OpenSSH recommended)

### Quick Install

```bash
# Clone repository
git clone https://github.com/yourusername/ssh-tunnel-manager.git
cd ssh-tunnel-manager

# Install dependencies
pip install -r requirements.txt

# Run application
python src/main.py
```

### Development Install

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linters
make lint

# Format code
make format

# Build executable
make build
```

## Usage

### Basic Connection

1. **Enter Connection Details**
   - Host: SSH server hostname or IP
   - Port: SSH port (default: 22)
   - Username: SSH username
   - Auth: Choose password or key file

2. **Configure Tunnels**
   - Select tunnel type: Local, Remote, or Dynamic
   - Enter local port and remote destination
   - Click "Add Tunnel"

3. **Connect**
   - Click "Connect" to establish SSH connection
   - Tunnels will start automatically

### Profile Management

**Save Profile:**
```
File → Save Profile
Enter profile name
Credentials stored securely in Windows Credential Manager
```

**Load Profile:**
```
File → Open Profile
Select from saved profiles
One-click connection with all tunnels
```

### Export Options

**SSH Command:**
```
Tools → Export SSH Command
Copy command to clipboard
Paste in terminal for manual execution
```

**Batch Script:**
```
Tools → Export Batch Script
Save as .bat file
Double-click to launch tunnels
```

## Configuration

### Settings File
Location: `~/.ssh-tunnel-manager/config.json`

Default settings:
```json
{
  "theme": "light",
  "connection_timeout": 10,
  "keepalive_interval": 30,
  "auto_reconnect": true,
  "max_reconnect_attempts": 5,
  "log_level": "INFO"
}
```

### Profiles
Location: `~/.ssh-tunnel-manager/profiles/`

Profiles are stored as encrypted JSON files. Passwords and passphrases are stored separately in Windows Credential Manager.

## Architecture

```
ssh-tunnel-manager/
├── src/
│   ├── core/           # SSH and tunnel management
│   ├── models/         # Data models (Connection, Tunnel, Profile)
│   ├── services/       # Business logic services
│   ├── utils/          # Utilities (validation, logging, crypto)
│   ├── gui/            # GUI components
│   └── main.py         # Application entry point
├── tests/              # Comprehensive test suite (≥90% coverage)
└── resources/          # Icons and assets
```

### Key Components

- **SSHManager**: Handles SSH connections using Paramiko
- **TunnelManager**: Manages port forwarding threads
- **TunnelMonitor**: Health checks and auto-reconnect
- **CredentialStore**: Secure credential storage
- **ProfileService**: Profile CRUD operations

## Development

### Running Tests

```bash
# All tests
pytest

# Unit tests only
make test-unit

# With coverage
make coverage

# Specific test file
pytest tests/unit/test_validators.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint
pylint src/
mypy src/

# All quality checks
make lint
```

### Building Executable

```bash
# Windows batch script
./build.bat

# Or using Make
make build

# Output: dist/SSH-Tunnel-Manager.exe
```

## Testing

### Test Coverage
- **Unit Tests**: 90%+ coverage for all modules
- **Integration Tests**: Full workflow testing
- **Security Tests**: Injection protection, encryption validation
- **Performance Tests**: Memory leak detection, responsiveness checks

### Running Specific Tests

```bash
# Validators
pytest tests/unit/test_validators.py -v

# Models
pytest tests/unit/test_connection_model.py -v

# Security
pytest tests/security/ -v -m security

# Performance
pytest tests/performance/ -v -m performance
```

## Security

### Best Practices
- Never store credentials in plain text
- Always use SSH key authentication when possible
- Verify host fingerprints on first connection
- Keep private keys in secure locations with proper permissions
- Regularly update dependencies

### Vulnerability Reporting
Please report security vulnerabilities to: security@example.com

## Troubleshooting

### Connection Issues
```
Issue: "Connection timed out"
Solution: Check firewall settings, increase timeout in settings

Issue: "Authentication failed"
Solution: Verify username/password, check key file permissions

Issue: "Port already in use"
Solution: Check which process is using the port, choose different port
```

### Tunnel Issues
```
Issue: "Tunnel drops frequently"
Solution: Enable auto-reconnect, check network stability

Issue: "Cannot forward privileged port"
Solution: Use port > 1024 or run with admin privileges
```

## FAQ

**Q: Can I use this on Linux/Mac?**
A: The application is designed for Windows but can be adapted for other platforms by modifying the credential storage backend.

**Q: Is my password stored securely?**
A: Yes. Passwords are stored in Windows Credential Manager using the keyring library and never saved to disk in plain text.

**Q: Can I run multiple SSH connections simultaneously?**
A: Yes. Each connection runs independently with its own set of tunnels.

**Q: What SSH key formats are supported?**
A: RSA, DSA, ECDSA, and Ed25519 keys in PEM or OpenSSH format.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass and coverage remains ≥90%
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details

## Credits

Built with:
- [Paramiko](https://www.paramiko.org/) - SSH implementation
- [cryptography](https://cryptography.io/) - Encryption
- [keyring](https://github.com/jaraco/keyring) - Credential storage
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - GUI framework

## Support

- Documentation: https://github.com/yourusername/ssh-tunnel-manager/wiki
- Issues: https://github.com/yourusername/ssh-tunnel-manager/issues
- Discussions: https://github.com/yourusername/ssh-tunnel-manager/discussions

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

---

**SSH Tunnel Manager** - Making SSH port forwarding simple and secure.
