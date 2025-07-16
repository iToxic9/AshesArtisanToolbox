"""
Test script for refactored modules to identify and fix remaining errors.
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication
from data_manager import DataManager
from gui.base_module import ModuleManager
from modules.calculator import CalculatorModule

# Configure logging to capture all errors
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_module_creation():
    """Test creating modules with new architecture"""
    try:
        # Create QApplication for GUI testing
        app = QApplication(sys.argv)
        
        # Create data manager
        data_manager = DataManager()
        
        # Create module manager
        module_manager = ModuleManager()
        
        # Test calculator module creation
        logger.info("Testing Calculator module creation...")
        calculator = CalculatorModule(data_manager)
        module_manager.register_module(calculator)
        
        logger.info("Calculator module created successfully")
        
        # Test module info
        info = calculator.get_module_info()
        logger.info(f"Calculator module info: {info}")
        
        # Test manager status
        manager_status = module_manager.get_manager_status()
        logger.info(f"Module manager status: {manager_status}")
        
        return True
        
    except Exception as e:
        logger.error(f"Module creation test failed: {e}")
        return False

def test_error_handling():
    """Test error handling capabilities"""
    try:
        app = QApplication(sys.argv)
        data_manager = DataManager()
        calculator = CalculatorModule(data_manager)
        
        # Test error handling with invalid operation
        result = calculator.safe_data_operation(
            "test invalid operation",
            lambda: 1/0  # This will cause ZeroDivisionError
        )
        
        logger.info(f"Error handling test result: {result}")
        return result is None  # Should return None on error
        
    except Exception as e:
        logger.error(f"Error handling test failed: {e}")
        return False

def test_rarity_system():
    """Test rarity system integration"""
    try:
        from rarity_system import RarityManager, ItemRarity, apply_rarity_style_to_item
        from PyQt6.QtWidgets import QTableWidgetItem
        
        # Test rarity enum
        common = RarityManager.string_to_rarity("common")
        epic = RarityManager.string_to_rarity("epic")
        
        logger.info(f"Common rarity: {common}")
        logger.info(f"Epic rarity: {epic}")
        
        # Test item styling
        app = QApplication(sys.argv)
        item = QTableWidgetItem("Test Item")
        apply_rarity_style_to_item(item, epic)
        
        logger.info("Rarity styling test passed")
        return True
        
    except Exception as e:
        logger.error(f"Rarity system test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting refactored module tests...")
    
    tests = [
        ("Module Creation", test_module_creation),
        ("Error Handling", test_error_handling),
        ("Rarity System", test_rarity_system),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            if test_func():
                logger.info(f"✅ {test_name} test PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} test FAILED with exception: {e}")
    
    logger.info(f"\n--- Test Results ---")
    logger.info(f"Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.error("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())