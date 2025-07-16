# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Ashes of Creation Artisan Toolbox** is a PyQt6 desktop application designed for the Ashes of Creation MMORPG (Alpha phase). The application focuses on crafting calculation and inventory management for artisan professions, specifically targeting Journeyman Scribe/Alchemy professions.

**Core Objective**: Desktop app for crafting calculation + inventory management across nodes.

## Key Features

### 1. API-Driven Recipe System
- **Primary Data Source**: Ashescodex.com API
- **API Endpoint**: `https://api.ashescodex.com/items?page=1`
- Comprehensive recipe database with component expansion
- Profession-specific highlighting (Scribe/Alchemy focus)
- Multi-craft and multi-rarity support

### 2. Tax-Aware Crafting Calculator
- **Formula**: `Total Cost = ∑(Material Costs) + [Base Fee × (1 + Node Tax)]`
- Dynamic tax rate slider (0-100%)
- Material price tracking with market analysis
- Quantity selector for batch calculations
- Profit optimization for different pricing tiers (market/guildie/personal)

### 3. Node-Based Inventory Manager
- Cross-node storage tracking
- Screenshot-based inventory scanning (OpenCV + Tesseract OCR)
- Material location tracking
- Auto-deduct on craft with history/undo functionality
- Minecraft creative menu style storage visualization

### 4. Batch Order Planning
- Recipe selection and quantity planning
- Inventory availability checking
- Material requirement calculation
- Auto-scaling based on available inventory

### 5. Market Price Tracking
- Purchase price history
- Source tracking (purchased/guildie/harvested)
- Market trend analysis and graphing
- Competitive pricing recommendations

## Technical Stack

```python
# APPROVED TECHNOLOGIES
GUI: PyQt6 (QMainWindow, QTabWidget, QTableView)
API Client: Requests + AsyncIO
Database: SQLite3 (with schema versioning)
Data Cache: Local JSON files
Future: OpenCV+Tesseract OCR for inventory scanning
```

## Architecture

The application follows a multi-tab desktop GUI architecture:
- **Main Calculator Tab**: Recipe calculations with tax integration
- **Inventory Tab**: Node-based storage management
- **Batch Planner Tab**: Order planning and optimization
- **Market Analysis Tab**: Price tracking and trends

## Common Development Commands

```bash
# Install dependencies
pip install PyQt6 requests asyncio sqlite3 opencv-python pytesseract

# Run the application
python main.py  # Or primary entry point file

# Database migration/setup
python -c "from database import init_db; init_db()"
```

## API Integration

The application integrates with Ashescodex.com API for recipe data:
- Caches API responses locally (JSON files)
- Handles pagination for complete item database
- Implements rate limiting for API calls
- Provides offline fallback from cached data

## Database Schema

SQLite3 database with versioning for:
- Recipe data (items, components, crafting requirements)
- Inventory tracking (locations, quantities, prices)
- Transaction history (purchases, sales, crafts)
- Market price history
- User preferences and settings

## Compliance Notes

- **No Game Modification**: Application operates externally to game client
- **Screenshot Analysis Only**: Uses OCR for inventory reading (non-intrusive)
- **Market Data**: Tracks user-input prices, not automated market scanning
- **Terms Compliance**: Designed to avoid ToS violations while providing utility