"""
Rarity system for Ashes of Creation Artisan Toolbox.
Defines rarity levels, utility functions, and component type handling.
"""

from enum import Enum, IntEnum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

class ItemRarity(IntEnum):
    """
    Item rarity levels in Ashes of Creation.
    IntEnum allows for easy comparison (Common < Uncommon < Rare, etc.)
    """
    COMMON = 1
    UNCOMMON = 2
    RARE = 3
    HEROIC = 4
    EPIC = 5
    LEGENDARY = 6

class ComponentType(Enum):
    """
    Component types for crafting recipes.
    Quality components are rarity-sensitive, Basic components are not.
    """
    QUALITY = "quality"    # Rarity matters (gathered/processed materials)
    BASIC = "basic"        # Rarity doesn't matter (NPC vendor items)

@dataclass
class RarityInfo:
    """Information about a specific rarity level"""
    name: str
    display_name: str
    color_hex: str
    sort_order: int

# Rarity information mapping
RARITY_INFO: Dict[ItemRarity, RarityInfo] = {
    ItemRarity.COMMON: RarityInfo("common", "Common", "#FFFFFF", 1),
    ItemRarity.UNCOMMON: RarityInfo("uncommon", "Uncommon", "#1EFF00", 2),
    ItemRarity.RARE: RarityInfo("rare", "Rare", "#0070DD", 3),
    ItemRarity.HEROIC: RarityInfo("heroic", "Heroic", "#A335EE", 4),
    ItemRarity.EPIC: RarityInfo("epic", "Epic", "#FF8000", 5),
    ItemRarity.LEGENDARY: RarityInfo("legendary", "Legendary", "#E6CC80", 6),
}

class RarityManager:
    """
    Utility class for rarity-related operations.
    Handles rarity conversions, validations, and calculations.
    """
    
    @staticmethod
    def string_to_rarity(rarity_str: str) -> ItemRarity:
        """Convert string to ItemRarity enum"""
        if not rarity_str:
            return ItemRarity.COMMON
            
        rarity_str = rarity_str.lower().strip()
        
        for rarity in ItemRarity:
            if RARITY_INFO[rarity].name == rarity_str:
                return rarity
                
        # Default to common if not found
        return ItemRarity.COMMON
    
    @staticmethod
    def rarity_to_string(rarity: ItemRarity) -> str:
        """Convert ItemRarity enum to string"""
        return RARITY_INFO[rarity].name
    
    @staticmethod
    def get_display_name(rarity: ItemRarity) -> str:
        """Get human-readable display name for rarity"""
        return RARITY_INFO[rarity].display_name
    
    @staticmethod
    def get_color_hex(rarity: ItemRarity) -> str:
        """Get color hex code for rarity"""
        return RARITY_INFO[rarity].color_hex
    
    @staticmethod
    def get_all_rarities() -> List[ItemRarity]:
        """Get all rarities in order"""
        return sorted(ItemRarity, key=lambda x: x.value)
    
    @staticmethod
    def get_rarity_display_list() -> List[str]:
        """Get list of rarity display names for UI dropdowns"""
        return [RARITY_INFO[rarity].display_name for rarity in RarityManager.get_all_rarities()]
    
    @staticmethod
    def can_craft_rarity(component_rarities: List[ItemRarity], 
                        target_rarity: ItemRarity,
                        quality_rating: int = 0) -> bool:
        """
        Determine if components can craft target rarity.
        For now, assume same rarity components create same rarity output.
        Quality rating consideration for future implementation.
        """
        if not component_rarities:
            return False
            
        # Basic implementation: all quality components must be at least target rarity
        min_required_rarity = target_rarity
        
        # Future: Quality rating could allow lower rarity components
        # if quality_rating >= some_threshold:
        #     min_required_rarity = max(ItemRarity.COMMON, target_rarity - 1)
        
        return all(comp_rarity >= min_required_rarity for comp_rarity in component_rarities)
    
    @staticmethod
    def get_crafting_result_rarity(quality_component_rarities: List[ItemRarity],
                                  quality_rating: int = 0) -> ItemRarity:
        """
        Determine the rarity of crafted item based on quality components.
        For now, use minimum quality component rarity.
        """
        if not quality_component_rarities:
            return ItemRarity.COMMON
            
        # Basic implementation: result rarity = minimum component rarity
        result_rarity = min(quality_component_rarities)
        
        # Future: Quality rating could boost result rarity
        # if quality_rating >= some_threshold:
        #     result_rarity = min(ItemRarity.LEGENDARY, result_rarity + 1)
        
        return result_rarity
    
    @staticmethod
    def create_item_key(item_id: int, rarity: ItemRarity) -> str:
        """Create unique key for item+rarity combination"""
        return f"{item_id}_{rarity.value}"
    
    @staticmethod
    def parse_item_key(item_key: str) -> Tuple[int, ItemRarity]:
        """Parse item key back to item_id and rarity"""
        try:
            parts = item_key.split('_')
            if len(parts) != 2:
                raise ValueError("Invalid item key format")
            
            item_id = int(parts[0])
            rarity = ItemRarity(int(parts[1]))
            return item_id, rarity
            
        except (ValueError, IndexError):
            # Default to common if parsing fails
            return 0, ItemRarity.COMMON

@dataclass
class ComponentRequirement:
    """Represents a component requirement for a recipe"""
    item_id: int
    quantity: int
    component_type: ComponentType
    rarity: Optional[ItemRarity] = None  # Only relevant for quality components

@dataclass
class RarityAwareItem:
    """Represents an item with rarity information"""
    item_id: int
    name: str
    base_rarity: ItemRarity
    current_rarity: ItemRarity
    item_type: str
    profession: Optional[str] = None
    
    @property
    def unique_key(self) -> str:
        """Get unique key for this item+rarity combination"""
        return RarityManager.create_item_key(self.item_id, self.current_rarity)
    
    @property
    def display_name(self) -> str:
        """Get display name with rarity"""
        rarity_name = RarityManager.get_display_name(self.current_rarity)
        return f"{rarity_name} {self.name}"
    
    @property
    def color_hex(self) -> str:
        """Get color for this item's rarity"""
        return RarityManager.get_color_hex(self.current_rarity)

def get_component_type_from_item(item_data: Dict) -> ComponentType:
    """
    Determine component type from item data.
    This is a heuristic - in practice, this information should come from the API.
    """
    # Basic heuristic: if item has profession, it's likely a quality component
    if item_data.get('profession'):
        return ComponentType.QUALITY
    
    # Items with certain types are typically basic components
    basic_types = ['paper', 'ink', 'thread', 'flux', 'solvent']
    item_type = item_data.get('type', '').lower()
    
    if any(basic_type in item_type for basic_type in basic_types):
        return ComponentType.BASIC
    
    # Default to quality component
    return ComponentType.QUALITY

# Utility functions for UI integration
def get_rarity_style_sheet(rarity: ItemRarity) -> str:
    """Get CSS stylesheet for rarity color"""
    color = RarityManager.get_color_hex(rarity)
    return f"color: {color}; font-weight: bold;"

def apply_rarity_style_to_item(item, rarity: ItemRarity):
    """Apply rarity color to QTableWidgetItem using foreground color"""
    from PyQt6.QtGui import QColor
    from PyQt6.QtCore import Qt
    
    color = RarityManager.get_color_hex(rarity)
    qcolor = QColor(color)
    item.setForeground(qcolor)
    
    # Make text bold for better visibility
    font = item.font()
    font.setBold(True)
    item.setFont(font)

def format_item_with_rarity(item_name: str, rarity: ItemRarity, 
                          quantity: int = None) -> str:
    """Format item name with rarity for display"""
    rarity_name = RarityManager.get_display_name(rarity)
    
    if quantity is not None:
        return f"{quantity}x {rarity_name} {item_name}"
    else:
        return f"{rarity_name} {item_name}"

# Example usage and testing
if __name__ == "__main__":
    # Test rarity conversions
    print("Testing rarity system...")
    
    # Test string conversion
    common = RarityManager.string_to_rarity("common")
    print(f"Common rarity: {common} -> {RarityManager.rarity_to_string(common)}")
    
    # Test rarity comparison
    print(f"Uncommon > Common: {ItemRarity.UNCOMMON > ItemRarity.COMMON}")
    
    # Test crafting logic
    component_rarities = [ItemRarity.RARE, ItemRarity.RARE, ItemRarity.UNCOMMON]
    result_rarity = RarityManager.get_crafting_result_rarity(component_rarities)
    print(f"Crafting result rarity: {RarityManager.get_display_name(result_rarity)}")
    
    # Test item key creation
    key = RarityManager.create_item_key(123, ItemRarity.EPIC)
    item_id, rarity = RarityManager.parse_item_key(key)
    print(f"Item key: {key} -> ID: {item_id}, Rarity: {RarityManager.get_display_name(rarity)}")