@echo off
REM Build script for SSH Tunnel Manager Windows executable

echo Building SSH Tunnel Manager...
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec"

REM Build the executable
pyinstaller --name="SSH-Tunnel-Manager" ^
    --onefile ^
    --windowed ^
    --icon=resources/icon.ico ^
    --add-data="resources;resources" ^
    --hidden-import=tkinter ^
    --hidden-import=paramiko ^
    --hidden-import=cryptography ^
    --hidden-import=keyring ^
    --hidden-import=keyring.backends.Windows ^
    src/main.py

if errorlevel 1 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Executable location: dist\SSH-Tunnel-Manager.exe
echo.
pause
