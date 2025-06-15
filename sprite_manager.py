"""
Sprite Management System
=======================

Centralized system for loading and managing game sprites from spritesheets.

Key Features:
1. Spritesheet Loading: Automatically load and tile spritesheets
2. Sprite Extraction: Extract individual sprites by index
3. Multi-tile Support: Handle sprites spanning multiple tiles
4. Fallback Graphics: Generate colored rectangles when sprites fail to load
5. Performance Optimization: Efficient sprite caching and reuse

The sprite manager provides a clean interface between the game logic
and graphical assets, allowing for easy sprite swapping and fallback
handling when assets are missing.

Supported Formats:
- PNG spritesheets with transparency
- Configurable tile dimensions
- Index-based sprite selection
- Multi-tile sprite composition

Usage:
- Load spritesheets once at startup
- Extract sprites by name and index as needed
- Automatic fallback to colored shapes if sprites unavailable
"""

import pygame

class SpriteManager:
    """
    Central manager for all game sprites and spritesheets.
    
    Handles:
    - Loading spritesheets from image files
    - Extracting individual sprites by index
    - Creating fallback graphics when sprites fail to load
    - Multi-tile sprite composition for large elements
    - Performance optimization through efficient storage
    
    The sprite manager abstracts away the complexity of working with
    spritesheets and provides a simple interface for the rest of the game.
    """
    def __init__(self):
        self.spritesheets = {}
        self.sprites = {}
    
    def load_spritesheet(self, name, filepath, tile_width, tile_height):
        """Load a spritesheet and store it"""
        try:
            self.spritesheets[name] = {
                'surface': pygame.image.load(filepath).convert_alpha(),
                'tile_width': tile_width,
                'tile_height': tile_height
            }
            print(f"Loaded spritesheet: {name}")
        except pygame.error as e:
            print(f"Could not load spritesheet {filepath}: {e}")
            # Create a fallback colored rectangle
            fallback = pygame.Surface((tile_width, tile_height), pygame.SRCALPHA)
            fallback.fill((200, 200, 200))
            self.spritesheets[name] = {
                'surface': fallback,
                'tile_width': tile_width,                'tile_height': tile_height
            }
    
    def get_sprite(self, spritesheet_name, index):
        """Extract a specific sprite from the spritesheet by index"""
        if spritesheet_name not in self.spritesheets:
            return None
            
        sheet_data = self.spritesheets[spritesheet_name]
        sheet = sheet_data['surface']
        tile_w = sheet_data['tile_width']
        tile_h = sheet_data['tile_height']
        
        # Calculate position in spritesheet
        cols = sheet.get_width() // tile_w
        col = index % cols
        row = index // cols
        
        # Extract the sprite
        sprite_rect = pygame.Rect(col * tile_w, row * tile_h, tile_w, tile_h)
        sprite = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
        sprite.blit(sheet, (0, 0), sprite_rect)
        
        return sprite
    
    def get_multi_tile_sprite(self, spritesheet_name, start_index, width_tiles, height_tiles):
        """Extract a sprite spanning multiple tiles"""
        if spritesheet_name not in self.spritesheets:
            return None
            
        sheet_data = self.spritesheets[spritesheet_name]
        sheet = sheet_data['surface']
        tile_w = sheet_data['tile_width']
        tile_h = sheet_data['tile_height']
        
        # Calculate starting position
        cols = sheet.get_width() // tile_w
        start_col = start_index % cols
        start_row = start_index // cols
        
        # Create surface for the multi-tile sprite
        sprite_w = tile_w * width_tiles
        sprite_h = tile_h * height_tiles
        sprite = pygame.Surface((sprite_w, sprite_h), pygame.SRCALPHA)
        
        # Extract the region
        source_rect = pygame.Rect(
            start_col * tile_w, 
            start_row * tile_h, 
            sprite_w, 
            sprite_h
        )
        sprite.blit(sheet, (0, 0), source_rect)
        
        return sprite

# Global sprite manager instance
sprite_manager = SpriteManager()
