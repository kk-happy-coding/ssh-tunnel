"""Setup configuration for SSH Tunnel Manager."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ssh-tunnel-manager",
    version="1.0.0",
    author="SSH Tunnel Manager Team",
    author_email="info@sshtunnel.example.com",
    description="Enterprise-grade SSH Port Forwarding GUI for Windows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ssh-tunnel-manager",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Networking",
        "Topic :: Security",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "paramiko>=3.4.0",
        "cryptography>=41.0.0",
        "keyring>=24.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "pytest-timeout>=2.2.0",
            "pylint>=3.0.0",
            "mypy>=1.7.0",
            "black>=23.12.0",
            "isort>=5.13.0",
            "pyinstaller>=6.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ssh-tunnel-manager=src.main:main",
        ],
    },
)
