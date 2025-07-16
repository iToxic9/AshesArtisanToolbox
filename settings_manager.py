"""
Settings Manager for user preferences and application configuration.
Provides centralized settings management with database persistence.
"""

import logging
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

from database import ArtisanDatabase

logger = logging.getLogger(__name__)

class Theme(Enum):
    """Available application themes"""
    DARK = "dark"
    LIGHT = "light"
    AUTO = "auto"

class Profession(Enum):
    """Available professions for filtering"""
    ALL = "All Professions"
    SCRIBE = "Scribe" 
    ALCHEMIST = "Alchemist"
    BLACKSMITH = "Blacksmith"
    CARPENTER = "Carpenter"
    JEWELER = "Jeweler"
    LEATHERWORKER = "Leatherworker"
    TAILOR = "Tailor"
    COOK = "Cook"

@dataclass
class UserSettings:
    """User preference settings with defaults"""
    
    # UI Preferences
    theme: str = Theme.DARK.value
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    
    # Profession Preferences  
    default_profession: str = Profession.SCRIBE.value
    profession_filter_enabled: bool = True
    
    # Calculation Preferences
    default_tax_rate: float = 15.0  # percentage
    auto_update_prices: bool = True
    use_inventory_constraints: bool = True
    
    # API Preferences
    auto_sync_enabled: bool = True
    sync_interval_hours: int = 24
    api_timeout_seconds: int = 15
    api_rate_limit_seconds: float = 1.5
    
    # Cache Preferences
    cache_enabled: bool = True
    cache_max_age_hours: int = 24
    auto_clear_cache: bool = False
    
    # Notification Preferences
    show_low_stock_alerts: bool = True
    show_price_alerts: bool = True
    show_sync_notifications: bool = True
    
    # Advanced Preferences
    debug_mode: bool = False
    log_level: str = "INFO"
    backup_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSettings':
        """Create settings from dictionary"""
        # Filter only known fields to handle version differences
        known_fields = set(cls.__annotations__.keys())
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered_data)

class SettingsManager:
    """
    Centralized settings management with database persistence.
    Handles user preferences, application configuration, and theme management.
    """
    
    def __init__(self, db_path: str = "artisan_toolbox.db"):
        self.db_path = db_path
        self._settings: Optional[UserSettings] = None
        self._callbacks: Dict[str, list] = {}  # Setting change callbacks
    
    def load_settings(self) -> UserSettings:
        """Load user settings from database"""
        if self._settings is not None:
            return self._settings
        
        try:
            with ArtisanDatabase(self.db_path) as db:
                settings_data = {}
                
                # Load all settings from database
                cursor = db.connection.execute("SELECT key, value FROM settings")
                for key, value in cursor.fetchall():
                    # Convert stored string values back to appropriate types
                    settings_data[key] = self._deserialize_value(key, value)
                
                # Create settings object with loaded data
                if settings_data:
                    self._settings = UserSettings.from_dict(settings_data)
                    logger.info("Settings loaded from database")
                else:
                    # Use defaults for first run
                    self._settings = UserSettings()
                    logger.info("Using default settings for first run")
                    self.save_settings()  # Save defaults to database
                
                return self._settings
                
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            # Fallback to defaults
            self._settings = UserSettings()
            return self._settings
    
    def save_settings(self) -> bool:
        """Save current settings to database"""
        if self._settings is None:
            return False
        
        try:
            with ArtisanDatabase(self.db_path) as db:
                settings_dict = self._settings.to_dict()
                
                # Save each setting individually
                for key, value in settings_dict.items():
                    serialized_value = self._serialize_value(value)
                    db.set_setting(key, serialized_value)
                
                logger.info("Settings saved to database")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        settings = self.load_settings()
        return getattr(settings, key, default)
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a specific setting value"""
        settings = self.load_settings()
        
        if not hasattr(settings, key):
            logger.warning(f"Unknown setting key: {key}")
            return False
        
        # Get old value for change notification
        old_value = getattr(settings, key)
        
        # Set new value
        setattr(settings, key, value)
        
        # Save to database
        success = self.save_settings()
        
        if success:
            # Notify callbacks of change
            self._notify_setting_changed(key, old_value, value)
            logger.info(f"Setting '{key}' changed from {old_value} to {value}")
        
        return success
    
    def register_callback(self, setting_key: str, callback_func):
        """Register a callback for when a setting changes"""
        if setting_key not in self._callbacks:
            self._callbacks[setting_key] = []
        
        self._callbacks[setting_key].append(callback_func)
        logger.debug(f"Registered callback for setting: {setting_key}")
    
    def _notify_setting_changed(self, key: str, old_value: Any, new_value: Any):
        """Notify registered callbacks of setting changes"""
        if key in self._callbacks:
            for callback in self._callbacks[key]:
                try:
                    callback(key, old_value, new_value)
                except Exception as e:
                    logger.error(f"Setting callback failed for {key}: {e}")
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize a value for database storage"""
        if isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return value
        else:
            # Fallback to string representation
            return str(value)
    
    def _deserialize_value(self, key: str, value: str) -> Any:
        """Deserialize a value from database storage"""
        # Get the expected type from the default settings
        default_settings = UserSettings()
        expected_type = type(getattr(default_settings, key, str))
        
        try:
            if expected_type == bool:
                return value.lower() in ("true", "1", "yes", "on")
            elif expected_type == int:
                return int(value)
            elif expected_type == float:
                return float(value)
            elif expected_type == str:
                return value
            else:
                return value
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to deserialize setting {key}={value}: {e}")
            return getattr(default_settings, key)
    
    def reset_to_defaults(self) -> bool:
        """Reset all settings to default values"""
        try:
            self._settings = UserSettings()
            success = self.save_settings()
            
            if success:
                logger.info("Settings reset to defaults")
                # Notify all callbacks of reset
                for key in self._settings.to_dict().keys():
                    self._notify_setting_changed(key, None, getattr(self._settings, key))
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            return False
    
    def export_settings(self) -> Dict[str, Any]:
        """Export settings as dictionary for backup"""
        settings = self.load_settings()
        return settings.to_dict()
    
    def import_settings(self, settings_dict: Dict[str, Any]) -> bool:
        """Import settings from dictionary"""
        try:
            self._settings = UserSettings.from_dict(settings_dict)
            success = self.save_settings()
            
            if success:
                logger.info("Settings imported successfully")
                # Notify callbacks of changes
                for key, value in settings_dict.items():
                    self._notify_setting_changed(key, None, value)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            return False
    
    def get_theme_style(self) -> str:
        """Get CSS style for current theme"""
        theme = self.get_setting('theme', Theme.DARK.value)
        
        if theme == Theme.LIGHT.value:
            return self._get_light_theme_css()
        else:  # Default to dark theme
            return self._get_dark_theme_css()
    
    def _get_dark_theme_css(self) -> str:
        """Get dark theme CSS"""
        return """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #3c3c3c;
        }
        
        QTabBar::tab {
            background-color: #555555;
            color: #ffffff;
            padding: 8px 16px;
            margin: 2px;
            border-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #0078d4;
        }
        
        QTabBar::tab:hover {
            background-color: #666666;
        }
        
        QPushButton {
            background-color: #0078d4;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #106ebe;
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
        }
        
        QPushButton:disabled {
            background-color: #555555;
            color: #888888;
        }
        
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 4px;
            border-radius: 4px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
            border: 2px solid #0078d4;
        }
        
        QTableWidget {
            background-color: #3c3c3c;
            color: #ffffff;
            gridline-color: #555555;
            selection-background-color: #0078d4;
        }
        
        QTableWidget::item {
            padding: 8px;
        }
        
        QHeaderView::section {
            background-color: #555555;
            color: #ffffff;
            padding: 8px;
            border: 1px solid #666666;
            font-weight: bold;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #555555;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        """
    
    def _get_light_theme_css(self) -> str:
        """Get light theme CSS"""
        return """
        QMainWindow {
            background-color: #ffffff;
            color: #000000;
        }
        
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background-color: #f5f5f5;
        }
        
        QTabBar::tab {
            background-color: #e0e0e0;
            color: #000000;
            padding: 8px 16px;
            margin: 2px;
            border-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #0078d4;
            color: #ffffff;
        }
        
        QTabBar::tab:hover {
            background-color: #d0d0d0;
        }
        
        QPushButton {
            background-color: #0078d4;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #106ebe;
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
        }
        
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            padding: 4px;
            border-radius: 4px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
            border: 2px solid #0078d4;
        }
        
        QTableWidget {
            background-color: #ffffff;
            color: #000000;
            gridline-color: #cccccc;
            selection-background-color: #0078d4;
        }
        
        QTableWidget::item {
            padding: 8px;
        }
        
        QHeaderView::section {
            background-color: #e0e0e0;
            color: #000000;
            padding: 8px;
            border: 1px solid #cccccc;
            font-weight: bold;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        """

# Global settings manager instance
_settings_manager: Optional[SettingsManager] = None

def get_settings_manager(db_path: str = "artisan_toolbox.db") -> SettingsManager:
    """Get the global settings manager instance"""
    global _settings_manager
    
    if _settings_manager is None:
        _settings_manager = SettingsManager(db_path)
    
    return _settings_manager

# Convenience functions for common operations
def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting value using the global settings manager"""
    return get_settings_manager().get_setting(key, default)

def set_setting(key: str, value: Any) -> bool:
    """Set a setting value using the global settings manager"""
    return get_settings_manager().set_setting(key, value)

def load_settings() -> UserSettings:
    """Load settings using the global settings manager"""
    return get_settings_manager().load_settings()

def save_settings() -> bool:
    """Save settings using the global settings manager"""
    return get_settings_manager().save_settings()

if __name__ == "__main__":
    # Test the settings manager
    print("Testing Settings Manager...")
    
    manager = SettingsManager("test_settings.db")
    
    # Load default settings
    settings = manager.load_settings()
    print(f"Default theme: {settings.theme}")
    print(f"Default tax rate: {settings.default_tax_rate}")
    
    # Change a setting
    manager.set_setting('theme', Theme.LIGHT.value)
    manager.set_setting('default_tax_rate', 20.0)
    
    # Reload and verify
    new_settings = manager.load_settings()
    print(f"New theme: {new_settings.theme}")
    print(f"New tax rate: {new_settings.default_tax_rate}")
    
    # Test export/import
    exported = manager.export_settings()
    print(f"Exported {len(exported)} settings")
    
    print("Settings manager test completed successfully!")