.PHONY: help install install-dev test lint format coverage build clean all

help:
	@echo "SSH Tunnel Manager - Makefile Commands"
	@echo "======================================="
	@echo "make install       - Install runtime dependencies"
	@echo "make install-dev   - Install development dependencies"
	@echo "make test          - Run all tests"
	@echo "make test-unit     - Run unit tests only"
	@echo "make test-integration - Run integration tests only"
	@echo "make test-gui      - Run GUI tests only"
	@echo "make test-security - Run security tests only"
	@echo "make test-performance - Run performance tests only"
	@echo "make lint          - Run pylint and mypy"
	@echo "make format        - Format code with black and isort"
	@echo "make coverage      - Generate coverage report"
	@echo "make build         - Build Windows .exe"
	@echo "make clean         - Clean build artifacts"
	@echo "make all           - Format, lint, test, and build"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v -m unit

test-integration:
	pytest tests/integration/ -v -m integration

test-gui:
	pytest tests/gui/ -v -m gui

test-security:
	pytest tests/security/ -v -m security

test-performance:
	pytest tests/performance/ -v -m performance

lint:
	@echo "Running pylint..."
	pylint src/ --rcfile=.pylintrc
	@echo "Running mypy..."
	mypy src/ --config-file=mypy.ini

format:
	@echo "Running isort..."
	isort src/ tests/
	@echo "Running black..."
	black src/ tests/

coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

build:
	@echo "Building Windows executable..."
	python -m PyInstaller --clean --noconfirm build.spec || \
	pyinstaller --name="SSH-Tunnel-Manager" \
		--onefile \
		--windowed \
		--icon=resources/icon.ico \
		--add-data="resources;resources" \
		--hidden-import=tkinter \
		--hidden-import=paramiko \
		--hidden-import=cryptography \
		--hidden-import=keyring \
		src/main.py

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

all: format lint test build
	@echo "All tasks completed successfully!"
