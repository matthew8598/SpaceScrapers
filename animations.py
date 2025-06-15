"""
Visual Effects and Animation System
==================================

This module provides a comprehensive animation system for SpaceScrapers including:

1. Particle Systems:
   - Explosion effects for meteorite impacts
   - Dust clouds for wrecking ball collisions
   - Wind particles for atmospheric effects
   - Tile placement feedback sparkles

2. Tile Animations:
   - Visual rotation effects (separate from physics collision)
   - Smooth tumbling animations when tiles become unstable
   - Stability feedback through visual cues
   - Support indication through rotation changes

3. Effect Management:
   - Centralized animation manager for all effects
   - Performance optimization through particle pooling
   - Time-based animation updates with proper delta timing
   - Alpha blending and fade effects

Key Design Principles:
- Visual effects are separated from physics simulation
- Animations provide feedback without affecting gameplay mechanics
- Smooth interpolation for professional-looking effects
- Configurable intensity and duration for different effect types

The animation system enhances user experience by providing clear visual
feedback for all game interactions while maintaining clean separation
between cosmetic effects and core game logic.
"""

import pygame
import math
import time
import random
import numpy as np

class Particle:
    """
    Individual particle for visual effects.
    
    Features:
    - Position and velocity-based movement
    - Gravity simulation for realistic trajectories
    - Life-based alpha blending for fade effects
    - Configurable size, color, and physics properties
    - Smooth interpolation for natural-looking motion
    
    Used for:
    - Explosion debris and sparks
    - Dust clouds from impacts
    - Wind effect particles
    - Tile placement feedback
    """
    def __init__(self, x, y, vx, vy, color, size=3, life=1.0, gravity=200):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
        self.gravity = gravity
        self.start_time = time.time()
    
    def update(self, dt):
        """Update particle position and life"""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt  # Apply gravity
        self.life -= dt
        
        return self.life > 0
    
    def draw(self, surface):
        """Draw particle with alpha based on remaining life"""
        if self.life <= 0:
            return
            
        alpha = max(0, min(255, int((self.life / self.max_life) * 255)))
        color = (*self.color[:3], alpha)
        
        # Create a surface with per-pixel alpha
        particle_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf, color, (self.size, self.size), self.size)
        surface.blit(particle_surf, (int(self.x - self.size), int(self.y - self.size)))

class TileRotationAnimation:
    """
    Smooth visual rotation animation for tiles - COSMETIC ONLY, does not affect physics.
    
    Key Features:
    - Visual feedback separate from collision detection
    - Smooth interpolation between rotation states
    - Capped rotation angles (±45°) for readability
    - Automatic return to upright position when stable
    - Integration with physics system for tumbling feedback
    
    Important: This rotation is purely visual - physics collision detection
    always uses the original upright tile orientation for consistency and
    predictability in gameplay.
    """
    def __init__(self, tile, target_angle_offset, duration=0.8):
        self.tile = tile
        self.start_visual_angle = getattr(tile, 'visual_rotation', 0)
        # Cap the rotation offset to ±45 degrees for visual feedback
        capped_offset = max(-45, min(45, target_angle_offset))
        self.target_visual_angle = capped_offset
        self.duration = duration
        self.start_time = time.time()
        self.active = True
    
    def update(self, dt):
        """Update visual rotation animation - does NOT affect physics collision"""
        if not self.active:
            return False
            
        elapsed = time.time() - self.start_time
        progress = min(1.0, elapsed / self.duration)
        
        # Smooth easing function (ease-out)
        eased_progress = 1 - (1 - progress) ** 3
        
        # Calculate current visual angle (separate from physics angle)
        angle_diff = self.target_visual_angle - self.start_visual_angle
        current_visual_angle = self.start_visual_angle + (angle_diff * eased_progress)
        
        # Store visual rotation separately from physics rotation
        self.tile.visual_rotation = current_visual_angle
        
        if progress >= 1.0:
            self.tile.visual_rotation = self.target_visual_angle
            self.active = False
            
        return self.active

class TilePlacementAnimation:
    """Animation feedback when placing tiles"""
    def __init__(self, position, color=(100, 255, 100), duration=0.5):
        self.position = position
        self.color = color
        self.duration = duration
        self.start_time = time.time()
        self.active = True
        self.max_radius = 30
    
    def update(self, dt):
        """Update placement animation"""
        if not self.active:
            return False
            
        elapsed = time.time() - self.start_time
        progress = min(1.0, elapsed / self.duration)
        
        if progress >= 1.0:
            self.active = False
            
        return self.active
    
    def draw(self, surface):
        """Draw placement feedback circle"""
        if not self.active:
            return
            
        elapsed = time.time() - self.start_time
        progress = min(1.0, elapsed / self.duration)
        
        # Expanding circle that fades out
        radius = int(self.max_radius * progress)
        alpha = max(0, int(255 * (1 - progress)))
        
        if alpha > 0 and radius > 0:
            # Create surface with alpha for the circle
            circle_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            color_with_alpha = (*self.color[:3], alpha)
            pygame.draw.circle(circle_surf, color_with_alpha, (radius, radius), radius, 3)
            surface.blit(circle_surf, (self.position[0] - radius, self.position[1] - radius))

class PulsingTargetLine:
    """Pulsing animation for the target height line"""
    def __init__(self, screen_width, target_y, color=(255, 255, 100)):
        self.screen_width = screen_width
        self.target_y = target_y
        self.color = color
        self.pulse_speed = 3.0  # Pulses per second
        self.min_alpha = 100
        self.max_alpha = 255
    
    def draw(self, surface):
        """Draw pulsing target line"""
        # Calculate pulsing alpha
        time_factor = time.time() * self.pulse_speed
        alpha_range = self.max_alpha - self.min_alpha
        alpha = self.min_alpha + (math.sin(time_factor) * 0.5 + 0.5) * alpha_range
        alpha = int(alpha)
        
        # Draw main line
        color_with_alpha = (*self.color[:3], alpha)
        line_surf = pygame.Surface((self.screen_width, 4), pygame.SRCALPHA)
        line_surf.fill(color_with_alpha)
        surface.blit(line_surf, (0, self.target_y - 2))
        
        # Draw dashed border for better visibility
        dash_length = 20
        gap_length = 10
        total_length = dash_length + gap_length
        
        for x in range(0, self.screen_width, total_length):
            dash_surf = pygame.Surface((min(dash_length, self.screen_width - x), 2), pygame.SRCALPHA)
            border_alpha = min(255, alpha + 50)
            border_color = (255, 255, 255, border_alpha)
            dash_surf.fill(border_color)
            surface.blit(dash_surf, (x, self.target_y - 1))

class AnimationManager:
    """Central manager for all animations and effects"""
    def __init__(self):
        self.particles = []
        self.tile_rotations = []
        self.placement_animations = []
        self.pulsing_target = None
    
    def add_particle_explosion(self, position, color=(255, 255, 100), count=15, force=150):
        """Add explosion effect when challenges hit tiles"""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, force)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(50, 100)  # Upward bias
            
            particle_color = (
                random.randint(max(0, color[0] - 50), min(255, color[0] + 50)),
                random.randint(max(0, color[1] - 50), min(255, color[1] + 50)),
                random.randint(max(0, color[2] - 50), min(255, color[2] + 50))
            )
            
            particle = Particle(
                position[0], position[1],
                vx, vy,
                particle_color,
                size=random.randint(2, 5),
                life=random.uniform(0.8, 1.5)
            )
            self.particles.append(particle)
    
    def add_meteorite_explosion(self, position):
        """Specific effect for meteorite impacts"""
        self.add_particle_explosion(position, color=(255, 150, 50), count=20, force=200)
        # Add additional sparks for more dramatic effect
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(100, 300)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(0, 50)
            
            spark = Particle(
                position[0], position[1],
                vx, vy,
                (255, 255, 200),  # Bright yellow sparks
                size=1,
                life=random.uniform(0.3, 0.8),
                gravity=100  # Light gravity for sparks
            )
            self.particles.append(spark)
    
    def add_wrecking_ball_impact(self, position):
        """Specific effect for wrecking ball impacts"""
        self.add_particle_explosion(position, color=(200, 200, 200), count=25, force=250)
    
    def add_wind_particles(self, position, wind_direction):
        """Add particles for wind effect"""
        for _ in range(5):
            vx = wind_direction * random.uniform(100, 200)
            vy = random.uniform(-20, 20)
            
            particle = Particle(
                position[0], position[1],
                vx, vy,
                (200, 200, 255),
                size=2,
                life=random.uniform(0.5, 1.0),
                gravity=0  # Wind particles don't fall
            )
            self.particles.append(particle)
    
    def add_tile_rotation(self, tile, angle_offset):
        """Add smooth VISUAL rotation animation for tumbling tiles (capped at ±45°)"""
        # Remove any existing rotation for this tile
        self.tile_rotations = [anim for anim in self.tile_rotations if anim.tile != tile]
        
        # Add new visual rotation animation with capped angle
        rotation_anim = TileRotationAnimation(tile, angle_offset)
        self.tile_rotations.append(rotation_anim)
    
    def add_tile_placement_feedback(self, position):
        """Add visual feedback when placing a tile"""
        placement_anim = TilePlacementAnimation(position)
        self.placement_animations.append(placement_anim)
    
    def set_pulsing_target_line(self, screen_width, target_y):
        """Set up the pulsing target line"""
        self.pulsing_target = PulsingTargetLine(screen_width, target_y)
    
    def update(self, dt):
        """Update all animations"""
        # Update particles
        self.particles = [p for p in self.particles if p.update(dt)]
        
        # Update tile rotations
        self.tile_rotations = [anim for anim in self.tile_rotations if anim.update(dt)]
        
        # Update placement animations
        self.placement_animations = [anim for anim in self.placement_animations if anim.update(dt)]
    
    def draw(self, surface):
        """Draw all visual effects"""
        # Draw particles
        for particle in self.particles:
            particle.draw(surface)
        
        # Draw placement animations
        for anim in self.placement_animations:
            anim.draw(surface)
        
        # Draw pulsing target line
        if self.pulsing_target:
            self.pulsing_target.draw(surface)
    
    def clear_all(self):
        """Clear all animations (useful for level restart)"""
        self.particles.clear()
        self.tile_rotations.clear()
        self.placement_animations.clear()
        self.pulsing_target = None

# Global animation manager instance
animation_manager = AnimationManager()
