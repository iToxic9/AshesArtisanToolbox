# Contributing to Ashes of Creation Artisan Toolbox

This document provides comprehensive guidance for contributors to understand the codebase structure, workflow patterns, and how to effectively contribute to the project.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture & Data Flow](#architecture--data-flow)
3. [Core Components](#core-components)
4. [Module System](#module-system)
5. [Development Workflow](#development-workflow)
6. [Game Context](#game-context)
7. [Adding New Features](#adding-new-features)
8. [Testing Guidelines](#testing-guidelines)
9. [Code Style](#code-style)

## Project Overview

The **Ashes of Creation Artisan Toolbox** is a PyQt6 desktop application designed for the Ashes of Creation MMORPG Alpha phase. It focuses on crafting calculations and inventory management across multiple nodes, specifically targeting artisan professions like Scribe and Alchemy.

### Core Objective
Desktop application for crafting calculation + inventory management across nodes with tax-aware pricing.

### Key Design Principles
- **API-Driven**: Primary data source is ashescodex.com API
- **Node-Centric**: Inventory tracking across multiple game nodes
- **Tax-Aware**: Incorporates node tax rates into crafting calculations
- **Profession-Focused**: Optimized for Journeyman Scribe/Alchemy professions
- **Offline-Capable**: Local caching for offline functionality

## Architecture & Data Flow

### High-Level Data Flow
```
External API → Local Cache → Database → GUI Modules → User Display
                     ↓
               Background Sync ← User Actions → Real-time Updates
```

### Detailed Component Flow
```
ashescodex.com API
        ↓
AshesCodexAPIClient (api_client.py)
        ↓
Local JSON Cache (cache/)
        ↓
DataManager (data_manager.py)
        ↓
ArtisanDatabase (database.py)
        ↓
GUI Modules (modules/)
        ↓
MainWindow (gui/main_window.py)
        ↓
User Interface
```

### Inter-Module Communication
Modules communicate via PyQt signals for loose coupling:
```python
# Example signal flows
calculator.craft_completed.connect(inventory.update_inventory_from_craft)
market.price_updated.connect(calculator.update_material_price)
inventory.low_stock_alert.connect(main_window.show_notification)
```

## Core Components

### 1. Application Entry Point (`main.py`)

**Purpose**: Application lifecycle management and initialization

**Key Classes**:
- `ArtisanToolboxApp`: Main QApplication subclass
  - Manages app metadata and styling
  - Coordinates data manager initialization
  - Handles application-level events

**Function Flow**:
1. Initialize logging system
2. Create QApplication instance
3. Initialize DataManager
4. Create MainWindow with modules
5. Apply theming and start event loop

### 2. Data Management Layer (`data_manager.py`)

**Purpose**: Orchestrates data synchronization between API, cache, and database

**Key Methods**:
- `initialize()`: Sets up database and checks sync requirements
- `sync_from_api()`: Fetches data from ashescodex.com with rate limiting
- `calculate_crafting_cost()`: Core tax-aware calculation logic
- `get_market_analysis()`: Price trend analysis

**Workflow**:
1. Check database schema version
2. Perform migrations if needed
3. Determine if API sync is required (24-hour interval)
4. Execute batch API requests with exponential backoff
5. Update local database with fetched data
6. Provide high-level data access methods

### 3. API Client (`api_client.py`)

**Purpose**: Robust API client with rate limiting and caching

**Key Features**:
- **Rate Limiting**: 1.5-second delay between requests
- **Caching**: 24-hour JSON cache with automatic expiration
- **Error Handling**: Exponential backoff with retry logic
- **Batch Processing**: Processes ~190 pages in smaller batches
- **Timeout Management**: Reduced timeouts to handle slow responses

**Request Flow**:
1. Check local cache first (if enabled)
2. Apply rate limiting delay
3. Make HTTP request with retry logic
4. Handle various HTTP status codes appropriately
5. Cache successful responses
6. Return structured APIResponse objects

### 4. Database Layer (`database.py`)

**Purpose**: SQLite database operations with schema versioning

**Key Tables**:
- `items`: Game items from API (id, name, type, rarity, profession)
- `recipes`: Crafting recipes with components
- `recipe_components`: Many-to-many recipe ingredients
- `inventory`: Node-based item storage tracking
- `market_prices`: Price history with source attribution
- `transactions`: Crafting and trading history
- `settings`: User preferences and app state

**Database Operations**:
- `bulk_upsert_items()`: Efficient batch item updates
- `search_items()`: Fuzzy search with profession filters
- `calculate_crafting_cost()`: Complex recipe cost calculation
- `get_market_analysis()`: Price trend analysis with statistics

### 5. GUI Framework (`gui/main_window.py`)

**Purpose**: Main window container with tab-based module system

**Key Components**:
- `DataInitializationThread`: Background API sync thread
- `MainWindow`: Primary container with menu/status bar
- Tab system for different modules
- Progress indicators for long-running operations
- Status bar with real-time updates

**UI Flow**:
1. Create main window structure
2. Initialize all module tabs
3. Start background data initialization
4. Handle module switching and communication
5. Provide user feedback for all operations

## Module System

Each module is a self-contained QWidget that handles a specific aspect of the toolbox:

### Calculator Module (`modules/calculator.py`)

**Purpose**: Tax-aware crafting cost calculations

**Core Features**:
- Recipe search by profession
- Dynamic tax rate slider (0-100%)
- Custom material price overrides
- Real-time cost updates
- Material availability checking

**Data Flow**: `API Cache → Recipe Database → Calculator Interface → Results Display`

**Key Methods**:
- `search_recipes()`: Find recipes by name/profession
- `calculate_costs()`: Apply tax formula and material costs
- `update_material_price()`: Handle custom price inputs
- `export_to_batch_planner()`: Send recipes to batch module

### Inventory Manager (`modules/inventory_manager.py`)

**Purpose**: Track materials across multiple node storage locations

**Core Features**:
- Multi-node inventory tracking
- Manual inventory entry
- Low-stock alerts
- Transaction history
- Future: Screenshot OCR integration

**Data Flow**: `User Input/Screenshots → Inventory Database → Overview Display`

**Key Methods**:
- `update_inventory()`: Add/modify inventory quantities
- `get_node_summary()`: Aggregate inventory by location
- `check_availability()`: Verify materials for crafting
- `handle_craft_deduction()`: Auto-deduct materials on craft

### Market Analysis (`modules/market_analysis.py`)

**Purpose**: Price tracking and market trend analysis

**Core Features**:
- Manual price recording by source (market/guildie/harvested)
- Price trend analysis (rising/falling/stable)
- Market recommendations
- Integration with calculator for dynamic pricing

**Data Flow**: `Price Records → Market Database → Trend Analysis → Calculator Updates`

### Batch Planner (`modules/batch_planner.py`) - In Development

**Purpose**: Multi-recipe optimization for efficient crafting orders

**Planned Features**:
- Multiple recipe batch planning
- Inventory availability checking
- Cost optimization algorithms
- Material requirement aggregation

## Development Workflow

### Setting Up Development Environment

1. **Clone the repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Test API integration**:
   ```bash
   python test_api_integration.py
   ```
4. **Run the application**:
   ```bash
   python main.py
   ```

### Code Organization Patterns

```python
# File organization follows this pattern:
main.py                 # Application entry point
gui/main_window.py      # Main GUI container
modules/calculator.py   # Feature-specific modules
data_manager.py         # Unified data access layer
api_client.py          # External API integration
database.py            # Data persistence layer
```

### Adding New Modules

1. **Create module file** in `modules/` directory
2. **Inherit from QWidget** for GUI components
3. **Use pyqtSignal** for inter-module communication
4. **Register in MainWindow**:
   ```python
   # In main_window.py
   new_module = NewModule(self.data_manager)
   self.tab_widget.addTab(new_module, "📊 New Feature")
   ```

### Database Schema Changes

1. **Update schema** in `database.py`
2. **Create migration** in `migrate_schema()` method
3. **Increment `CURRENT_VERSION`** constant
4. **Test with existing data**

## Game Context

Understanding Ashes of Creation's artisan system is crucial for effective development:

### Artisan Profession System
- **22 Total Professions**: Divided into Gathering, Processing, Crafting
- **Progression Limits**: Only 2 professions can reach Grandmaster
- **Specialization Focus**: Encourages player interdependence
- **Guild Cooperation**: Requires 11+ players to cover all professions

### Node-Based Economy
- **Crafting Stations**: Located in nodes or freeholds
- **Tax Systems**: Each node can set tax rates (0-100%)
- **Resource Scarcity**: Time-gated by resource availability
- **Player-Driven**: Economy entirely controlled by players

### Target User Workflow
1. **Guild Coordination**: Plan crafting orders across multiple artisans
2. **Resource Management**: Track materials across different node storages
3. **Cost Optimization**: Calculate profitable crafting with tax considerations
4. **Market Analysis**: Track price trends for buying/selling decisions

## Adding New Features

### Before Starting
1. **Review existing modules** for similar patterns
2. **Check database schema** for required data
3. **Plan signal communication** with other modules
4. **Consider API data requirements**

### Implementation Pattern
1. **Design data flow** from source to display
2. **Create database schema** if needed
3. **Implement backend logic** in data_manager.py
4. **Create GUI module** following existing patterns
5. **Add signal connections** for inter-module communication
6. **Update main window** to include new module

### Example: Adding a New Feature
```python
# 1. Add database table (if needed)
def create_new_feature_table(self):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS new_feature (
            id INTEGER PRIMARY KEY,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

# 2. Add data manager methods
def get_new_feature_data(self):
    with ArtisanDatabase(self.db_path) as db:
        # Implementation here
        pass

# 3. Create module class
class NewFeatureModule(QWidget):
    # Signal definitions
    data_updated = pyqtSignal(dict)
    
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.setup_ui()

# 4. Register in MainWindow
def create_modules(self):
    # ... existing modules ...
    self.new_feature = NewFeatureModule(self.data_manager)
    self.tab_widget.addTab(self.new_feature, "🆕 New Feature")
```

## Testing Guidelines

### Integration Tests
```bash
# Test API connectivity and data flow
python test_api_integration.py
```

**Test Coverage**:
- API client functionality
- Database operations
- Data manager integration
- Error handling and recovery

### Manual Testing Checklist
1. **API Connectivity**: Test with/without internet
2. **Database Operations**: Create, read, update operations
3. **GUI Responsiveness**: Module switching and data updates
4. **Error Handling**: Invalid inputs and network issues
5. **Performance**: Large dataset handling

### Module Testing
Each module should be testable independently:
```python
# Example module test
def test_calculator_module():
    data_manager = DataManager()
    calculator = CalculatorModule(data_manager)
    # Test specific functionality
```

## Code Style

### Python Guidelines
- Follow **PEP 8** style guidelines
- Use **type hints** for function parameters
- Add **docstrings** for classes and methods
- Keep functions **focused and modular**

### PyQt6 Patterns
```python
# Signal definitions at class level
class MyModule(QWidget):
    data_changed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup UI components"""
        # UI creation code
    
    def connect_signals(self):
        """Connect signals and slots"""
        # Signal connections
```

### Database Patterns
```python
# Always use context managers
with ArtisanDatabase(self.db_path) as db:
    result = db.some_operation()
    return result

# Use parameterized queries
cursor.execute(
    "SELECT * FROM items WHERE name LIKE ?",
    (f"%{search_term}%",)
)
```

### Error Handling
```python
# Consistent error handling with logging
try:
    result = some_operation()
    return result
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    return None
```

## Common Development Tasks

### Adding a New Recipe Source
1. Update `api_client.py` to handle new endpoint
2. Modify `database.py` schema for new data fields
3. Update `data_manager.py` to process new recipe format
4. Enhance calculator module to display new recipe types

### Implementing Screenshot OCR
1. Add OpenCV and Tesseract dependencies
2. Create image processing utilities
3. Add OCR module to inventory manager
4. Implement error correction for OCR results

### Adding Export/Import Functionality
1. Design export format (JSON/CSV)
2. Add export methods to data_manager
3. Create import validation logic
4. Add GUI controls to relevant modules

---

This documentation should provide a solid foundation for understanding and contributing to the Ashes of Creation Artisan Toolbox. For questions not covered here, please refer to the source code comments and existing implementation patterns.