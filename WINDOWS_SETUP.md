# Windows Setup Guide for SSH Tunnel Manager

This guide will help you build and run SSH Tunnel Manager on your Windows PC.

## Prerequisites

1. **Python 3.10 or higher**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **Git** (optional, for cloning)
   - Download from: https://git-scm.com/download/win

## Quick Start

### Option 1: Install and Run from Source

1. **Open Command Prompt or PowerShell**

2. **Navigate to the project directory**
   ```cmd
   cd path\to\ssh-tunnel-manager
   ```

3. **Install dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```cmd
   python src\main.py
   ```

### Option 2: Build Standalone Executable

1. **Install build dependencies**
   ```cmd
   pip install -r requirements-dev.txt
   ```

2. **Run the build script**
   ```cmd
   build.bat
   ```

3. **Find the executable**
   - Location: `dist\SSH-Tunnel-Manager.exe`
   - Double-click to run

## Troubleshooting

### "pip is not recognized"
- Reinstall Python and check "Add Python to PATH"
- Or add Python to PATH manually:
  - `C:\Users\YourName\AppData\Local\Programs\Python\Python3XX\`
  - `C:\Users\YourName\AppData\Local\Programs\Python\Python3XX\Scripts\`

### "python is not recognized"
- Same fix as above

### ImportError: No module named 'tkinter'
- Tkinter comes with Python on Windows
- If missing, reinstall Python with "tcl/tk and IDLE" option checked

### "ModuleNotFoundError: No module named 'paramiko'"
- Run: `pip install -r requirements.txt`

### Permission errors when installing packages
- Run Command Prompt as Administrator
- Or use: `pip install --user -r requirements.txt`

### Build fails with PyInstaller
- Make sure you're in the project root directory
- Check that all dependencies are installed:
  ```cmd
  pip list | findstr paramiko
  pip list | findstr cryptography
  pip list | findstr keyring
  ```

### Application won't start
1. **Check Python version**
   ```cmd
   python --version
   ```
   Should be 3.10 or higher

2. **Test imports**
   ```cmd
   python test_app.py
   ```

3. **Check error messages in console**

## Running Tests

```cmd
REM Install test dependencies
pip install pytest pytest-cov

REM Run all tests
pytest

REM Run specific test suite
pytest tests\unit\ -v

REM Run with coverage
pytest --cov=src --cov-report=html
```

## Building for Distribution

The build process creates a standalone .exe file that doesn't require Python to be installed on the target machine.

```cmd
REM Clean previous builds
rmdir /s /q build dist

REM Build
build.bat

REM Test the executable
dist\SSH-Tunnel-Manager.exe
```

## Directory Structure After Build

```
ssh-tunnel-manager\
├── src\              (source code)
├── tests\            (test suite)
├── dist\             (built executable)
│   └── SSH-Tunnel-Manager.exe
├── build\            (build artifacts - can be deleted)
└── resources\        (icons and config)
```

## First Run Configuration

On first run, the application will create:
- `C:\Users\YourName\.ssh-tunnel-manager\config.json` (settings)
- `C:\Users\YourName\.ssh-tunnel-manager\logs\` (log files)
- `C:\Users\YourName\.ssh-tunnel-manager\profiles\` (saved profiles)

## Using the Application

### 1. Create an SSH Connection

1. **Fill in connection details:**
   - Host: Your SSH server (e.g., example.com or 192.168.1.100)
   - Port: SSH port (usually 22)
   - Username: Your SSH username
   - Auth: Choose "password" or "key_file"
   - Password/Key: Enter credentials

2. **Test the connection (optional):**
   - Click "Test Connection" to verify credentials

3. **Click "Connect"**

### 2. Add a Tunnel

1. **Select tunnel type:**
   - **Local (-L)**: Forward local port to remote destination
   - **Remote (-R)**: Forward remote port to local destination
   - **Dynamic (-D)**: SOCKS5 proxy

2. **Configure ports:**
   - Local Port: Port on your machine
   - Remote Host: Destination host (usually "localhost")
   - Remote Port: Destination port

3. **Click "Add Tunnel"**

### 3. Save a Profile (Optional)

1. Go to **File → Save Profile**
2. Enter a name for your profile
3. Credentials are stored securely in Windows Credential Manager

### 4. Export Configuration (Optional)

1. **Tools → Export SSH Command**
   - Get the equivalent SSH command
   - Copy to clipboard

2. **Tools → Export Batch Script**
   - Create a .bat file to run tunnels
   - Double-click to start tunnels from Windows Explorer

## Example Configurations

### Web Development - Forward Local Port to Remote Server

**Scenario:** Access a web server running on your remote server
- Type: Local
- Local Port: 8080
- Remote Host: localhost
- Remote Port: 80

**Result:** Access remote web server at `http://localhost:8080`

### Database Access - Forward Database Port

**Scenario:** Connect to remote MySQL database
- Type: Local
- Local Port: 3307
- Remote Host: localhost
- Remote Port: 3306

**Result:** Connect to database at `localhost:3307`

### SOCKS5 Proxy - Browse Through SSH

**Scenario:** Route all traffic through SSH server
- Type: Dynamic
- Local Port: 1080

**Result:** Configure browser to use SOCKS5 proxy at `localhost:1080`

## Security Notes

1. **Credentials are stored securely:**
   - Passwords: Windows Credential Manager
   - Profiles: AES-256 encrypted

2. **Best practices:**
   - Use SSH keys instead of passwords when possible
   - Keep your private keys in `C:\Users\YourName\.ssh\`
   - Set proper permissions on key files (right-click → Properties → Security)

3. **Firewall:**
   - Windows may ask to allow Python/SSH-Tunnel-Manager through firewall
   - Click "Allow" for private networks

## Getting Help

If you encounter issues:

1. Check the log files:
   - `C:\Users\YourName\.ssh-tunnel-manager\logs\app.log`

2. Run in verbose mode:
   ```cmd
   python src\main.py
   ```
   (console will show debug output)

3. Run tests to verify installation:
   ```cmd
   pytest tests\unit\ -v
   ```

4. Check the issues page:
   - https://github.com/yourusername/ssh-tunnel-manager/issues

## Uninstalling

1. Delete the application folder
2. Delete configuration folder:
   ```cmd
   rmdir /s /q "%USERPROFILE%\.ssh-tunnel-manager"
   ```
3. Remove stored credentials (Windows Credential Manager):
   - Press Windows key + R
   - Type: `control /name Microsoft.CredentialManager`
   - Look for entries starting with "ssh-tunnel-manager"

---

**Need more help?** Open an issue on GitHub or check the full README.md
