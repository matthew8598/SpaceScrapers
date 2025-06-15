"""
Tile Placement and Physics System
=================================

This module handles:
- Tile drag & drop mechanics from selection area to build area
- Pixel-perfect collision detection between tiles  
- Realistic physics simulation (gravity, friction, restitution)
- Tumbling and rotation effects when tiles become unstable
- Support detection to determine when tiles are properly supported

Key Features:
- Visual rotation feedback (separate from physics collision)
- Smart tumbling only when tiles are unsupported and not on ground
- Progressive physics with damping for stable stacking
- Gravity switching based on tile support state

Physics Implementation:
- Uses NumPy for vector math and smooth physics integration
- Pixel-perfect collision using Pygame masks
- Support detection with bottom-edge detection points
- Realistic tumbling based on center-of-mass calculations
"""

import pygame
import numpy as np
from storage.level_storage import LevelStorage
from tiles import tile_types

# Import animation manager for feedback effects
try:
    from animations import animation_manager
except ImportError:
    # Fallback if animations not available
    class FallbackAnimationManager:
        def add_tile_placement_feedback(self, pos): pass
        def add_tile_rotation(self, tile, angle): pass
    animation_manager = FallbackAnimationManager()

# Physics constants
GRAVITY = 500  # Pixels per second squared - realistic but not too harsh
global gravity_switch
gravity_switch = True  # Global switch to enable/disable gravity effects

class Tile:
    """
    Individual tile with physics properties and visual effects.
    
    Handles:
    - Position and velocity for physics simulation
    - Visual rotation effects (separate from collision detection)
    - Support detection and gravity state management
    - Collision detection with other tiles and ground
    - Tumbling physics when inadequately supported
    """
    
    def __init__(self, tile_obj, position, gravity_switch=gravity_switch):
        # Core tile properties
        self.tile_obj = tile_obj  # Reference to TileShape instance from tiles.py
        self.position = np.array(position, dtype=float)  # World position (center point)
        self.dragging = False  # Whether tile is currently being dragged
        self.tile_type = type(tile_obj).__name__.lower().replace('tile', '')
        self.gravity_switch = gravity_switch  # Individual gravity state
        
        # Visual effects (separate from physics)
        self.visual_rotation = 0.0  # Cosmetic rotation in degrees (±45° max)

        # Physics properties initialized from tile definition
        self.velocity = np.zeros(2, dtype=float)  # [x, y] velocity vector
        self.angular_velocity = 0.0  # Rotational velocity (for future use)
        
        # Get physics constants from the tile object (defined in tiles.py)
        self.mass = getattr(tile_obj, "mass", 1.0)
        self.inertia = getattr(tile_obj, "inertia", 1.0)
        self.friction = getattr(tile_obj, "friction", 0.98)  # Velocity damping
        self.restitution = getattr(tile_obj, "restitution", 0.2)  # Bounce factor
        self.is_static = False  # True when tile comes to rest
    
    def draw(self, surface):
        """
        Render the tile with optional visual rotation effects.
        
        Visual rotation is purely cosmetic and doesn't affect collision detection.
        Physics collision always uses the original upright orientation.
        """
        # Import tiles module for debug mode checking
        import tiles
        
        # Calculate drawing position (top-left corner from center point)
        draw_x = int(self.position[0] - self.tile_obj.size[0] // 2)
        draw_y = int(self.position[1] - self.tile_obj.size[1] // 2)
        
        # Apply visual rotation if present (cosmetic feedback only)
        if hasattr(self, 'visual_rotation') and abs(self.visual_rotation) > 0.1:
            # Create surface for the tile sprite/shape
            tile_surface = pygame.Surface(self.tile_obj.size, pygame.SRCALPHA)
            
            # Draw tile content (with or without debug info)
            if hasattr(tiles, 'DEBUG_MODE') and tiles.DEBUG_MODE:
                self.tile_obj.draw_with_debug(tile_surface, pos=(0, 0))
            else:
                self.tile_obj.draw(tile_surface, pos=(0, 0))
            
            # Apply rotation and center properly
            rotated_surface = pygame.transform.rotate(tile_surface, self.visual_rotation)
            new_rect = rotated_surface.get_rect(center=(self.position[0], self.position[1]))
            surface.blit(rotated_surface, new_rect.topleft)
        else:
            # No visual rotation - draw normally
            if hasattr(tiles, 'DEBUG_MODE') and tiles.DEBUG_MODE:
                self.tile_obj.draw_with_debug(surface, pos=(draw_x, draw_y))
            else:
                self.tile_obj.draw(surface, pos=(draw_x, draw_y))

    def get_rect(self):
        """Get bounding rectangle for the tile."""
        w, h = self.tile_obj.size
        return pygame.Rect(int(self.position[0] - w // 2), int(self.position[1] - h // 2), w, h)

    def get_mask(self):
        """Generate collision mask for pixel-perfect collision detection."""
        surf = pygame.Surface(self.tile_obj.size, pygame.SRCALPHA)
        self.tile_obj.draw(surf)
        return pygame.mask.from_surface(surf)

    def apply_physics(self, dt, gravity=GRAVITY):
        """
        Apply physics simulation to the tile including gravity and friction.
        
        Physics Pipeline:
        1. Apply gravitational acceleration (if gravity enabled)
        2. Apply friction damping to reduce velocity over time
        3. Integrate velocity to update position
        4. Manage static state for performance optimization
        
        Args:
            dt: Delta time for physics integration
            gravity: Gravitational acceleration (pixels/sec²)
        """
        # Only apply physics if not static (performance optimization)
        if self.is_static:
            return
            
        # Apply gravity if enabled (controlled by support detection)
        if self.gravity_switch:
            self.velocity[1] += gravity * dt
        else:
            self.velocity[1] = 0
            
        # Apply friction to gradually slow down tiles
        self.velocity *= self.friction
        
        # Integrate velocity to update position (Euler integration)
        self.position += self.velocity * dt

    def resolve_ground_collision(self, ground_y):
        """Handle collision with the ground surface."""
        rect = self.get_rect()
        if rect.bottom > ground_y:
            overlap = rect.bottom - ground_y
            self.position[1] -= overlap
            self.velocity[1] *= -self.restitution
            # Stop small bounces
            if abs(self.velocity[1]) < 10:
                self.velocity[1] = 0
                self.is_static = True

    def resolve_tile_collision(self, other, ground_y=600):
        """
        Handle collision between this tile and another tile.
        
        Implements sophisticated collision physics:
        1. Pixel-perfect collision detection using masks
        2. Support detection with 3 points (center, left corner, right corner)
        3. Smart tumbling only when inadequately supported and not on ground
        4. Visual rotation feedback for unstable tiles
        5. Stability improvements for well-supported tiles
        
        Args:
            other: The other Tile object to check collision with
            ground_y: Y-coordinate of the ground level
        """
        global gravity_switch
        collision_states = [False, False, False]  # [center, left, right]
        
        # Quick bounding box check first for performance
        if not self.get_rect().colliderect(other.get_rect()):
            return
        
        # Pixel-perfect collision detection using pygame masks
        mask1 = self.get_mask()
        mask2 = other.get_mask()
        
        # Calculate offset for mask overlap check
        offset = (
            int(other.position[0] - other.tile_obj.size[0]//2 - (self.position[0] - self.tile_obj.size[0]//2)),
            int(other.position[1] - other.tile_obj.size[1]//2 - (self.position[1] - self.tile_obj.size[1]//2))
        )
        
        overlap = mask1.overlap(mask2, offset)
        if overlap:
            # Generate support detection points based on current tile position
            width, height = self.tile_obj.size
            tile_x = int(self.position[0] - width//2)
            tile_y = int(self.position[1] - height//2)
            
            # Three detection points at bottom edge of tile
            detection_points = [
                (tile_x + width//2, tile_y + height),  # Middle bottom [0]
                (tile_x, tile_y + height),             # Left bottom [1] 
                (tile_x + width, tile_y + height)      # Right bottom [2]
            ]
            
            collision_states = [False, False, False]
            
            # Check each detection point against the other tile's mask
            for i, point in enumerate(detection_points):
                # Convert world coordinates to other tile's local mask coordinates
                other_tile_x = int(other.position[0] - other.tile_obj.size[0]//2)
                other_tile_y = int(other.position[1] - other.tile_obj.size[1]//2)
                
                local_x = point[0] - other_tile_x
                local_y = point[1] - other_tile_y
                
                # Check bounds and collision
                if (0 <= local_x < other.tile_obj.size[0] and 
                    0 <= local_y < other.tile_obj.size[1]):
                    try:
                        if mask2.get_at((local_x, local_y)):
                            collision_states[i] = True
                    except IndexError:
                        pass
          # Only disable gravity if there's bottom support
        if any(collision_states):
            self.gravity_switch = False
        
        
        # Apply tumbling physics based on collision pattern
        # Only tumble if there's inadequate support (single corner contact only)
        # Don't tumble if:
        # - Center is supported (collision_states[0])
        # - Both corners are supported (collision_states[1] and collision_states[2])
        # - Center + one corner is supported
        
        supported_points = sum(collision_states)
        center_supported = collision_states[0]
        left_supported = collision_states[1]
        right_supported = collision_states[2]        # Only apply tumbling for unstable single-corner contacts
        if supported_points == 1 and not center_supported:
            # Check if this tile is on or very close to the ground
            tile_bottom = self.position[1] + self.tile_obj.size[1] // 2
            is_on_ground = tile_bottom >= ground_y - 15  # 15 pixel tolerance
            
            # Only tumble if NOT on the ground
            if not is_on_ground:
                if right_supported and not left_supported:
                    # Only right corner supported - tumble left
                    self.velocity[0] -= 2  # Reduced tumbling force
                    self.angular_velocity = 15
                    # Add visual rotation animation (right support = tilt left = -15°)
                    animation_manager.add_tile_rotation(self, -15)
                elif left_supported and not right_supported:
                    # Only left corner supported - tumble right
                    self.velocity[0] += 2  # Reduced tumbling force
                    self.angular_velocity = -15
                    # Add visual rotation animation (left support = tilt right = +15°)
                    animation_manager.add_tile_rotation(self, 15)        # Add additional tumbling when tiles have significant velocity and little support
        if abs(self.velocity[0]) > 50 and supported_points <= 1:
            # Check if on ground before tumbling
            tile_bottom = self.position[1] + self.tile_obj.size[1] // 2
            is_on_ground = tile_bottom >= ground_y - 15
            
            if not is_on_ground:
                # Fast-moving tile with little support - add dramatic rotation
                if self.velocity[0] > 0:
                    # Moving right - tilt right
                    animation_manager.add_tile_rotation(self, 30)
                else:
                    # Moving left - tilt left  
                    animation_manager.add_tile_rotation(self, -30)# If tile has good support (center or multiple points), stabilize it
        if center_supported or supported_points >= 2:
            # Reduce angular velocity to stabilize supported tiles
            self.angular_velocity *= 0.8
            # Reduce horizontal movement for stable tiles
            self.velocity[0] *= 0.9
            # Reset visual rotation for well-supported tiles
            if abs(self.visual_rotation) > 5:
                animation_manager.add_tile_rotation(self, 0)  # Return to upright
            # Reset visual rotation when tile becomes stable
            if hasattr(self, 'visual_rotation'):
                self.visual_rotation *= 0.9  # Gradually return to upright# Cap velocity and rotation to prevent extreme reactions
        max_velocity = 300  # Reduced max velocity for more stable physics
        self.velocity = np.clip(self.velocity, -max_velocity, max_velocity)
        self.angular_velocity = max(-3, min(3, self.angular_velocity))  # Reduced max angular velocity

    def check_support(self, all_tiles):
        """Check if this tile is supported by another tile or ground"""
        width, height = self.tile_obj.size
        tile_x = int(self.position[0] - width//2)
        tile_y = int(self.position[1] - height//2)
          # Use the same detection points as collision detection for consistency
        detection_points = [
            (tile_x + width//2, tile_y + height),  # Middle bottom [0]
            (tile_x, tile_y + height),             # Left bottom [1] 
            (tile_x + width, tile_y + height)      # Right bottom [2]
        ]
        
        support_count = 0
        
        # Check if any detection point is supported
        for point in detection_points:
            for other in all_tiles:
                if other == self:
                    continue
                  # Check if point is inside other tile using mask collision
                other_tile_x = int(other.position[0] - other.tile_obj.size[0]//2)
                other_tile_y = int(other.position[1] - other.tile_obj.size[1]//2)
                
                local_x = point[0] - other_tile_x
                local_y = point[1] - other_tile_y
                
                if (0 <= local_x < other.tile_obj.size[0] and 
                    0 <= local_y < other.tile_obj.size[1]):
                    try:
                        mask2 = other.get_mask()
                        if mask2.get_at((local_x, local_y)):
                            support_count += 1
                            break  # Found support for this point, move to next
                    except IndexError:
                        pass
        
        # Consider tile supported if it has at least one support point
        # For better stability, could require 2+ support points for large tiles
        return support_count > 0
    
    def reset_level(self):
        """Reset the level to initial state"""
        # Move all placed tiles back to selection area
        for tile in self.placed_tiles:
            tile.position = (0, self.selection_area_top + 50)  # Will be repositioned below
            tile.velocity = np.zeros(2, dtype=float)
            tile.is_static = False
            tile.gravity_switch = True
            # Reset visual rotation
            if hasattr(tile, 'visual_rotation'):
                tile.visual_rotation = 0.0
            self.selection_tiles.append(tile)
        
        self.placed_tiles.clear()
        self.dragged_tile = None
        
        # Reposition selection tiles
        x = 60
        for tile in self.selection_tiles:
            tile.position = (x, self.selection_area_top + 50)
            x += 70

class TilePlacer:
    """
    Main controller for tile placement and physics simulation.
    
    Core Responsibilities:
    1. Level Setup: Initialize tiles from level configuration
    2. User Interaction: Handle mouse drag-and-drop mechanics
    3. Physics Management: Run real-time simulation with collision detection
    4. Placement Validation: Prevent overlapping tiles using pixel-perfect detection
    5. Visual Feedback: Coordinate with animation system for user feedback
    
    Key Features:
    - Pixel-perfect collision detection for both placement and physics
    - Sophisticated support detection system (3-point bottom edge detection)
    - Visual rotation feedback separate from physics collision
    - Smart tumbling physics only when tiles are inadequately supported
    - Performance optimization through static tile detection
    
    Interaction Flow:
    1. User drags tile from selection area
    2. Real-time placement preview during drag
    3. Collision validation on release
    4. Physics simulation for placed tiles
    5. Support detection and gravity management
    6. Visual feedback through animations
    """
    def __init__(self, level_id, screen_height):
        self.level = LevelStorage.get_level_by_id(level_id)
        self.tile_counts = {}
        self.selection_tiles = []
        self.placed_tiles = []
        self.dragged_tile = None
        self.offset = (0, 0)
        self.selection_area_top = screen_height - 100

        # Prepare tiles from level definition
        x = 60
        for tile_type, tile_info in self.level["tiles"].items():
            # Use the key as the tile type; fallback to "rectangle" if blank
            ttype = tile_type if tile_type else "rectangle"
            count = tile_info.get("count", 1)
            self.tile_counts[ttype] = count
            for i in range(count):
                tile_obj = tile_types[ttype]()  # Create tile instance
                tile = Tile(tile_obj, (x, screen_height - 50))
                tile.tile_type = ttype
                self.selection_tiles.append(tile)
                x += 70

    def draw_selection_area(self, surface):
        for tile in self.selection_tiles:
            tile.draw(surface)

    def draw_placed_tiles(self, surface):
        for tile in self.placed_tiles:
            tile.draw(surface)

    def draw_dragged_tile(self, surface, mouse_pos):
        if self.dragged_tile:
            self.dragged_tile.position = mouse_pos
            self.dragged_tile.draw(surface)

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for tile in reversed(self.selection_tiles):
                if tile.get_rect().collidepoint(mouse_pos):
                    self.dragged_tile = tile
                    self.selection_tiles.remove(tile)
                    self.offset = (tile.position[0] - mouse_pos[0], tile.position[1] - mouse_pos[1])
                    break
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragged_tile:
                if mouse_pos[1] < self.selection_area_top:
                    # Check for overlap with already placed tiles
                    self.dragged_tile.position = mouse_pos
                    overlap = False
                    for placed in self.placed_tiles:
                        # Use pixel-perfect collision for accuracy
                        offset = (
                            int(placed.position[0] - placed.tile_obj.size[0] // 2 - (self.dragged_tile.position[0] - self.dragged_tile.tile_obj.size[0] // 2)),
                            int(placed.position[1] - placed.tile_obj.size[1] // 2 - (self.dragged_tile.position[1] - self.dragged_tile.tile_obj.size[1] // 2))
                        )
                        mask1 = self.dragged_tile.get_mask()
                        mask2 = placed.get_mask()
                        if mask1.overlap(mask2, offset):
                            overlap = True
                            break
                    if not overlap:
                        self.placed_tiles.append(self.dragged_tile)
                        # Add placement feedback animation
                        animation_manager.add_tile_placement_feedback(self.dragged_tile.position)
                    else:
                        # Move back to selection area
                        self.dragged_tile.position = (self.dragged_tile.position[0], self.selection_area_top + 50)
                        self.selection_tiles.append(self.dragged_tile)
                else:
                    self.dragged_tile.position = (self.dragged_tile.position[0], self.selection_area_top + 50)
                    self.selection_tiles.append(self.dragged_tile)
                self.dragged_tile = None
        elif event.type == pygame.KEYDOWN:
            # Rotation controls removed - tiles can no longer be rotated
            pass

    def simulate(self, dt, ground_y):
        """
        Run physics simulation for all placed tiles.
        
        Simulation Pipeline:
        1. Support Detection: Check if each tile is adequately supported
        2. Gravity Management: Re-enable gravity for unsupported tiles above ground
        3. Physics Integration: Apply forces, velocity, and position updates
        4. Collision Resolution: Handle ground and tile-to-tile collisions
        5. Stability Analysis: Detect and respond to unstable configurations
        
        Performance Optimizations:
        - Static tile detection to skip physics for settled tiles
        - Early exit for stable configurations
        - Efficient O(n²) collision detection with spatial optimizations
        
        Args:
            dt: Delta time for physics integration (seconds)
            ground_y: Y-coordinate of ground level for collision detection
        """
        # Phase 1: Support detection and gravity management
        for tile in self.placed_tiles:
            # Re-evaluate support for non-static tiles
            if not tile.is_static and not tile.check_support(self.placed_tiles):
                # Check if tile is above ground before enabling gravity
                if tile.get_rect().bottom < ground_y - 5:  # 5 pixel tolerance
                    tile.gravity_switch = True
            
            # Apply physics simulation (gravity, friction, integration)
            tile.apply_physics(dt)
            
            # Handle ground collision with bounce and damping
            tile.resolve_ground_collision(ground_y)
        
        # Phase 2: Tile-to-tile collision detection and response
        # Note: O(n²) algorithm - could be optimized with spatial partitioning for large numbers of tiles
        for i, tile in enumerate(self.placed_tiles):
            for j, other in enumerate(self.placed_tiles):
                if i != j:
                    tile.resolve_tile_collision(other, ground_y)

    def get_tower_height(self, ground_y):
        """Calculate the highest point of the tower above ground"""
        if not self.placed_tiles:
            return 0
        
        min_y = ground_y  # Start from ground level
        for tile in self.placed_tiles:
            tile_top = tile.position[1] - tile.tile_obj.size[1] // 2
            if tile_top < min_y:
                min_y = tile_top
        
        # Return height above ground (ground_y - min_y)
        return max(0, ground_y - min_y)
