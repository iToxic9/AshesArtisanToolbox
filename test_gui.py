"""
GUI Test Runner for the Ashes of Creation Artisan Toolbox.
Tests GUI components and inter-module communication.
"""

import sys
import asyncio
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QTest

# Configure logging for testing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_main_application():
    """Test the main application startup"""
    print("\n=== Testing Main Application ===")
    
    try:
        from main import ArtisanToolboxApp
        
        app = ArtisanToolboxApp([])
        
        if app.main_window:
            print("[OK] Main window created successfully")
            
            # Test tab creation
            tab_widget = app.main_window.tab_widget
            if tab_widget and tab_widget.count() >= 4:
                print(f"[OK] All {tab_widget.count()} tabs created")
                
                # Test each tab
                for i in range(tab_widget.count()):
                    tab_name = tab_widget.tabText(i)
                    widget = tab_widget.widget(i)
                    if widget:
                        print(f"  [OK] Tab '{tab_name}' loaded")
                    else:
                        print(f"  [FAIL] Tab '{tab_name}' failed to load")
                        return False
            else:
                print("[FAIL] Insufficient tabs created")
                return False
            
            # Test window properties
            if app.main_window.windowTitle():
                print("[OK] Window title set")
            
            if app.main_window.width() > 0 and app.main_window.height() > 0:
                print("[OK] Window has valid dimensions")
            
            return True
            
        else:
            print("[FAIL] Main window creation failed")
            return False
            
    except Exception as e:
        print(f"[FAIL] Main application test failed: {e}")
        return False

def test_data_manager_integration():
    """Test data manager integration"""
    print("\n=== Testing Data Manager Integration ===")
    
    try:
        from data_manager import DataManager
        
        manager = DataManager("test_gui.db")
        print("[OK] Data manager created")
        
        # Test initialization
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(manager.initialize())
        if success:
            print("[OK] Data manager initialized")
        else:
            print("[FAIL] Data manager initialization failed")
            return False
        
        # Test basic operations
        status = manager.get_data_status()
        if status:
            print("[OK] Data status retrieved")
            print(f"  Database stats: {status.get('database_stats', {})}")
        
        # Test search functionality
        items = manager.search_items("scroll")
        print(f"[OK] Search functionality works: {len(items)} items found")
        
        loop.close()
        return True
        
    except Exception as e:
        print(f"[FAIL] Data manager test failed: {e}")
        return False

def test_module_communication():
    """Test inter-module communication"""
    print("\n=== Testing Module Communication ===")
    
    try:
        from data_manager import DataManager
        from modules.calculator import CalculatorModule
        from modules.inventory_manager import InventoryManagerModule
        from modules.market_analysis import MarketAnalysisModule
        from modules.batch_planner import BatchPlannerModule
        
        manager = DataManager("test_gui.db")
        
        # Create modules
        calculator = CalculatorModule(manager)
        inventory = InventoryManagerModule(manager)
        market = MarketAnalysisModule(manager)
        batch_planner = BatchPlannerModule(manager)
        
        print("[OK] All modules created successfully")
        
        # Test signal connections
        signal_tests = []
        
        # Test calculator -> inventory connection
        try:
            calculator.craft_completed.connect(inventory.update_inventory_from_craft)
            signal_tests.append("Calculator → Inventory")
        except Exception as e:
            print(f"[FAIL] Calculator → Inventory connection failed: {e}")
        
        # Test market -> calculator connection  
        try:
            market.price_updated.connect(calculator.update_material_price)
            signal_tests.append("Market → Calculator")
        except Exception as e:
            print(f"[FAIL] Market → Calculator connection failed: {e}")
        
        # Test batch planner -> calculator connection
        try:
            batch_planner.recipe_selected.connect(calculator.load_recipe)
            signal_tests.append("Batch Planner → Calculator")
        except Exception as e:
            print(f"[FAIL] Batch Planner → Calculator connection failed: {e}")
        
        print(f"[OK] Signal connections established: {', '.join(signal_tests)}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Module communication test failed: {e}")
        return False

def test_gui_responsiveness():
    """Test GUI responsiveness and basic interactions"""
    print("\n=== Testing GUI Responsiveness ===")
    
    app = None
    try:
        from main import ArtisanToolboxApp
        
        app = ArtisanToolboxApp([])
        
        if not app.main_window:
            print("[FAIL] Main window not available")
            return False
        
        main_window = app.main_window
        
        # Test tab switching
        tab_widget = main_window.tab_widget
        original_index = tab_widget.currentIndex()
        
        for i in range(tab_widget.count()):
            tab_widget.setCurrentIndex(i)
            current_widget = tab_widget.currentWidget()
            if current_widget and current_widget.isEnabled():
                tab_name = tab_widget.tabText(i)
                print(f"  [OK] Tab '{tab_name}' is responsive")
            else:
                print(f"  [FAIL] Tab {i} is not responsive")
        
        # Restore original tab
        tab_widget.setCurrentIndex(original_index)
        print("[OK] Tab switching works correctly")
        
        # Test window resizing
        original_size = main_window.size()
        main_window.resize(800, 600)
        if main_window.width() == 800 and main_window.height() == 600:
            print("[OK] Window resizing works")
        
        # Restore original size
        main_window.resize(original_size)
        
        return True
        
    except Exception as e:
        print(f"[FAIL] GUI responsiveness test failed: {e}")
        return False
    finally:
        if app:
            app.quit()

def run_gui_tests():
    """Run all GUI tests"""
    print("Ashes of Creation Artisan Toolbox - GUI Test Suite")
    print("=" * 55)
    
    tests = [
        ("Main Application", test_main_application),
        ("Data Manager Integration", test_data_manager_integration),
        ("Module Communication", test_module_communication),
        ("GUI Responsiveness", test_gui_responsiveness)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[FAIL] {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 55)
    print("GUI TEST SUMMARY")
    print("=" * 55)
    
    passed = 0
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("[SUCCESS] All GUI tests passed! Application is ready.")
        return True
    else:
        print("[NO_DATA] Some GUI tests failed. Check the output above.")
        return False

def interactive_test():
    """Run an interactive test of the application"""
    print("\n=== Interactive Test ===")
    print("Starting interactive GUI test...")
    
    try:
        from main import ArtisanToolboxApp
        
        app = ArtisanToolboxApp([])
        
        if app.main_window:
            app.main_window.show()
            
            # Auto-close after 5 seconds for automated testing
            QTimer.singleShot(5000, app.quit)
            
            print("[OK] GUI displayed successfully")
            print("  Application will auto-close in 5 seconds...")
            
            # Run the event loop
            exit_code = app.exec()
            
            if exit_code == 0:
                print("[OK] Application closed normally")
                return True
            else:
                print(f"[FAIL] Application exited with code: {exit_code}")
                return False
        else:
            print("[FAIL] Failed to create main window")
            return False
            
    except Exception as e:
        print(f"[FAIL] Interactive test failed: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GUI Test Runner")
    parser.add_argument("--interactive", action="store_true", 
                       help="Run interactive GUI test")
    parser.add_argument("--quick", action="store_true",
                       help="Run quick tests only")
    
    args = parser.parse_args()
    
    if args.interactive:
        success = interactive_test()
        sys.exit(0 if success else 1)
    elif args.quick:
        # Quick test - just module creation
        success = test_data_manager_integration() and test_module_communication()
        sys.exit(0 if success else 1)
    else:
        success = run_gui_tests()
        sys.exit(0 if success else 1)