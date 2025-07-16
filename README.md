# Ashes of Creation Artisan Toolbox

A comprehensive desktop application for crafting calculations and inventory management in the Ashes of Creation MMORPG (Alpha phase). Built with PyQt6 and focused on Journeyman Scribe/Alchemy professions.

## 📋 Project Status

**Current Version**: 1.0.0-alpha  
**Phase**: Core Framework Complete  
**Next Phase**: GUI Polish & Advanced Features  

### ✅ Completed Features
- ✅ **API Integration Framework** - Robust ashescodex.com API client with caching
- ✅ **Database Layer** - SQLite with schema versioning and migrations
- ✅ **Data Management** - Unified data flow between API, cache, and database
- ✅ **Main Application** - PyQt6 GUI framework with modern dark theme
- ✅ **Calculator Module** - Tax-aware crafting cost calculations
- ✅ **Inventory Manager** - Node-based storage tracking
- ✅ **Market Analysis** - Price tracking and trend analysis
- ✅ **Inter-Module Communication** - Signal-based data flow between components

### 🚧 In Progress
- 🚧 **Batch Planner Module** - Multi-recipe optimization planning
- 🚧 **API Timeout Improvements** - Better handling of slow/failed requests
- 🚧 **Documentation** - Complete README and code documentation

### 📋 Planned Features
- 📋 **Settings System** - User preferences and configuration
- 📋 **Screenshot OCR** - Inventory scanning from game screenshots
- 📋 **Export/Import** - Data backup and sharing capabilities
- 📋 **Advanced Analytics** - Market trend predictions and alerts

## 🏗️ Architecture Overview

### Data Flow Diagram
```
Ashescodex API → Local Cache → Database → GUI Modules
                      ↓
               [Calculator] ← User Input → Results Display
                      ↓
               [Inventory Manager] ← Screenshot OCR (Future)
                      ↓
               [Market Analysis] → Price Trends
                      ↓
               [Batch Planner] → Optimized Orders
```

### Project Structure
```
AshesArtisanToolbox/
├── main.py                 # Application entry point
├── data_manager.py         # Unified data management layer
├── api_client.py          # Ashescodex API client with caching
├── database.py            # SQLite database operations
├── requirements.txt       # Python dependencies
├── test_api_integration.py # Integration tests
├── CLAUDE.md              # AI assistant context
│
├── gui/                   # GUI components
│   ├── __init__.py
│   └── main_window.py     # Main application window
│
├── modules/               # Toolbox modules
│   ├── __init__.py
│   ├── calculator.py      # Crafting cost calculator
│   ├── inventory_manager.py # Node-based inventory tracking
│   ├── market_analysis.py # Price tracking and trends
│   └── batch_planner.py   # Multi-recipe planning (WIP)
│
├── cache/                 # API response cache (auto-created)
└── resources/            # Icons and assets (future)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager
- Internet connection for API data sync

### Installation
1. **Clone/Download** the project to your local machine
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Test the framework**:
   ```bash
   python test_api_integration.py
   ```
4. **Run the application**:
   ```bash
   python main.py
   ```

### First Run Setup
1. The application will automatically initialize the database
2. First sync with ashescodex.com API will download ~190 pages of item data
3. Data is cached locally for offline use
4. Subsequent syncs only update changed items

## 🎮 Core Features

### 1. 🧮 Calculator Module
**Purpose**: Tax-aware crafting cost calculations with material price tracking

**Key Features**:
- Recipe search by profession (Scribe, Alchemist, etc.)
- Dynamic tax rate slider (0-100%)
- Custom material price overrides
- Real-time cost calculations
- Material availability checking
- Export to batch planner

**Data Flow**: `API Cache → Recipe Database → Calculator Interface → Results Display`

### 2. 📦 Inventory Manager
**Purpose**: Track materials across multiple node storage locations

**Key Features**:
- Multi-node inventory tracking
- Manual inventory entry
- Inventory overview with low-stock alerts
- Node-specific storage management
- Transaction history
- Future: Screenshot OCR integration

**Data Flow**: `User Input/Screenshots → Inventory Database → Overview Display`

### 3. 📈 Market Analysis
**Purpose**: Price tracking and market trend analysis for profitability

**Key Features**:
- Manual price recording by source (market/guildie/harvested)
- Price trend analysis (rising/falling/stable)
- Market recommendations
- Price history tracking
- Integration with calculator for dynamic pricing

**Data Flow**: `Price Records → Market Database → Trend Analysis → Calculator Updates`

### 4. 📋 Batch Planner (In Development)
**Purpose**: Multi-recipe optimization for efficient crafting orders

**Planned Features**:
- Multiple recipe batch planning
- Inventory availability checking
- Cost optimization algorithms
- Material requirement aggregation
- Priority-based crafting orders

## 🔧 Technical Implementation

### API Integration
- **Endpoint**: `https://api.ashescodex.com/items?page=1`
- **Rate Limiting**: 1 second between requests (respectful to unofficial API)
- **Caching**: 24-hour local JSON cache
- **Error Handling**: Exponential backoff with retry logic
- **Pagination**: Handles ~190 pages of item data

### Database Schema
**SQLite Database** with the following key tables:
- `items` - Game items from API
- `recipes` - Crafting recipes with components
- `inventory` - Node-based item storage
- `market_prices` - Price tracking with source attribution
- `transactions` - Crafting and trading history
- `settings` - User preferences

### GUI Framework
- **Framework**: PyQt6 with modern dark theme
- **Architecture**: Tab-based interface with modular components
- **Communication**: Signal-based inter-module data flow
- **Styling**: Custom CSS for professional appearance

## 🔍 Development Guide

### Code Organization
```python
# Main application structure
main.py                 # Entry point and app lifecycle
gui/main_window.py      # Main window with tab management
modules/calculator.py   # Individual feature modules
data_manager.py         # Unified data access layer
api_client.py          # External API integration
database.py            # Data persistence layer
```

### Key Classes
- `ArtisanToolboxApp` - Main application class
- `MainWindow` - Primary GUI container
- `DataManager` - Unified data operations
- `AshesCodexAPIClient` - API client with caching
- `ArtisanDatabase` - Database operations
- `CalculatorModule` - Crafting calculations
- `InventoryManagerModule` - Storage tracking
- `MarketAnalysisModule` - Price analysis

### Inter-Module Communication
Modules communicate via PyQt signals:
```python
# Example: Calculator notifies inventory when items are crafted
calculator.craft_completed.connect(inventory.update_inventory_from_craft)

# Example: Market analysis updates calculator prices
market.price_updated.connect(calculator.update_material_price)
```

### Database Operations
```python
# Example: Adding items to inventory
with ArtisanDatabase() as db:
    success = db.update_inventory(item_id, node_name, quantity, avg_cost)
```

### API Usage
```python
# Example: Fetching items with proper rate limiting
async with AshesCodexAPIClient() as client:
    items = await client.get_all_items(max_pages=200)
```

## 🧪 Testing

### Integration Tests
```bash
python test_api_integration.py
```

**Tests Include**:
- API client functionality
- Database operations
- Data manager integration
- Error handling and recovery

### Manual Testing
1. **API Connectivity**: Test with/without internet
2. **Database Operations**: Create, read, update operations
3. **GUI Responsiveness**: Module switching and data updates
4. **Error Handling**: Invalid inputs and network issues

## 📊 Configuration

### Settings Management
User preferences are stored in the SQLite database:
- `last_api_sync` - Last successful API synchronization
- `default_tax_rate` - Default node tax rate
- `preferred_profession` - Default profession filter
- `theme_preference` - UI theme selection (future)

### Cache Management
- **Location**: `./cache/` directory
- **Format**: JSON files per API endpoint
- **Lifetime**: 24 hours
- **Cleanup**: Automatic on application start

## 🚨 Troubleshooting

### Common Issues

**1. API Sync Fails**
```
Error: Failed to sync with ashescodex.com
Solution: Check internet connection, wait for rate limiting, or use cached data
```

**2. Database Locked**
```
Error: Database is locked
Solution: Close other instances of the application
```

**3. Module Not Loading**
```
Error: Failed to initialize modules
Solution: Check PyQt6 installation and Python version
```

### Debug Mode
Enable detailed logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

### Code Style
- Follow PEP 8 Python style guidelines
- Use type hints for function parameters
- Add docstrings for classes and methods
- Keep functions focused and modular

### Adding New Modules
1. Create module file in `modules/` directory
2. Inherit from `QWidget` for GUI components
3. Use `pyqtSignal` for inter-module communication
4. Register in `main_window.py`

### Database Changes
1. Update schema in `database.py`
2. Create migration in `migrate_schema()` method
3. Increment `CURRENT_VERSION` constant
4. Test with existing data

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **Ashescodex.com** for providing the unofficial API
- **Ashes of Creation** by Intrepid Studios
- **PyQt6** for the GUI framework
- **SQLite** for embedded database support

---

**Note**: This is an unofficial tool for personal/guild use. It does not modify game files or violate terms of service. All data is sourced from the publicly available ashescodex.com API.