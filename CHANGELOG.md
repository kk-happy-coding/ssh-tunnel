# Changelog

All notable changes to SSH Tunnel Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-02-11

### Added
- Initial release of SSH Tunnel Manager
- Complete SSH connection management with multiple authentication methods
  - Password authentication
  - Private key authentication (RSA, DSA, ECDSA, Ed25519)
  - Key with passphrase
  - SSH agent support
- All three tunnel types supported
  - Local port forwarding (-L)
  - Remote port forwarding (-R)
  - Dynamic port forwarding / SOCKS5 proxy (-D)
- Profile management system
  - Save and load connection profiles
  - Encrypted profile storage (AES-256)
  - Import/export profiles
  - Recent connections list
- Secure credential storage
  - Windows Credential Manager integration
  - Passwords never stored in plain text
  - Memory cleanup for sensitive data
- Real-time tunnel monitoring
  - Health checks every 15 seconds
  - Auto-reconnect with exponential backoff
  - Bandwidth tracking (bytes in/out)
  - Uptime display
- Modern GUI with Tkinter
  - Dark and light themes
  - Responsive layout
  - Color-coded log console
  - System tray integration
  - Keyboard shortcuts
- Export functionality
  - SSH command generation
  - Windows Batch script export
  - PowerShell script export
  - SSH config file generation
- Comprehensive input validation
  - Host, port, username validation
  - Key file format verification
  - Protection against injection attacks
  - Path traversal prevention
- Configuration management
  - Persistent user preferences
  - Window position/size memory
  - Customizable timeouts and intervals
- Logging system
  - Rotating file logs (5MB max, 5 backups)
  - Sensitive data redaction
  - Multiple log levels
  - GUI log panel with filtering
- Comprehensive test suite
  - 90%+ code coverage
  - Unit tests for all modules
  - Integration tests
  - Security tests
  - Performance tests
- Build system
  - PyInstaller configuration
  - Windows .exe generation
  - Makefile for common tasks
  - Batch build script
- Complete documentation
  - README with usage guide
  - Inline code documentation
  - Type hints throughout
  - Architecture overview

### Security
- AES-256 encryption for stored profiles
- Windows Credential Manager for passwords
- Input validation to prevent injection
- Host key verification
- Known hosts file management
- Memory cleanup for sensitive data

### Performance
- Multi-threaded tunnel management
- Non-blocking GUI operations
- Efficient port checking
- Minimal memory footprint

### Developer Experience
- Type hints on all functions
- Comprehensive docstrings
- Linting with pylint and mypy
- Code formatting with black and isort
- Pre-configured VS Code settings
- Git hooks for quality checks

## [Unreleased]

### Planned Features
- Multi-platform support (Linux, macOS)
- SSH config file import
- Tunnel statistics graphs
- Notifications for connection events
- Automatic update checking
- Dark mode improvements
- More export formats
- Tunnel templates
- Bulk operations
- Command-line interface
- REST API for automation

### Known Issues
- None currently identified

---

## Version History

- **1.0.0** (2025-02-11): Initial release

## Upgrade Guide

### From 0.x to 1.0.0
This is the first stable release. No upgrade path necessary.

## Breaking Changes

None in this release.

## Deprecations

None in this release.

## Security Advisories

None at this time. Security issues should be reported to security@example.com.

---

For detailed commit history, see: https://github.com/yourusername/ssh-tunnel-manager/commits/main
