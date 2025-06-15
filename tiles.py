"""
Tile Definition and Graphics System
==================================

This module defines the various tile types available in SpaceScrapers and
handles their visual representation through sprites or colored shapes.

Core Features:

1. Tile Type System:
   - Rectangle: Versatile building block for foundations and walls
   - Square: Compact, stable tile for solid construction
   - Beam: Long, narrow tile perfect for bridges and supports
   - Triangle: Angled tile for roofs and structural reinforcement

2. Graphics Management:
   - Sprite-based rendering from spritesheets
   - Fallback colored shapes when sprites unavailable
   - Automatic size detection from sprite dimensions
   - Rotation and caching system for performance
   - Multi-tile sprite support for large structural elements

3. Physics Properties:
   - Mass, friction, and restitution values per tile type
   - Size and collision detection properties
   - Support for debug visualization modes

4. Debug Features:
   - Visual collision detection feedback
   - Support point visualization
   - Physics property display
   - Toggle-able debug modes for development

Design Philosophy:
- Each tile type has unique properties affecting gameplay
- Visual representation separated from physics simulation
- Extensible system for adding new tile types
- Performance optimization through sprite caching
"""

import pygame
import math

# Configuration constants
DEBUG_MODE = False  # Set to True to show collision detection lines
COLLISION_DEBUG = False  # Set to True to show collision detection feedback

# Try to import sprite_manager, create fallback if not available
try:
    from sprite_manager import sprite_manager
except ImportError:
    # Create a minimal fallback sprite manager
    class FallbackSpriteManager:
        def get_sprite(self, name, index):
            return None
    sprite_manager = FallbackSpriteManager()

class TileShape:
    """
    Base class for all tile types in SpaceScrapers.
    
    Core Functionality:
    - Sprite management with automatic size detection
    - Rotation and caching for performance optimization
    - Debug visualization for collision detection
    - Physics property definitions (mass, friction, etc.)
    - Support for both sprite-based and colored rendering
    
    Visual Features:
    - Multi-tile sprite support for complex shapes
    - Rotation caching to improve performance
    - Debug lines to show collision detection points
    - Fallback rendering when sprites are unavailable
    
    This class serves as the foundation for all tile types and handles
    the complex interactions between visual representation and game logic.
    """
    def __init__(self, color=(200,200,200), sprite_name=None, sprite_index=0):
        self.color = color
        self.angle = 0  # rotation in degrees
        self.detection_lines = []  # List to store detection lines
        self.sprite_name = sprite_name
        self.sprite_index = sprite_index
        self.sprite_cache = {}  # Cache rotated sprites
        self._size = None  # Cache for actual sprite size
        
        # Initialize size from sprite if available
        self._initialize_size()

    def _initialize_size(self):
        """Initialize the size property based on the actual sprite dimensions"""
        if self.sprite_name:
            sprite = self.get_sprite()
            if sprite:
                # Get actual sprite dimensions
                self._size = sprite.get_size()
                print(f"Tile {self.__class__.__name__} sprite size: {self._size}")
                return
        
        # Fallback to class-defined size if no sprite or sprite unavailable        if hasattr(self, 'size'):
            self._size = self.size
        else:
            self._size = (32, 32)  # Default fallback size
            print(f"Using fallback size for {self.__class__.__name__}: {self._size}")
    
    @property
    def size(self):
        """Get the actual size of the tile (from sprite or fallback)"""
        if self._size is None:
            self._initialize_size()
        return self._size

    def get_sprite(self):
        """Get the sprite for this tile"""
        if self.sprite_name:
            # Check if this tile uses multi-tile sprites
            if hasattr(self, 'multi_tile_config'):
                config = self.multi_tile_config
                return sprite_manager.get_multi_tile_sprite(
                    self.sprite_name, 
                    config['start_index'], 
                    config['width_tiles'], 
                    config['height_tiles']
                )
            else:
                return sprite_manager.get_sprite(self.sprite_name, self.sprite_index)
        return None

    def get_rotated_sprite(self, angle):
        """Get a cached rotated sprite"""
        # Round angle to nearest 5 degrees for caching efficiency
        cache_angle = round(angle / 5) * 5
        cache_key = f"{self.sprite_name}_{self.sprite_index}_{cache_angle}"
        
        if cache_key not in self.sprite_cache:
            base_sprite = self.get_sprite()
            if base_sprite:
                self.sprite_cache[cache_key] = pygame.transform.rotate(base_sprite, cache_angle)
            else:
                # Fallback to colored surface - use a default size if self.size not available
                size = getattr(self, 'size', (32, 32))
                surf = pygame.Surface(size, pygame.SRCALPHA)
                surf.fill(self.color)
                self.sprite_cache[cache_key] = pygame.transform.rotate(surf, cache_angle)
        
        return self.sprite_cache[cache_key]

    def rotate(self, angle):
        # Rotation is purely cosmetic/animation - doesn't affect physics collision
        self.angle = (self.angle + angle) % 360
    
    def get_mask(self):
        # Returns a pygame.Mask for collision - use NON-ROTATED sprite for physics
        # Rotation is purely cosmetic, physics always uses original orientation
        sprite = self.get_sprite()  # Get original sprite without rotation
        if sprite:
            return pygame.mask.from_surface(sprite)
        else:
            # Fallback: create surface and draw shape for mask generation (no rotation)
            surf = pygame.Surface(self.size, pygame.SRCALPHA)
            self.draw_shape(surf)
            return pygame.mask.from_surface(surf)

    def draw(self, surface, pos=(0,0)):
        # Use sprite if available, otherwise draw shape
        sprite = self.get_rotated_sprite(self.angle)
        if sprite:
            # Center the sprite at the position
            sprite_rect = sprite.get_rect()
            sprite_rect.center = (pos[0] + self.size[0]//2, pos[1] + self.size[1]//2)
            surface.blit(sprite, sprite_rect.topleft)
        else:
            # Fallback to drawing shapes
            self.draw_shape(surface, pos)
    
    def draw_with_debug(self, surface, pos=(0,0)):
        # Draw the tile first
        self.draw(surface, pos)
        # Then draw detection lines separately (only for debug)
        self.draw_detection_lines(surface, pos)
    
    def draw_shape(self, surface, pos=(0,0)):
        # To be implemented by subclasses - fallback drawing
        pass

    def draw_detection_lines(self, surface, pos):
        if DEBUG_MODE:
            # Calculate detection points based on the actual rotated bottom edge
            width, height = self.size
            x, y = pos
            
            # Calculate the center of the tile
            center_x = x + width // 2
            center_y = y + height // 2
            
            # Calculate the four corners relative to center
            half_width = width // 2
            half_height = height // 2
            corners = [
                (-half_width, -half_height),  # top-left
                (half_width, -half_height),   # top-right
                (half_width, half_height),    # bottom-right
                (-half_width, half_height)    # bottom-left
            ]
              # Rotate the corners based on the tile's rotation
            import math
            angle_rad = math.radians(self.angle)
            cos_angle = math.cos(angle_rad)
            sin_angle = math.sin(angle_rad)
            
            rotated_corners = []
            for corner_x, corner_y in corners:
                # Rotate the point around the origin
                rotated_x = corner_x * cos_angle - corner_y * sin_angle
                rotated_y = corner_x * sin_angle + corner_y * cos_angle
                # Translate to the tile's actual position
                world_x = center_x + rotated_x
                world_y = center_y + rotated_y
                rotated_corners.append((world_x, world_y))
            
            # Find the two corners with the highest Y values (bottom-most after rotation)
            sorted_corners = sorted(rotated_corners, key=lambda point: point[1], reverse=True)
            bottom_corners = sorted_corners[:2]
            
            # Sort the bottom corners by X coordinate to get left and right
            bottom_corners.sort(key=lambda point: point[0])
            bottom_left = bottom_corners[0]
            bottom_right = bottom_corners[1]
            
            # Calculate middle point of the bottom edge
            bottom_middle = ((bottom_left[0] + bottom_right[0]) / 2, (bottom_left[1] + bottom_right[1]) / 2)
            
            # Detection points are the actual bottom corners and middle
            detection_points = [bottom_middle, bottom_left, bottom_right]
            
            # Draw short lines downward from each detection point
            line_length = 10
            for point in detection_points:
                start_point = (int(point[0]), int(point[1]))
                end_point = (int(point[0]), int(point[1] + line_length))
                pygame.draw.line(surface, (255, 0, 0), start_point, end_point, 2)
            
            # Draw detection points as small colored circles for identification
            for i, point in enumerate(detection_points):
                if i == 0:
                    circle_color = (255, 255, 0)  # Yellow for middle
                elif i == 1:
                    circle_color = (255, 0, 255)  # Magenta for left
                else:
                    circle_color = (0, 255, 255)  # Cyan for right
                pygame.draw.circle(surface, circle_color, (int(point[0]), int(point[1])), 3)

class RectangleTile(TileShape):
    def __init__(self):
        super().__init__(sprite_name="blocks", sprite_index=26)  
        # Configure as 2x1 multi-tile (twice as wide)
        self.multi_tile_config = {
            'start_index': 26,  # Starting position in tileset
            'width_tiles': 2,   # 2 tiles wide
            'height_tiles': 1   # 1 tile high
        }
        # Override size for rectangle - twice as wide as standard tile
        self._size = (192, 96)  # 2x1 tiles = 192x96 pixels
        # Physics properties
        self.mass = 1.5  # Heavier due to larger size
        self.inertia = 1.2
        self.friction = 0.98
        self.restitution = 0.2
    
    def draw_shape(self, surface, pos=(0,0)):
        # Fallback drawing method
        rect = pygame.Rect(pos, self.size)
        rotated = pygame.transform.rotate(
            pygame.Surface(self.size, pygame.SRCALPHA), self.angle)
        pygame.draw.rect(rotated, self.color, rotated.get_rect())
        surface.blit(rotated, rect.topleft)

class SquareTile(TileShape):
    def __init__(self):
        super().__init__(sprite_name="blocks", sprite_index=28)  
        # Physics properties
        self.mass = 0.8
        self.inertia = 0.8
        self.friction = 0.98
        self.restitution = 0.2

    def draw_shape(self, surface, pos=(0,0)):
        rotated = pygame.transform.rotate(
            pygame.Surface(self.size, pygame.SRCALPHA), self.angle)
        pygame.draw.rect(rotated, self.color, rotated.get_rect())
        surface.blit(rotated, pos)

class BeamTile(TileShape):
    def __init__(self):
        super().__init__(sprite_name="blocks", sprite_index=37)
        # Configure as 0.5x2 multi-tile (half tile wide, 2 tiles high) - VERTICAL beam
        self.multi_tile_config = {
            'start_index': 37,   # Starting position in tileset
            'width_tiles': 1,   # 1 tile wide
            'height_tiles': 2   # 2 tiles high
        }
        # Override size for beam - half tile wide, 2 tiles high (VERTICAL)
        self._size = (48, 192)  # 0.5x2 tiles = 48x192 pixels (tall and thin)
        # Physics properties - lighter and more unstable due to thin profile
        self.mass = 0.8
        self.inertia = 0.4
        self.friction = 0.96
        self.restitution = 0.3
    
    def get_sprite(self):
        """Get the sprite for this tile with custom sizing for vertical beam"""
        if self.sprite_name and hasattr(self, 'multi_tile_config'):
            config = self.multi_tile_config
            full_sprite = sprite_manager.get_multi_tile_sprite(
                self.sprite_name, 
                config['start_index'], 
                config['width_tiles'], 
                config['height_tiles']
            )
            if full_sprite:
                # Scale to create a thin vertical beam
                scaled = pygame.transform.scale(full_sprite, self._size)
                return scaled
        return super().get_sprite()
    
    def draw_shape(self, surface, pos=(0,0)):
        s = pygame.Surface(self.size, pygame.SRCALPHA)
        pygame.draw.rect(s, self.color, (0, 0, self.size[0], self.size[1]))
        rotated = pygame.transform.rotate(s, self.angle)
        surface.blit(rotated, pos)


# Dictionary of all available tile types
tile_types = {
    'rectangle': RectangleTile,
    'square': SquareTile,
    'beam': BeamTile,
}
