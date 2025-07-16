"""
SQLite database layer for Ashes of Creation Artisan Toolbox.
Handles items, recipes, inventory, and market data with schema versioning.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class Item:
    """Represents a game item"""
    id: int
    name: str
    type: str
    rarity: str
    level: int
    profession: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None

@dataclass
class Recipe:
    """Represents a crafting recipe"""
    id: int
    output_item_id: int
    profession: str
    level_required: int
    base_crafting_fee: float
    components: List[Dict]  # [{"item_id": int, "quantity": int}]

@dataclass
class InventoryItem:
    """Represents an item in inventory"""
    item_id: int
    node_name: str
    quantity: int
    average_cost: float
    last_updated: datetime

class ArtisanDatabase:
    """
    SQLite database manager for the Artisan Toolbox.
    Handles all data persistence with schema versioning.
    """
    
    CURRENT_VERSION = 2
    
    def __init__(self, db_path: str = "artisan_toolbox.db"):
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        
    def connect(self):
        """Establish database connection with proper configuration"""
        self.connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0
        )
        self.connection.row_factory = sqlite3.Row  # Enable dict-like access
        self.connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
        logger.info(f"Connected to database: {self.db_path}")
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def get_schema_version(self) -> int:
        """Get current database schema version"""
        try:
            cursor = self.connection.execute(
                "SELECT version FROM schema_info ORDER BY version DESC LIMIT 1"
            )
            result = cursor.fetchone()
            return result[0] if result else 0
        except sqlite3.OperationalError:
            # Table doesn't exist, version 0
            return 0
    
    def create_tables(self):
        """Create all database tables with proper schema"""
        cursor = self.connection.cursor()
        
        # Schema version tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_info (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)
        
        # Game items from API
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                rarity TEXT NOT NULL,
                level INTEGER DEFAULT 0,
                profession TEXT,
                description TEXT,
                icon_url TEXT,
                api_data TEXT,  -- Full JSON from API
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(id)
            )
        """)
        
        # Crafting recipes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                output_item_id INTEGER NOT NULL,
                profession TEXT NOT NULL,
                level_required INTEGER DEFAULT 0,
                base_crafting_fee REAL DEFAULT 0.0,
                station_type TEXT,
                crafting_time INTEGER DEFAULT 0,  -- seconds
                api_data TEXT,  -- Full JSON from API
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (output_item_id) REFERENCES items(id),
                UNIQUE(output_item_id, profession)
            )
        """)
        
        # Recipe components (many-to-many)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recipe_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                component_type TEXT NOT NULL DEFAULT 'quality',  -- 'quality' or 'basic'
                is_optional BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES items(id),
                UNIQUE(recipe_id, item_id)
            )
        """)
        
        # Node-based inventory tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                rarity TEXT NOT NULL DEFAULT 'common',
                node_name TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                average_cost REAL DEFAULT 0.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (item_id) REFERENCES items(id),
                UNIQUE(item_id, rarity, node_name)
            )
        """)
        
        # Market price tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                rarity TEXT NOT NULL DEFAULT 'common',
                price REAL NOT NULL,
                source TEXT NOT NULL,  -- 'market', 'guildie', 'harvested'
                node_name TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
        """)
        
        # Transaction history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,  -- 'buy', 'sell', 'craft', 'use'
                item_id INTEGER NOT NULL,
                rarity TEXT NOT NULL DEFAULT 'common',
                quantity INTEGER NOT NULL,
                unit_price REAL DEFAULT 0.0,
                total_cost REAL DEFAULT 0.0,
                node_name TEXT,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
        """)
        
        # User settings and preferences
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_items_name ON items(name)",
            "CREATE INDEX IF NOT EXISTS idx_items_type ON items(type)",
            "CREATE INDEX IF NOT EXISTS idx_items_profession ON items(profession)",
            "CREATE INDEX IF NOT EXISTS idx_items_rarity ON items(rarity)",
            "CREATE INDEX IF NOT EXISTS idx_recipes_profession ON recipes(profession)",
            "CREATE INDEX IF NOT EXISTS idx_inventory_node ON inventory(node_name)",
            "CREATE INDEX IF NOT EXISTS idx_inventory_item_rarity ON inventory(item_id, rarity)",
            "CREATE INDEX IF NOT EXISTS idx_market_prices_item_rarity_date ON market_prices(item_id, rarity, recorded_at)",
            "CREATE INDEX IF NOT EXISTS idx_transactions_item_rarity_date ON transactions(item_id, rarity, transaction_date)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        self.connection.commit()
        logger.info("Database tables created successfully")
    
    def migrate_schema(self):
        """Apply database migrations if needed"""
        current_version = self.get_schema_version()
        
        if current_version < self.CURRENT_VERSION:
            logger.info(f"Migrating database from version {current_version} to {self.CURRENT_VERSION}")
            
            # Apply migrations
            if current_version == 0:
                self.create_tables()
                self.connection.execute(
                    "INSERT INTO schema_info (version, description) VALUES (?, ?)",
                    (1, "Initial schema creation")
                )
            
            # Migration to version 2: Add rarity support
            if current_version < 2:
                self._migrate_to_v2()
            
            self.connection.commit()
            logger.info("Database migration completed")
    
    def _migrate_to_v2(self):
        """Migration to version 2: Add rarity support to inventory, market_prices, and transactions"""
        cursor = self.connection.cursor()
        
        try:
            # Add rarity column to inventory table
            cursor.execute("ALTER TABLE inventory ADD COLUMN rarity TEXT NOT NULL DEFAULT 'common'")
            
            # Add rarity column to market_prices table
            cursor.execute("ALTER TABLE market_prices ADD COLUMN rarity TEXT NOT NULL DEFAULT 'common'")
            
            # Add rarity column to transactions table
            cursor.execute("ALTER TABLE transactions ADD COLUMN rarity TEXT NOT NULL DEFAULT 'common'")
            
            # Add component_type column to recipe_components table
            cursor.execute("ALTER TABLE recipe_components ADD COLUMN component_type TEXT NOT NULL DEFAULT 'quality'")
            
            # Drop old unique constraints and create new ones
            cursor.execute("DROP INDEX IF EXISTS idx_inventory_unique")
            cursor.execute("CREATE UNIQUE INDEX idx_inventory_unique ON inventory(item_id, rarity, node_name)")
            
            # Add new indexes for rarity
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_rarity ON items(rarity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_item_rarity ON inventory(item_id, rarity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_prices_item_rarity_date ON market_prices(item_id, rarity, recorded_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_item_rarity_date ON transactions(item_id, rarity, transaction_date)")
            
            # Update schema version
            cursor.execute(
                "INSERT INTO schema_info (version, description) VALUES (?, ?)",
                (2, "Added rarity support to inventory, market_prices, and transactions tables")
            )
            
            logger.info("Successfully migrated to schema version 2")
            
        except sqlite3.Error as e:
            logger.error(f"Migration to v2 failed: {e}")
            raise
    
    def upsert_item(self, item_data: Dict) -> bool:
        """Insert or update an item from API data"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO items (
                    id, name, type, rarity, level, profession, description, 
                    icon_url, api_data, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                item_data.get('id'),
                item_data.get('name', ''),
                item_data.get('type', ''),
                item_data.get('rarity', ''),
                item_data.get('level', 0),
                item_data.get('profession'),
                item_data.get('description'),
                item_data.get('icon_url'),
                json.dumps(item_data)
            ))
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to upsert item {item_data.get('name', 'unknown')}: {e}")
            return False
    
    def bulk_upsert_items(self, items: List[Dict]) -> int:
        """Bulk insert/update items with transaction"""
        success_count = 0
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("BEGIN TRANSACTION")
            
            for item_data in items:
                if self.upsert_item(item_data):
                    success_count += 1
            
            cursor.execute("COMMIT")
            logger.info(f"Bulk upserted {success_count}/{len(items)} items")
            
        except sqlite3.Error as e:
            cursor.execute("ROLLBACK")
            logger.error(f"Bulk upsert failed: {e}")
        
        return success_count
    
    def get_items_by_profession(self, profession: str) -> List[sqlite3.Row]:
        """Get all items for a specific profession"""
        cursor = self.connection.execute(
            "SELECT * FROM items WHERE profession = ? ORDER BY name",
            (profession,)
        )
        return cursor.fetchall()
    
    def search_items(self, search_term: str, profession: str = None) -> List[sqlite3.Row]:
        """Search items by name with optional profession filter"""
        if profession:
            cursor = self.connection.execute(
                "SELECT * FROM items WHERE name LIKE ? AND profession = ? ORDER BY name",
                (f"%{search_term}%", profession)
            )
        else:
            cursor = self.connection.execute(
                "SELECT * FROM items WHERE name LIKE ? ORDER BY name",
                (f"%{search_term}%",)
            )
        return cursor.fetchall()
    
    def update_inventory(self, item_id: int, node_name: str, 
                        quantity: int, rarity: str = 'common', 
                        average_cost: float = 0.0) -> bool:
        """Update inventory for an item at a specific node with rarity"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO inventory (
                    item_id, rarity, node_name, quantity, average_cost, last_updated
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (item_id, rarity, node_name, quantity, average_cost))
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to update inventory: {e}")
            return False
    
    def get_inventory_summary(self, item_id: int, rarity: str = None) -> List[sqlite3.Row]:
        """Get inventory summary for an item across all nodes, optionally filtered by rarity"""
        if rarity:
            cursor = self.connection.execute("""
                SELECT rarity, node_name, quantity, average_cost, last_updated
                FROM inventory 
                WHERE item_id = ? AND rarity = ? AND quantity > 0
                ORDER BY node_name
            """, (item_id, rarity))
        else:
            cursor = self.connection.execute("""
                SELECT rarity, node_name, quantity, average_cost, last_updated
                FROM inventory 
                WHERE item_id = ? AND quantity > 0
                ORDER BY rarity, node_name
            """, (item_id,))
        return cursor.fetchall()
    
    def record_market_price(self, item_id: int, price: float, 
                          source: str, rarity: str = 'common', 
                          node_name: str = None) -> bool:
        """Record a market price observation with rarity"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO market_prices (item_id, rarity, price, source, node_name)
                VALUES (?, ?, ?, ?, ?)
            """, (item_id, rarity, price, source, node_name))
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to record market price: {e}")
            return False
    
    def get_recent_market_prices(self, item_id: int, rarity: str = None, 
                               days: int = 30) -> List[sqlite3.Row]:
        """Get recent market prices for an item, optionally filtered by rarity"""
        since_date = datetime.now() - timedelta(days=days)
        
        if rarity:
            cursor = self.connection.execute("""
                SELECT price, source, rarity, node_name, recorded_at
                FROM market_prices 
                WHERE item_id = ? AND rarity = ? AND recorded_at >= ?
                ORDER BY recorded_at DESC
            """, (item_id, rarity, since_date.isoformat()))
        else:
            cursor = self.connection.execute("""
                SELECT price, source, rarity, node_name, recorded_at
                FROM market_prices 
                WHERE item_id = ? AND recorded_at >= ?
                ORDER BY recorded_at DESC
            """, (item_id, since_date.isoformat()))
        return cursor.fetchall()
    
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get a user setting"""
        cursor = self.connection.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        result = cursor.fetchone()
        return result[0] if result else default
    
    def set_setting(self, key: str, value: str) -> bool:
        """Set a user setting"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to set setting {key}: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        stats = {}
        tables = ['items', 'recipes', 'inventory', 'market_prices', 'transactions']
        
        for table in tables:
            cursor = self.connection.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        
        return stats


def init_database(db_path: str = "artisan_toolbox.db") -> bool:
    """Initialize database with schema"""
    try:
        with ArtisanDatabase(db_path) as db:
            db.migrate_schema()
            
            # Set initial settings
            db.set_setting('db_initialized', 'true')
            db.set_setting('last_api_sync', '')
            
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


# Example usage
if __name__ == "__main__":
    # Initialize database
    if init_database():
        print("Database initialized successfully")
        
        # Test basic operations
        with ArtisanDatabase() as db:
            # Test item insertion
            test_item = {
                'id': 1,
                'name': 'Test Scroll',
                'type': 'scroll',
                'rarity': 'common',
                'level': 1,
                'profession': 'scribe'
            }
            
            if db.upsert_item(test_item):
                print("Test item inserted")
            
            # Test search
            results = db.search_items('scroll')
            print(f"Found {len(results)} items matching 'scroll'")
            
            # Print stats
            stats = db.get_database_stats()
            print(f"Database stats: {stats}")