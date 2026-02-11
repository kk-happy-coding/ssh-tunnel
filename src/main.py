"""Main entry point for SSH Tunnel Manager."""

import sys
import tkinter as tk
from pathlib import Path

from src.gui.main_window import MainWindow
from src.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code
    """
    try:
        # Setup logging
        setup_logging()

        logger.info("Starting SSH Tunnel Manager...")

        # Create root window
        root = tk.Tk()

        # Create main window
        app = MainWindow(root)

        # Run application
        app.run()

        logger.info("SSH Tunnel Manager stopped")
        return 0

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
