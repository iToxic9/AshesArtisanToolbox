"""
Data Management Layer - Synchronizes API, cache, and database.
Handles data flow between Ashescodex API and local storage.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from api_client import AshesCodexAPIClient
from database import ArtisanDatabase
from rarity_system import RarityManager, ItemRarity, ComponentType, get_component_type_from_item

logger = logging.getLogger(__name__)

class DataManager:
    """
    Orchestrates data synchronization between API, cache, and database.
    Provides high-level interface for data operations.
    """
    
    def __init__(self, db_path: str = "artisan_toolbox.db", 
                 cache_dir: str = "cache"):
        self.db_path = db_path
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Sync settings
        self.auto_sync_interval_hours = 24
        self.max_api_pages = 200
        
    async def initialize(self) -> bool:
        """Initialize data manager and ensure database is ready"""
        try:
            with ArtisanDatabase(self.db_path) as db:
                db.migrate_schema()
                
                # Check if we need initial data sync
                last_sync = db.get_setting('last_api_sync')
                if not last_sync:
                    logger.info("No previous sync found, will perform initial data sync")
                    return True
                
                # Check if sync is needed based on time
                try:
                    last_sync_time = datetime.fromisoformat(last_sync)
                    if datetime.now() - last_sync_time > timedelta(hours=self.auto_sync_interval_hours):
                        logger.info("Auto-sync interval exceeded, sync recommended")
                except ValueError:
                    logger.warning("Invalid last sync timestamp, sync recommended")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize data manager: {e}")
            return False
    
    async def sync_from_api(self, force: bool = False) -> Tuple[bool, Dict]:
        """
        Synchronize data from API to database.
        Returns (success, stats) tuple.
        """
        stats = {
            'items_fetched': 0,
            'items_updated': 0,
            'errors': 0,
            'sync_duration': 0,
            'cache_hits': 0,
            'api_requests': 0
        }
        
        start_time = datetime.now()
        
        try:
            with ArtisanDatabase(self.db_path) as db:
                # Check if sync is needed
                if not force:
                    last_sync = db.get_setting('last_api_sync')
                    if last_sync:
                        last_sync_time = datetime.fromisoformat(last_sync)
                        if datetime.now() - last_sync_time < timedelta(hours=self.auto_sync_interval_hours):
                            logger.info("Sync not needed yet, use force=True to override")
                            return True, stats
                
                logger.info("Starting API synchronization...")
                
                async with AshesCodexAPIClient(cache_dir=str(self.cache_dir)) as api_client:
                    # Fetch all items from API
                    all_items = await api_client.get_all_items(
                        use_cache=not force,
                        max_pages=self.max_api_pages
                    )
                    
                    # Get API client stats
                    api_stats = api_client.get_stats()
                    stats['cache_hits'] = api_stats['cache_hits']
                    stats['api_requests'] = api_stats['total_requests']
                    stats['items_fetched'] = len(all_items)
                    
                    if all_items:
                        # Bulk insert items into database
                        items_updated = db.bulk_upsert_items(all_items)
                        stats['items_updated'] = items_updated
                        
                        # Update sync timestamp
                        db.set_setting('last_api_sync', datetime.now().isoformat())
                        
                        logger.info(f"Sync completed: {items_updated} items updated")
                    else:
                        logger.warning("No items fetched from API")
                        stats['errors'] = 1
                
        except Exception as e:
            logger.error(f"API sync failed: {e}")
            stats['errors'] = 1
            return False, stats
        
        finally:
            stats['sync_duration'] = (datetime.now() - start_time).total_seconds()
        
        return stats['errors'] == 0, stats
    
    def get_items_for_profession(self, profession: str) -> List[Dict]:
        """Get all items for a specific profession"""
        try:
            with ArtisanDatabase(self.db_path) as db:
                rows = db.get_items_by_profession(profession)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get items for profession {profession}: {e}")
            return []
    
    def search_items(self, search_term: str, profession: str = None) -> List[Dict]:
        """Search items with optional profession filter"""
        try:
            with ArtisanDatabase(self.db_path) as db:
                rows = db.search_items(search_term, profession)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to search items: {e}")
            return []
    
    def update_inventory(self, item_id: int, node_name: str, 
                        quantity: int, rarity: str = 'common', 
                        average_cost: float = 0.0) -> bool:
        """Update inventory for an item at a node with rarity"""
        try:
            with ArtisanDatabase(self.db_path) as db:
                return db.update_inventory(item_id, node_name, quantity, rarity, average_cost)
        except Exception as e:
            logger.error(f"Failed to update inventory: {e}")
            return False
    
    def get_inventory_summary(self, item_id: int, rarity: str = None) -> List[Dict]:
        """Get inventory summary across all nodes, optionally filtered by rarity"""
        try:
            with ArtisanDatabase(self.db_path) as db:
                rows = db.get_inventory_summary(item_id, rarity)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get inventory summary: {e}")
            return []
    
    def record_market_price(self, item_id: int, price: float, 
                          source: str, rarity: str = 'common', 
                          node_name: str = None) -> bool:
        """Record a market price observation with rarity"""
        try:
            with ArtisanDatabase(self.db_path) as db:
                return db.record_market_price(item_id, price, source, rarity, node_name)
        except Exception as e:
            logger.error(f"Failed to record market price: {e}")
            return False
    
    def get_market_analysis(self, item_id: int, rarity: str = None, days: int = 30) -> Dict:
        """Get market price analysis for an item, optionally filtered by rarity"""
        try:
            with ArtisanDatabase(self.db_path) as db:
                prices = db.get_recent_market_prices(item_id, rarity, days)
                
                if not prices:
                    return {
                        'average_price': 0.0,
                        'min_price': 0.0,
                        'max_price': 0.0,
                        'price_trend': 'no_data',
                        'data_points': 0,
                        'rarity': rarity
                    }
                
                price_values = [float(row['price']) for row in prices]
                
                # Calculate basic statistics
                analysis = {
                    'average_price': sum(price_values) / len(price_values),
                    'min_price': min(price_values),
                    'max_price': max(price_values),
                    'data_points': len(price_values),
                    'rarity': rarity
                }
                
                # Simple trend analysis (compare recent vs older prices)
                if len(price_values) >= 6:
                    recent_avg = sum(price_values[:3]) / 3  # Most recent 3
                    older_avg = sum(price_values[-3:]) / 3  # Oldest 3
                    
                    if recent_avg > older_avg * 1.1:
                        analysis['price_trend'] = 'rising'
                    elif recent_avg < older_avg * 0.9:
                        analysis['price_trend'] = 'falling'
                    else:
                        analysis['price_trend'] = 'stable'
                else:
                    analysis['price_trend'] = 'insufficient_data'
                
                return analysis
                
        except Exception as e:
            logger.error(f"Failed to get market analysis: {e}")
            return {}
    
    def calculate_crafting_cost(self, item_id: int, target_rarity: str = 'common', 
                              quantity: int = 1, tax_rate: float = 0.0, 
                              custom_prices: Dict[str, float] = None, 
                              quality_rating: int = 0) -> Dict:
        """
        Calculate total crafting cost for an item with rarity considerations.
        Returns detailed cost breakdown including rarity-specific components.
        
        Args:
            item_id: The item to craft
            target_rarity: Desired rarity of the crafted item
            quantity: Number of items to craft
            tax_rate: Node tax rate (0.0 to 1.0)
            custom_prices: Custom prices in format {item_id_rarity: price}
            quality_rating: Crafting quality rating (for future implementation)
        """
        try:
            with ArtisanDatabase(self.db_path) as db:
                # Get recipe for the item
                cursor = db.connection.execute("""
                    SELECT r.*, rc.item_id, rc.quantity as component_qty, 
                           rc.component_type, i.name as component_name, i.rarity as base_rarity
                    FROM recipes r
                    JOIN recipe_components rc ON r.id = rc.recipe_id
                    JOIN items i ON rc.item_id = i.id
                    WHERE r.output_item_id = ?
                """, (item_id,))
                
                recipe_data = cursor.fetchall()
                
                if not recipe_data:
                    return {'error': 'Recipe not found'}
                
                # Extract recipe info and components
                recipe_info = recipe_data[0]
                base_fee = float(recipe_info['base_crafting_fee'])
                
                components = []
                total_material_cost = 0.0
                target_rarity_enum = RarityManager.string_to_rarity(target_rarity)
                
                for row in recipe_data:
                    component_id = row['item_id']
                    component_qty = row['component_qty']
                    component_name = row['component_name']
                    component_type = row.get('component_type', 'quality')
                    base_rarity = row.get('base_rarity', 'common')
                    
                    # Determine required rarity for this component
                    if component_type == 'basic':
                        # Basic components always use base rarity
                        required_rarity = base_rarity
                    else:
                        # Quality components need to match target rarity
                        required_rarity = target_rarity
                    
                    # Create component key for price lookup
                    component_key = RarityManager.create_item_key(component_id, 
                                                                RarityManager.string_to_rarity(required_rarity))
                    
                    # Get price (custom price, recent market price, or 0)
                    if custom_prices and component_key in custom_prices:
                        unit_price = custom_prices[component_key]
                        price_source = 'custom'
                    else:
                        # Get most recent market price for this rarity
                        recent_prices = db.get_recent_market_prices(component_id, required_rarity, 7)
                        if recent_prices:
                            unit_price = float(recent_prices[0]['price'])
                            price_source = f"market_{recent_prices[0]['source']}"
                        else:
                            unit_price = 0.0
                            price_source = 'no_data'
                    
                    component_cost = unit_price * component_qty * quantity
                    total_material_cost += component_cost
                    
                    components.append({
                        'item_id': component_id,
                        'name': component_name,
                        'rarity': required_rarity,
                        'component_type': component_type,
                        'quantity_needed': component_qty * quantity,
                        'unit_price': unit_price,
                        'total_cost': component_cost,
                        'price_source': price_source,
                        'component_key': component_key
                    })
                
                # Calculate tax on base fee
                base_fee_total = base_fee * quantity
                tax_amount = base_fee_total * tax_rate
                total_cost = total_material_cost + base_fee_total + tax_amount
                
                return {
                    'item_id': item_id,
                    'target_rarity': target_rarity,
                    'quantity': quantity,
                    'components': components,
                    'material_cost': total_material_cost,
                    'base_crafting_fee': base_fee_total,
                    'tax_amount': tax_amount,
                    'total_cost': total_cost,
                    'cost_per_unit': total_cost / quantity if quantity > 0 else 0.0,
                    'tax_rate': tax_rate,
                    'quality_rating': quality_rating
                }
                
        except Exception as e:
            logger.error(f"Failed to calculate crafting cost: {e}")
            return {'error': str(e)}
    
    def get_data_status(self) -> Dict:
        """Get status of data synchronization and database"""
        try:
            with ArtisanDatabase(self.db_path) as db:
                stats = db.get_database_stats()
                last_sync = db.get_setting('last_api_sync')
                
                status = {
                    'database_stats': stats,
                    'last_sync': last_sync,
                    'sync_age_hours': 0
                }
                
                if last_sync:
                    try:
                        last_sync_time = datetime.fromisoformat(last_sync)
                        age = datetime.now() - last_sync_time
                        status['sync_age_hours'] = age.total_seconds() / 3600
                    except ValueError:
                        status['sync_age_hours'] = -1
                
                return status
                
        except Exception as e:
            logger.error(f"Failed to get data status: {e}")
            return {'error': str(e)}
    
    async def check_api_connectivity(self) -> Tuple[bool, str]:
        """Test API connectivity and responsiveness"""
        try:
            async with AshesCodexAPIClient(cache_dir=str(self.cache_dir)) as client:
                response = await client.get_items_page(1, use_cache=False)
                
                if response.success:
                    return True, "API is accessible"
                else:
                    return False, f"API error: {response.error}"
                    
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def get_available_rarities_for_item(self, item_id: int) -> List[str]:
        """Get all available rarities for an item in inventory"""
        try:
            with ArtisanDatabase(self.db_path) as db:
                cursor = db.connection.execute("""
                    SELECT DISTINCT rarity FROM inventory 
                    WHERE item_id = ? AND quantity > 0
                    ORDER BY rarity
                """, (item_id,))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get available rarities: {e}")
            return []
    
    def get_inventory_by_rarity(self, rarity: str) -> List[Dict]:
        """Get all inventory items of a specific rarity"""
        try:
            with ArtisanDatabase(self.db_path) as db:
                cursor = db.connection.execute("""
                    SELECT i.id, i.name, i.type, i.profession, inv.rarity, 
                           inv.node_name, inv.quantity, inv.average_cost, inv.last_updated
                    FROM inventory inv
                    JOIN items i ON inv.item_id = i.id
                    WHERE inv.rarity = ? AND inv.quantity > 0
                    ORDER BY i.name, inv.node_name
                """, (rarity,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get inventory by rarity: {e}")
            return []
    
    def check_crafting_availability(self, item_id: int, target_rarity: str, 
                                  quantity: int = 1, node_name: str = None) -> Dict:
        """
        Check if materials are available for crafting with rarity considerations.
        Returns availability status and missing materials.
        """
        try:
            # Get crafting cost breakdown
            cost_breakdown = self.calculate_crafting_cost(item_id, target_rarity, quantity)
            
            if 'error' in cost_breakdown:
                return {'error': cost_breakdown['error']}
            
            available_components = []
            missing_components = []
            
            for component in cost_breakdown['components']:
                component_id = component['item_id']
                required_rarity = component['rarity']
                needed_quantity = component['quantity_needed']
                
                # Check inventory availability
                inventory_summary = self.get_inventory_summary(component_id, required_rarity)
                
                if node_name:
                    # Check specific node
                    node_inventory = [inv for inv in inventory_summary if inv['node_name'] == node_name]
                    available_quantity = node_inventory[0]['quantity'] if node_inventory else 0
                else:
                    # Check all nodes
                    available_quantity = sum(inv['quantity'] for inv in inventory_summary)
                
                component_info = {
                    'item_id': component_id,
                    'name': component['name'],
                    'rarity': required_rarity,
                    'needed_quantity': needed_quantity,
                    'available_quantity': available_quantity,
                    'is_sufficient': available_quantity >= needed_quantity
                }
                
                if component_info['is_sufficient']:
                    available_components.append(component_info)
                else:
                    missing_components.append(component_info)
            
            return {
                'can_craft': len(missing_components) == 0,
                'available_components': available_components,
                'missing_components': missing_components,
                'total_components': len(cost_breakdown['components'])
            }
            
        except Exception as e:
            logger.error(f"Failed to check crafting availability: {e}")
            return {'error': str(e)}


# Convenience functions for common operations
async def quick_sync(force: bool = False) -> bool:
    """Quick sync operation for CLI usage"""
    manager = DataManager()
    if await manager.initialize():
        success, stats = await manager.sync_from_api(force)
        if success:
            print(f"Sync completed: {stats['items_updated']} items updated")
            print(f"Duration: {stats['sync_duration']:.1f}s")
            print(f"API requests: {stats['api_requests']}, Cache hits: {stats['cache_hits']}")
            return True
        else:
            print(f"Sync failed with {stats['errors']} errors")
            return False
    return False

def get_status() -> Dict:
    """Get current data status for CLI usage"""
    manager = DataManager()
    return manager.get_data_status()


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def main():
        manager = DataManager()
        
        # Initialize
        if await manager.initialize():
            print("Data manager initialized")
            
            # Check API connectivity
            connected, message = await manager.check_api_connectivity()
            print(f"API Status: {message}")
            
            if connected:
                # Perform sync
                success, stats = await manager.sync_from_api()
                print(f"Sync result: {success}")
                print(f"Stats: {stats}")
            
            # Get status
            status = manager.get_data_status()
            print(f"Data status: {status}")
    
    asyncio.run(main())