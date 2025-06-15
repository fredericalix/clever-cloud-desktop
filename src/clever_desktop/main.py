"""
Main Entry Point

Application entry point that sets up Qt, logging, and starts the application.
"""

import sys
import asyncio
import logging

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from .config import get_app_dirs
from .logging_config import setup_logging
from .app import ApplicationManager
from .resources import get_app_icon


def setup_qt_application() -> QApplication:
    """Setup Qt application with proper configuration."""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("Clever Cloud Desktop")
    app.setApplicationDisplayName("Clever Cloud Desktop Manager")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Clever Cloud")
    app.setOrganizationDomain("clever-cloud.com")
    
    # Set application icon
    app.setWindowIcon(get_app_icon())
    
    # Enable high DPI support
    from PySide6.QtCore import Qt
    app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    
    return app


def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler."""
    if issubclass(exc_type, KeyboardInterrupt):
        # Allow Ctrl+C to work
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = logging.getLogger(__name__)
    logger.critical(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )


async def async_main():
    """Async main function that handles application initialization."""
    # Setup logging
    app_dirs = get_app_dirs()
    setup_logging(app_dirs.user_log_dir)
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Starting Clever Cloud Desktop Manager")
    logger.info(f"Data directory: {app_dirs.user_data_dir}")
    logger.info(f"Config directory: {app_dirs.user_config_dir}")
    logger.info(f"Cache directory: {app_dirs.user_cache_dir}")
    logger.info(f"Log directory: {app_dirs.user_log_dir}")
    logger.info("=" * 60)
    
    # Setup Qt application
    qt_app = setup_qt_application()
    
    # Install global exception handler
    sys.excepthook = handle_exception
    
    # Create application manager
    app_manager = ApplicationManager()
    
    try:
        # Initialize application (this will show splash screen and check auth)
        logger.info("Initializing application manager...")
        await app_manager.initialize()
        
        # Setup shutdown handler
        def shutdown_handler():
            logger.info("Shutdown signal received")
            # Schedule shutdown for next event loop iteration
            QTimer.singleShot(0, lambda: asyncio.create_task(app_manager.shutdown()))
        
        # Connect Qt signals
        qt_app.aboutToQuit.connect(shutdown_handler)
        
        # Start Qt event loop
        logger.info("Starting Qt event loop...")
        
        # Use QTimer to allow async operations
        timer = QTimer()
        timer.timeout.connect(lambda: None)
        timer.start(100)  # Process async events every 100ms
        
        exit_code = qt_app.exec()
        
        logger.info(f"Application exited with code: {exit_code}")
        return exit_code
        
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    finally:
        # Ensure cleanup
        try:
            await app_manager.shutdown()
        except Exception as e:
            logger.error(f"Error during final cleanup: {e}")


def main():
    """Main entry point."""
    try:
        # Run async main
        if sys.platform == "win32":
            # Windows specific event loop policy
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        exit_code = asyncio.run(async_main())
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 