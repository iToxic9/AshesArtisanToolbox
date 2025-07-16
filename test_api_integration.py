"""
Test script for API integration and data management.
Run this to verify the framework is working correctly.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_api_client():
    """Test the API client functionality"""
    print("\n=== Testing API Client ===")
    
    try:
        from api_client import AshesCodexAPIClient
        
        async with AshesCodexAPIClient() as client:
            print("[OK] API client initialized")
            
            # Test single page
            response = await client.get_items_page(1)
            if response.success:
                items = response.data.get('data', [])
                print(f"[OK] Fetched page 1: {len(items)} items")
                
                if items:
                    sample_item = items[0]
                    print(f"  Sample item: {sample_item.get('name', 'Unknown')}")
            else:
                print(f"[FAIL] Failed to fetch page 1: {response.error}")
                return False
            
            # Test limited pagination
            print("Testing pagination (first 3 pages)...")
            all_items = await client.get_all_items(max_pages=3)
            print(f"[OK] Fetched {len(all_items)} total items")
            
            # Print stats
            stats = client.get_stats()
            print(f"[OK] API Stats: {stats}")
            
        return True
        
    except ImportError as e:
        print(f"[FAIL] Failed to import api_client: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] API client test failed: {e}")
        return False

async def test_database():
    """Test database functionality"""
    print("\n=== Testing Database ===")
    
    try:
        from database import ArtisanDatabase, init_database
        
        # Initialize database
        test_db_path = "test_artisan_toolbox.db"
        if init_database(test_db_path):
            print("[OK] Database initialized")
        else:
            print("[FAIL] Database initialization failed")
            return False
        
        with ArtisanDatabase(test_db_path) as db:
            print("[OK] Database connection established")
            
            # Test item insertion
            test_item = {
                'id': 999,
                'name': 'Test Scroll of Testing',
                'type': 'scroll',
                'rarity': 'common',
                'level': 1,
                'profession': 'scribe',
                'description': 'A scroll for testing purposes'
            }
            
            if db.upsert_item(test_item):
                print("[OK] Test item inserted")
            else:
                print("[FAIL] Failed to insert test item")
                return False
            
            # Test search
            results = db.search_items('Test Scroll')
            if results:
                print(f"[OK] Search found {len(results)} items")
            else:
                print("[FAIL] Search failed")
                return False
            
            # Test inventory update
            if db.update_inventory(999, "Lionhold", 5, 10.0):
                print("[OK] Inventory updated")
            else:
                print("[FAIL] Failed to update inventory")
                return False
            
            # Test market price recording
            if db.record_market_price(999, 15.0, "market", "Lionhold"):
                print("[OK] Market price recorded")
            else:
                print("[FAIL] Failed to record market price")
                return False
            
            # Get stats
            stats = db.get_database_stats()
            print(f"[OK] Database stats: {stats}")
        
        # Clean up test database
        Path(test_db_path).unlink(missing_ok=True)
        print("[OK] Test database cleaned up")
        
        return True
        
    except ImportError as e:
        print(f"[FAIL] Failed to import database: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Database test failed: {e}")
        return False

async def test_data_manager():
    """Test data manager integration"""
    print("\n=== Testing Data Manager ===")
    
    try:
        from data_manager import DataManager
        
        manager = DataManager("test_integration.db")
        
        # Initialize
        if await manager.initialize():
            print("[OK] Data manager initialized")
        else:
            print("[FAIL] Data manager initialization failed")
            return False
        
        # Test API connectivity
        connected, message = await manager.check_api_connectivity()
        print(f"[OK] API connectivity: {message}")
        
        if connected:
            # Test limited sync
            print("Testing limited data sync...")
            success, stats = await manager.sync_from_api(force=True)
            if success:
                print(f"[OK] Sync completed: {stats}")
            else:
                print(f"[FAIL] Sync failed: {stats}")
        else:
            print("[WARNING] Skipping sync test due to API connectivity issues")
        
        # Test data operations
        items = manager.search_items("scroll", "scribe")
        print(f"[OK] Found {len(items)} scribe scrolls")
        
        # Get status
        status = manager.get_data_status()
        print(f"[OK] Data status: {status}")
        
        # Clean up
        Path("test_integration.db").unlink(missing_ok=True)
        print("[OK] Test database cleaned up")
        
        return True
        
    except ImportError as e:
        print(f"[FAIL] Failed to import data_manager: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Data manager test failed: {e}")
        return False

async def run_all_tests():
    """Run comprehensive test suite"""
    print("Ashes of Creation Artisan Toolbox - Integration Test")
    print("=" * 50)
    
    tests = [
        ("API Client", test_api_client),
        ("Database", test_database),
        ("Data Manager", test_data_manager)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[FAIL] {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("[SUCCESS] All tests passed! Framework is ready.")
        return True
    else:
        print("[NO_DATA] Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest suite crashed: {e}")
        sys.exit(1)