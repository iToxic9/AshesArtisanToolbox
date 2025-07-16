"""
Base module class for Artisan Toolbox modules.
Provides common functionality and enforces consistent patterns.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.QtCore import pyqtSignal, QObject

from data_manager import DataManager

logger = logging.getLogger(__name__)

class ModuleError(Exception):
    """Base exception for module-specific errors"""
    pass

class ModuleSignals(QObject):
    """Centralized signal definitions for inter-module communication"""
    
    # Generic signals with flexible data
    data_updated = pyqtSignal(str, dict)  # module_name, data
    error_occurred = pyqtSignal(str, str)  # module_name, error_message
    status_changed = pyqtSignal(str, str)  # module_name, status
    
    # Specific module signals
    craft_completed = pyqtSignal(dict)  # craft_data
    inventory_updated = pyqtSignal(dict)  # inventory_data
    price_updated = pyqtSignal(dict)  # price_data

class BaseModule(QWidget, ABC):
    """
    Base class for all toolbox modules.
    Provides common functionality and enforces consistent patterns.
    """
    
    def __init__(self, data_manager: DataManager, module_name: str):
        super().__init__()
        
        self.data_manager = data_manager
        self.module_name = module_name
        self.signals = ModuleSignals()
        self.is_initialized = False
        
        # Module state
        self.current_data = {}
        self.error_count = 0
        self.max_errors = 10
        
        try:
            self.setup_ui()
            self.connect_signals()
            self.is_initialized = True
            logger.info(f"{self.module_name} module initialized successfully")
        except Exception as e:
            self.handle_error(f"Failed to initialize {self.module_name} module", e)
    
    @abstractmethod
    def setup_ui(self):
        """Setup the module's UI components. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def connect_signals(self):
        """Connect UI signals to handlers. Must be implemented by subclasses."""
        pass
    
    def handle_error(self, message: str, exception: Exception = None, 
                    show_user: bool = True, critical: bool = False):
        """
        Centralized error handling for all modules.
        
        Args:
            message: User-friendly error message
            exception: The exception that occurred (optional)
            show_user: Whether to show message to user
            critical: Whether this is a critical error
        """
        self.error_count += 1
        
        # Log the error
        if exception:
            logger.error(f"{self.module_name}: {message} - {str(exception)}")
        else:
            logger.error(f"{self.module_name}: {message}")
        
        # Emit error signal
        self.signals.error_occurred.emit(self.module_name, message)
        
        # Show to user if requested
        if show_user:
            if critical or self.error_count >= self.max_errors:
                QMessageBox.critical(self, f"{self.module_name} Error", message)
            else:
                QMessageBox.warning(self, f"{self.module_name} Warning", message)
        
        # Reset if too many errors
        if self.error_count >= self.max_errors:
            self.reset_module()
    
    def reset_module(self):
        """Reset module to clean state"""
        try:
            self.current_data.clear()
            self.error_count = 0
            self.refresh_data()
            logger.info(f"{self.module_name} module reset successfully")
        except Exception as e:
            logger.critical(f"Failed to reset {self.module_name} module: {e}")
    
    def emit_data_update(self, data: Dict[str, Any]):
        """Emit data update signal with error handling"""
        try:
            self.current_data.update(data)
            self.signals.data_updated.emit(self.module_name, data)
        except Exception as e:
            self.handle_error("Failed to emit data update", e, show_user=False)
    
    def safe_data_operation(self, operation_name: str, operation_func, *args, **kwargs):
        """
        Safely execute data operations with error handling and logging.
        
        Args:
            operation_name: Name of the operation for logging
            operation_func: Function to execute
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Result of the operation or None if failed
        """
        try:
            logger.debug(f"{self.module_name}: Starting {operation_name}")
            result = operation_func(*args, **kwargs)
            logger.debug(f"{self.module_name}: Completed {operation_name}")
            return result
        except Exception as e:
            self.handle_error(f"Failed to {operation_name}", e)
            return None
    
    def get_safe_value(self, data: Dict, key: str, default=None, value_type=None):
        """
        Safely get value from dictionary with type checking.
        
        Args:
            data: Dictionary to get value from
            key: Key to look for
            default: Default value if key not found
            value_type: Expected type for validation
            
        Returns:
            Value from dictionary or default
        """
        try:
            value = data.get(key, default)
            
            if value_type and value is not None:
                if not isinstance(value, value_type):
                    logger.warning(f"{self.module_name}: Expected {value_type} for {key}, got {type(value)}")
                    return default
            
            return value
        except Exception as e:
            logger.warning(f"{self.module_name}: Error getting value for {key}: {e}")
            return default
    
    def validate_required_fields(self, data: Dict, required_fields: list) -> bool:
        """
        Validate that all required fields are present in data.
        
        Args:
            data: Dictionary to validate
            required_fields: List of required field names
            
        Returns:
            True if all required fields present, False otherwise
        """
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            self.handle_error(f"Missing required fields: {', '.join(missing_fields)}")
            return False
        
        return True
    
    def update_status(self, status: str):
        """Update module status and emit signal"""
        try:
            self.signals.status_changed.emit(self.module_name, status)
            logger.debug(f"{self.module_name}: Status updated to {status}")
        except Exception as e:
            logger.warning(f"{self.module_name}: Failed to update status: {e}")
    
    @abstractmethod
    def refresh_data(self):
        """Refresh module data. Must be implemented by subclasses."""
        pass
    
    def get_module_info(self) -> Dict[str, Any]:
        """Get information about the module's current state"""
        return {
            'module_name': self.module_name,
            'is_initialized': self.is_initialized,
            'error_count': self.error_count,
            'data_keys': list(self.current_data.keys())
        }

class ModuleManager:
    """
    Manager for coordinating between modules.
    Implements the Mediator pattern to reduce coupling.
    """
    
    def __init__(self):
        self.modules = {}
        self.signals = ModuleSignals()
        
    def register_module(self, module: BaseModule):
        """Register a module with the manager"""
        self.modules[module.module_name] = module
        
        # Connect module signals to manager
        module.signals.data_updated.connect(self.handle_data_update)
        module.signals.error_occurred.connect(self.handle_error)
        module.signals.status_changed.connect(self.handle_status_change)
        
        logger.info(f"Registered module: {module.module_name}")
    
    def handle_data_update(self, module_name: str, data: Dict):
        """Handle data updates from modules"""
        logger.debug(f"Data update from {module_name}: {list(data.keys())}")
        
        # Broadcast to other interested modules
        for name, module in self.modules.items():
            if name != module_name:
                try:
                    # Only notify if module has a handle_external_update method
                    if hasattr(module, 'handle_external_update'):
                        module.handle_external_update(module_name, data)
                except Exception as e:
                    logger.warning(f"Failed to notify {name} of update from {module_name}: {e}")
    
    def handle_error(self, module_name: str, error_message: str):
        """Handle errors from modules"""
        logger.warning(f"Error in {module_name}: {error_message}")
        # Could implement additional error handling logic here
    
    def handle_status_change(self, module_name: str, status: str):
        """Handle status changes from modules"""
        logger.debug(f"Status change in {module_name}: {status}")
    
    def broadcast_signal(self, signal_name: str, data: Dict):
        """Broadcast a signal to all modules"""
        for module in self.modules.values():
            try:
                if hasattr(module, f'handle_{signal_name}'):
                    getattr(module, f'handle_{signal_name}')(data)
            except Exception as e:
                logger.warning(f"Failed to broadcast {signal_name} to {module.module_name}: {e}")
    
    def get_manager_status(self) -> Dict:
        """Get status of all managed modules"""
        return {
            'module_count': len(self.modules),
            'modules': {name: module.get_module_info() for name, module in self.modules.items()}
        }