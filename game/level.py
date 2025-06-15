"""
Level Management System
======================

Handles individual level setup and rendering including:
- Background image/color management
- Ground rendering and physics boundaries  
- UI layout for tile selection area
- Visual scaling and positioning

Each level represents a different space environment with unique:
- Background imagery (Earth, Mars, Jupiter)
- Color schemes and atmospheric effects
- Ground textures and properties
- Environmental challenges and objectives

The level system provides the visual foundation that the physics
and gameplay systems build upon.
"""

import pygame

class Level:
    """
    Individual level configuration and rendering.
    
    Manages:
    - Background imagery and scaling for different space environments
    - Ground rendering with appropriate textures and colors
    - UI layout including tile selection area
    - Visual boundaries for physics simulation
    
    Each level provides a unique visual environment that affects
    both the aesthetic experience and gameplay challenge level.
    """
    def __init__(self, level_data, screen_size):
        self.name = level_data.get("name", "Unnamed Level")
        self.screen_width, self.screen_height = screen_size
        
        # Load background image or use color fallback
        background_value = level_data.get("background_image", (20, 20, 40))
        if isinstance(background_value, str):
            # It's a file path, load the image
            try:
                self.background_image = pygame.image.load(background_value)
                # Scale to fit screen
                self.background_image = pygame.transform.scale(self.background_image, screen_size)
                self.background_color = None
            except pygame.error:
                # Fallback to color if image loading fails
                self.background_image = None
                self.background_color = (20, 20, 40)
        else:
            # It's a color tuple
            self.background_image = None
            self.background_color = background_value
            
        self.ground_color = level_data.get("ground_image", (80, 60, 40))
        self.ground_height = 100  # Fixed height for ground

        # In the future, load sprites, tiles, etc. here

    def draw(self, screen):
        # Draw background
        if self.background_image:
            screen.blit(self.background_image, (0, 0))
        else:
            screen.fill(self.background_color)
            
        # Draw ground
        ground_rect = pygame.Rect(
            0,
            self.screen_height - self.ground_height,
            self.screen_width,
            self.ground_height
        )
        pygame.draw.rect(screen, self.ground_color, ground_rect)
        
        # Draw tile selection UI
        tile_selection_rect = pygame.Rect(
            0, self.screen_height - 100, self.screen_width, 100
        )
        # Make selection area semi-transparent so background shows through
        selection_surface = pygame.Surface((self.screen_width, 100))
        selection_surface.set_alpha(180)  # Semi-transparent
        selection_surface.fill((100, 100, 100))
        screen.blit(selection_surface, (0, self.screen_height - 100))

    def draw_target_line(self, screen, target_height):
        """Draw the target height line"""
        target_y = self.screen_height - self.ground_height - target_height
        if target_y > 0:  # Only draw if target line is visible
            pygame.draw.line(screen, (255, 255, 0), (0, target_y), (self.screen_width, target_y), 3)
            # Add some visual indicators
            for x in range(0, self.screen_width, 100):
                pygame.draw.circle(screen, (255, 255, 0), (x, target_y), 5)
            
            # Label
            font = pygame.font.SysFont('Arial', 20)
            text = font.render(f"TARGET: {target_height}px", True, (255, 255, 0))
            screen.blit(text, (self.screen_width - 150, target_y - 25))