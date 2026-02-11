"""Logging utilities for SSH Tunnel Manager."""

import logging
import re
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from src.utils.constants import (
    LOG_DATE_FORMAT,
    LOG_DIR,
    LOG_FILE_BACKUP_COUNT,
    LOG_FILE_MAX_BYTES,
    LOG_FORMAT,
    PASSWORD_REDACTED,
)


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive data from log messages."""

    # Patterns to detect sensitive data
    SENSITIVE_PATTERNS = [
        (re.compile(r"password['\"]?\s*[:=]\s*['\"]?([^'\"\\s]+)", re.IGNORECASE), PASSWORD_REDACTED),
        (re.compile(r"passwd['\"]?\s*[:=]\s*['\"]?([^'\"\\s]+)", re.IGNORECASE), PASSWORD_REDACTED),
        (re.compile(r"passphrase['\"]?\s*[:=]\s*['\"]?([^'\"\\s]+)", re.IGNORECASE), PASSWORD_REDACTED),
        (re.compile(r"secret['\"]?\s*[:=]\s*['\"]?([^'\"\\s]+)", re.IGNORECASE), PASSWORD_REDACTED),
        (re.compile(r"token['\"]?\s*[:=]\s*['\"]?([^'\"\\s]+)", re.IGNORECASE), PASSWORD_REDACTED),
        (re.compile(r"key['\"]?\s*[:=]\s*['\"]?([^'\"\\s]+)", re.IGNORECASE), PASSWORD_REDACTED),
        (re.compile(r"-----BEGIN.*PRIVATE KEY-----.*-----END.*PRIVATE KEY-----", re.DOTALL), PASSWORD_REDACTED),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record to redact sensitive data.

        Args:
            record: Log record to filter

        Returns:
            True (always allow the record, just modify it)
        """
        if record.msg:
            message = str(record.msg)
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                message = pattern.sub(replacement, message)
            record.msg = message

        if record.args:
            filtered_args = []
            for arg in record.args:
                arg_str = str(arg)
                for pattern, replacement in self.SENSITIVE_PATTERNS:
                    arg_str = pattern.sub(replacement, arg_str)
                filtered_args.append(arg_str)
            record.args = tuple(filtered_args)

        return True


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console: bool = True,
) -> None:
    """
    Set up application logging.

    Args:
        log_level: Logging level (default: INFO)
        log_file: Path to log file (default: LOG_DIR/app.log)
        console: Whether to also log to console
    """
    # Create log directory
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if log_file is None:
        log_file = LOG_DIR / "app.log"

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers = []

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Create sensitive data filter
    sensitive_filter = SensitiveDataFilter()

    # File handler with rotation
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=LOG_FILE_MAX_BYTES,
            backupCount=LOG_FILE_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(sensitive_filter)
        root_logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not create log file: {e}", file=sys.stderr)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(sensitive_filter)
        root_logger.addHandler(console_handler)

    # Set level for noisy libraries
    logging.getLogger("paramiko").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class GUILogHandler(logging.Handler):
    """Custom logging handler that sends logs to GUI text widget."""

    def __init__(self, text_widget: Optional[object] = None) -> None:
        """
        Initialize GUI log handler.

        Args:
            text_widget: Tkinter Text widget to write logs to
        """
        super().__init__()
        self.text_widget = text_widget
        self.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
        self.addFilter(SensitiveDataFilter())

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to the GUI text widget.

        Args:
            record: Log record to emit
        """
        if self.text_widget is None:
            return

        try:
            msg = self.format(record)
            # Thread-safe insertion into Tkinter widget
            self.text_widget.after(
                0, lambda: self._insert_log(msg, record.levelname)
            )
        except Exception:
            self.handleError(record)

    def _insert_log(self, message: str, level: str) -> None:
        """
        Insert log message into text widget (must run in GUI thread).

        Args:
            message: Formatted log message
            level: Log level name
        """
        if self.text_widget is None:
            return

        try:
            # Map log levels to text tags
            tag = level.lower()

            # Insert the message
            self.text_widget.insert("end", message + "\n", tag)

            # Auto-scroll to the bottom
            self.text_widget.see("end")

            # Limit text widget size (keep last 10000 lines)
            lines = int(self.text_widget.index("end-1c").split(".")[0])
            if lines > 10000:
                self.text_widget.delete("1.0", f"{lines - 10000}.0")
        except Exception:
            pass  # Fail silently if widget is destroyed
