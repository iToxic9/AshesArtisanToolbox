"""
Main application entry point for Ashes of Creation Artisan Toolbox.
PyQt6-based desktop application for crafting calculations and inventory management.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from gui.main_window import MainWindow
from data_manager import DataManager
from settings_manager import get_settings_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('artisan_toolbox.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ArtisanToolboxApp(QApplication):
    """
    Main application class that manages the PyQt6 application lifecycle
    and coordinates with the data management system.
    """
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # Application metadata
        self.setApplicationName("Ashes of Creation Artisan Toolbox")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("AshesArtisanToolbox")
        
        # Application state
        self.data_manager: Optional[DataManager] = None
        self.main_window: Optional[MainWindow] = None
        self.settings_manager = get_settings_manager()
        
        # Setup application
        self.setup_application()
    
    def setup_application(self):
        """Initialize application components"""
        try:
            # Initialize data manager
            self.data_manager = DataManager()
            
            # Create main window
            self.main_window = MainWindow(self.data_manager)
            
            # Setup application icon (if available)
            self.setup_icon()
            
            # Setup application styling
            self.setup_styling()
            
            logger.info("Application initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            self.quit()
    
    def setup_icon(self):
        """Setup application icon"""
        icon_path = Path("resources/icon.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
    
    def setup_styling(self):
        """Setup application styling and theme"""
        # Get theme from settings
        theme_style = self.settings_manager.get_theme_style()
        self.setStyleSheet(theme_style)
    
    def run(self):
        """Start the application"""
        try:
            # Show main window
            self.main_window.show()
            
            # Initialize data manager in background
            self.main_window.initialize_data_manager()
            
            # Start event loop
            return self.exec()
            
        except Exception as e:
            logger.error(f"Application runtime error: {e}")
            return 1
    
    def closeEvent(self, event):
        """Handle application close event"""
        logger.info("Application closing...")
        event.accept()


def main():
    """Main entry point"""
    try:
        # Create and run application
        app = ArtisanToolboxApp(sys.argv)
        exit_code = app.run()
        
        logger.info(f"Application exited with code: {exit_code}")
        return exit_code
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Application crashed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())