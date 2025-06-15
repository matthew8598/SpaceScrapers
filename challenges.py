"""
Environmental Challenge System
=============================

This module implements various environmental challenges that test tower stability:

1. WreckingBall: Heavy pendulum that sweeps across the screen, applying impact forces
2. Meteorite: Falling projectiles with explosive impacts and debris effects
3. Wind: Horizontal forces that push tiles and test structural integrity

Each challenge has:
- Configurable timing and intensity
- Realistic physics interactions with tiles
- Visual effects (particles, debris, impact animations)
- Sound integration capabilities

The challenge system is designed to be extensible - new environmental
hazards can be easily added by implementing the base challenge interface.

Key Features:
- Physics-based impact calculations using mass and velocity
- Particle systems for visual feedback
- Gradual force application for realistic interactions
- Collision detection with placed tiles
- Animation integration for enhanced user experience
"""

import pygame
import math
import time
import numpy as np

# Import animation manager for particle effects
try:
    from animations import animation_manager
except ImportError:
    # Fallback if animations not available
    class FallbackAnimationManager:
        def add_wrecking_ball_impact(self, pos): pass
        def add_meteorite_explosion(self, pos): pass
        def add_wind_particles(self, pos, direction): pass
    animation_manager = FallbackAnimationManager()

class WreckingBall:
    """
    Heavy pendulum challenge that sweeps across the screen.
    
    Features:
    - Realistic pendulum physics with angular momentum
    - Variable swing timing and intensity
    - Impact force calculation based on mass and velocity
    - Visual chain rendering connecting to anchor point
    - Particle effects on tile collisions
    - Gradual force application for realistic interactions
    
    The wrecking ball is designed to test tower stability by applying
    horizontal forces at various heights as it swings across the build area.
    """
    
    def __init__(self, screen_width, screen_height, trigger_time=2.0):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.trigger_time = trigger_time  # Time to wait before starting
        self.started = False
        self.active = False
        self.finished = False
        
        # Ball properties
        self.radius = 40
        self.color = (80, 80, 80)  # Dark gray
        self.chain_color = (60, 60, 60)  # Darker gray for chain
          # Physics properties
        self.mass = 500  # Heavy ball
        self.chain_length = 450  # Longer chain to reach further
          # Starting position (positioned to sweep across the center)
        self.anchor_x = screen_width * 0.5  # Position anchor closer to right edge
        self.anchor_y = 150  # High up
        
        # Current position (start swinging from the right)
        self.angle = math.pi * 0.5  # Start at 90 degrees (horizontal right)
        self.x = self.anchor_x + self.chain_length * math.sin(self.angle)
        self.y = self.anchor_y + self.chain_length * math.cos(self.angle)
        
        # Movement
        self.swing_speed = 3.0  # Faster swing speed
        self.angular_velocity = 0
          # Animation state
        self.sweep_direction = -1  # -1 for left, 1 for right
        self.max_swing_angle = math.pi * 0.7  # Maximum swing angle
        
    def update(self, dt, simulation_time):
        """Update the wrecking ball position"""
        if not self.started and simulation_time >= self.trigger_time:
            self.started = True
            self.active = True
            # Start with strong leftward velocity
            self.angular_velocity = -self.swing_speed * 1.5
            
        if self.active and not self.finished:
            # Simple pendulum physics
            gravity = 800
            angular_acceleration = -(gravity / self.chain_length) * math.sin(self.angle)
            self.angular_velocity += angular_acceleration * dt
            self.angle += self.angular_velocity * dt
            
            # Add some damping to make it more controllable
            self.angular_velocity *= 0.998
            
            # Calculate ball position
            self.x = self.anchor_x + self.chain_length * math.sin(self.angle)
            self.y = self.anchor_y + self.chain_length * math.cos(self.angle)
              # Check if ball has swung past the screen
            if self.x < -50:  # Off-screen left (reduced to allow more sweep)
                self.finished = True
                self.active = False
    
    def draw(self, surface):
        """Draw the wrecking ball and chain"""
        if not self.started:
            return
            
        # Draw chain
        chain_segments = 10
        for i in range(chain_segments):
            t = i / chain_segments
            chain_x = self.anchor_x + (self.x - self.anchor_x) * t
            chain_y = self.anchor_y + (self.y - self.anchor_y) * t
            pygame.draw.circle(surface, self.chain_color, (int(chain_x), int(chain_y)), 3)
        
        # Draw anchor point
        pygame.draw.circle(surface, (100, 100, 100), (int(self.anchor_x), int(self.anchor_y)), 8)
        
        # Draw ball
        if self.active:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            # Add some shine effect
            highlight_x = int(self.x - self.radius * 0.3)
            highlight_y = int(self.y - self.radius * 0.3)
            pygame.draw.circle(surface, (120, 120, 120), (highlight_x, highlight_y), self.radius // 3)    
    def get_collision_rect(self):
        """Get the collision rectangle for the ball"""
        if not self.active:
            return None
        return pygame.Rect(
            int(self.x - self.radius), 
            int(self.y - self.radius),
            self.radius * 2, 
            self.radius * 2
        )
    
    def check_collision_with_tile(self, tile):
        """Check if the wrecking ball collides with a tile"""
        if not self.active:
            return False
            
        ball_rect = self.get_collision_rect()
        if ball_rect and ball_rect.colliderect(tile.get_rect()):
            # More precise circular collision
            dx = self.x - tile.position[0]
            dy = self.y - tile.position[1]
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Get approximate tile radius (assume square for simplicity)
            tile_radius = max(tile.tile_obj.size) / 2
            
            if distance < (self.radius + tile_radius * 0.8):  # 0.8 factor for better feel
                # Add particle effect at collision point
                collision_x = tile.position[0] + dx * 0.5
                collision_y = tile.position[1] + dy * 0.5
                animation_manager.add_wrecking_ball_impact((collision_x, collision_y))
                  # Apply knockback force to the tile
                if distance > 0:
                    force_magnitude = 300  # Knockback strength
                    force_x = (dx / distance) * force_magnitude
                    force_y = (dy / distance) * force_magnitude
                    
                    tile.velocity[0] += force_x
                    tile.velocity[1] += force_y
                    tile.angular_velocity += (force_x + force_y) * 0.01  # Add some spin
                    
                    # Add dramatic visual rotation based on impact direction
                    if force_x > 0:
                        # Hit from left, rotate right
                        animation_manager.add_tile_rotation(tile, 25)
                    else:
                        # Hit from right, rotate left
                        animation_manager.add_tile_rotation(tile, -25)
                    tile.gravity_switch = True  # Make sure gravity is enabled
                
                return True
        return False


class Wind:
    """A wind challenge that applies horizontal forces to tiles based on their properties"""
    
    def __init__(self, screen_width, screen_height, trigger_time=1.0, duration=4.0):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.trigger_time = trigger_time
        self.duration = duration
        self.started = False
        self.active = False
        self.finished = False
        self.time_active = 0
          # Wind properties
        self.base_wind_force = 25  # Reduced base wind force
        self.wind_direction = 1  # 1 for right, -1 for left
        self.wind_variance = 0.2  # Reduced wind variance
        self.current_wind_strength = 0
        
        # Visual effects
        self.particles = []
        self.particle_spawn_timer = 0
        
    def update(self, dt, simulation_time):
        """Update the wind challenge"""
        if not self.started and simulation_time >= self.trigger_time:
            self.started = True
            self.active = True
            self.time_active = 0
            
        if self.active and not self.finished:
            self.time_active += dt
            
            # Calculate wind strength with some variation
            wind_phase = math.sin(self.time_active * 2) * self.wind_variance
            self.current_wind_strength = self.base_wind_force * (1 + wind_phase)
            
            # Update particles for visual effect
            self._update_particles(dt)
            
            # Check if duration is over
            if self.time_active >= self.duration:
                self.finished = True
                self.active = False
    
    def _update_particles(self, dt):
        """Update wind particles for visual effect"""
        # Spawn new particles
        self.particle_spawn_timer += dt
        if self.particle_spawn_timer >= 0.05:  # Spawn every 50ms
            self.particle_spawn_timer = 0
            # Spawn particles from the left side of screen
            for _ in range(3):
                particle = {
                    'x': -10,
                    'y': np.random.randint(50, self.screen_height - 150),
                    'speed': np.random.uniform(200, 400),
                    'life': 1.0,
                    'size': np.random.uniform(2, 5)
                }
                self.particles.append(particle)
        
        # Update existing particles
        for particle in self.particles[:]:
            particle['x'] += particle['speed'] * dt * self.wind_direction
            particle['life'] -= dt
            if particle['life'] <= 0 or particle['x'] > self.screen_width + 10:
                self.particles.remove(particle)
    
    def draw(self, surface):
        """Draw wind effects"""
        if not self.active:
            return
            
        # Draw particles
        for particle in self.particles:
            alpha = int(particle['life'] * 100)
            color = (200, 200, 255, alpha)
            # Create a surface for the particle with alpha
            particle_surf = pygame.Surface((int(particle['size']), int(particle['size'])), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, color, (int(particle['size']/2), int(particle['size']/2)), int(particle['size']/2))
            surface.blit(particle_surf, (int(particle['x']), int(particle['y'])))
        
        # Draw wind strength indicator
        wind_bar_width = 200
        wind_bar_height = 20
        wind_bar_x = self.screen_width - wind_bar_width - 20
        wind_bar_y = 50
        
        # Background bar
        pygame.draw.rect(surface, (50, 50, 50), (wind_bar_x, wind_bar_y, wind_bar_width, wind_bar_height))
        
        # Wind strength bar
        strength_ratio = abs(self.current_wind_strength) / (self.base_wind_force * 1.5)
        strength_width = int(wind_bar_width * strength_ratio)
        color = (100 + int(150 * strength_ratio), 100, 255 - int(100 * strength_ratio))
        pygame.draw.rect(surface, color, (wind_bar_x, wind_bar_y, strength_width, wind_bar_height))
          # Label
        font = pygame.font.SysFont('Arial', 16)
        text = font.render("WIND FORCE", True, (255, 255, 255))
        surface.blit(text, (wind_bar_x, wind_bar_y - 25))
    
    def apply_wind_to_tiles(self, tiles):
        """Apply wind forces to all tiles based on their properties"""
        if not self.active:
            return
            
        for tile in tiles:
            wind_force = self._calculate_wind_force(tile, tiles)
            if wind_force != 0:
                # Add wind particle effects around affected tiles
                if abs(wind_force) > 5:  # Only add particles for significant wind force
                    animation_manager.add_wind_particles(
                        (tile.position[0], tile.position[1]), 
                        self.wind_direction
                    )
                
                # Apply horizontal force
                tile.velocity[0] += wind_force
                # Add some turbulence (small random vertical force)
                turbulence = np.random.uniform(-5, 5)  # Reduced turbulence
                tile.velocity[1] += turbulence
    
    def _calculate_wind_force(self, target_tile, all_tiles):
        """Calculate wind force on a specific tile based on exposure and properties"""        # Base force calculation
        base_force = self.current_wind_strength * self.wind_direction
        
        # Factor in tile mass (heavier tiles resist wind more)
        mass_factor = 1.0 / (1.0 + target_tile.mass * 0.5)  # More gradual mass resistance
        
        # Calculate exposure factor (how much the tile is exposed to wind)
        exposure_factor = self._calculate_exposure(target_tile, all_tiles)
        
        # Factor in contact with ground and other tiles (more contacts = more resistance)
        contact_factor = self._calculate_contact_resistance(target_tile, all_tiles)
        
        # Calculate tile's cross-sectional area facing the wind
        area_factor = self._calculate_wind_area(target_tile)
        
        # Final force calculation
        wind_force = base_force * mass_factor * exposure_factor * contact_factor * area_factor
        
        return wind_force
    
    def _calculate_exposure(self, target_tile, all_tiles):
        """Calculate how exposed a tile is to wind (0.0 to 1.0)"""
        # Check if there are tiles blocking the wind path
        target_rect = target_tile.get_rect()
        target_x = target_rect.centerx
        target_y = target_rect.centery
        
        blocking_factor = 1.0
        
        # Check for tiles that might block wind (in front of target tile)
        for other_tile in all_tiles:
            if other_tile == target_tile:
                continue
                
            other_rect = other_tile.get_rect()
            other_x = other_rect.centerx
            other_y = other_rect.centery
              # Check if other tile is in wind path (upwind from target)
            if self.wind_direction > 0:  # Wind blowing right
                is_upwind = other_x < target_x
            else:  # Wind blowing left
                is_upwind = other_x > target_x
            
            if is_upwind:
                # Calculate if other tile blocks wind
                horizontal_distance = abs(other_x - target_x)
                vertical_distance = abs(other_y - target_y)
                  # Tiles close horizontally and vertically provide wind blocking
                if horizontal_distance < 150 and vertical_distance < 100:
                    block_strength = max(0, 1 - (horizontal_distance / 150) - (vertical_distance / 100))
                    blocking_factor *= (1 - block_strength * 0.7)  # Up to 70% blocking
        
        return max(0.1, blocking_factor)  # Minimum 10% exposure
    
    def _calculate_contact_resistance(self, target_tile, all_tiles):
        """Calculate resistance based on contacts with ground and other tiles"""
        target_rect = target_tile.get_rect()
        ground_y = self.screen_height - 100  # Assuming ground height
        
        resistance_factor = 1.0
        
        # Check if tile is on the ground (strong resistance)
        if target_rect.bottom >= ground_y - 5:  # Close to or touching ground
            resistance_factor *= 0.1  # Very strong resistance from ground contact
        
        # Use the tile's collision detection system to get accurate contact info
        contact_count = 0
        stable_contacts = 0
        
        # Check contacts with other tiles using the same detection system as tile physics
        width, height = target_tile.tile_obj.size
        tile_x = int(target_tile.position[0] - width//2)
        tile_y = int(target_tile.position[1] - height//2)
        
        # Detection points at bottom of current tile (same as in tile_placement.py)
        detection_points = [
            (tile_x + width//2, tile_y + height),  # Middle bottom [0]
            (tile_x, tile_y + height),             # Left bottom [1] 
            (tile_x + width, tile_y + height)      # Right bottom [2]
        ]
        
        collision_states = [False, False, False]
        
        # Check each detection point against other tiles
        for other_tile in all_tiles:
            if other_tile == target_tile:
                continue
                
            for i, point in enumerate(detection_points):
                # Convert world coordinates to other tile's local mask coordinates
                other_tile_x = int(other_tile.position[0] - other_tile.tile_obj.size[0]//2)
                other_tile_y = int(other_tile.position[1] - other_tile.tile_obj.size[1]//2)
                
                local_x = point[0] - other_tile_x
                local_y = point[1] - other_tile_y
                
                if (0 <= local_x < other_tile.tile_obj.size[0] and 
                    0 <= local_y < other_tile.tile_obj.size[1]):
                    try:
                        mask2 = other_tile.get_mask()
                        if mask2.get_at((local_x, local_y)):
                            collision_states[i] = True
                    except IndexError:
                        pass
        
        # Calculate resistance based on contact pattern (same logic as tile physics)
        supported_points = sum(collision_states)
        center_supported = collision_states[0]  # Middle bottom
        left_supported = collision_states[1]    # Left bottom
        right_supported = collision_states[2]   # Right bottom
        
        # Stable tiles get much more resistance to wind
        if center_supported or supported_points >= 2:
            # Well-supported tiles are very resistant to wind
            resistance_factor *= 0.15  # 85% resistance
        elif supported_points == 1:
            # Single contact point (unstable) - moderate resistance
            resistance_factor *= 0.6   # 40% resistance        # If no contacts with other tiles, resistance_factor stays at 1.0
        
        return resistance_factor

    def _calculate_wind_area(self, tile):
        """Calculate the effective area of tile facing the wind"""
        # Get tile dimensions - no rotation, so use width directly
        width, height = tile.tile_obj.size
        
        # Normalize area factor (larger tiles catch more wind)
        base_area = 96 * 96  # Reference area (standard tile size)
        tile_area = width * height
        area_factor = math.sqrt(tile_area / base_area)
        
        return min(2.0, area_factor)  # Cap at 2x multiplier


class Meteorite:
    """A single meteorite that falls from the sky"""
    
    def __init__(self, x, y, velocity_x, velocity_y, size, mass):
        self.x = x
        self.y = y
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.size = size
        self.mass = mass
        self.radius = size // 2
        self.active = True
        self.hit_tiles = set()  # Track which tiles this meteorite has already hit
        
        # Visual properties
        self.color = (150, 75, 0)  # Brown/orange color
        self.trail_points = []  # For drawing trail effect
        self.max_trail_length = 8
        
    def update(self, dt):
        """Update meteorite position and physics"""
        if not self.active:
            return
            
        # Apply gravity to meteorite (faster fall)
        self.velocity_y += 800 * dt
        
        # Update position
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        
        # Add current position to trail
        self.trail_points.append((self.x, self.y))
        if len(self.trail_points) > self.max_trail_length:
            self.trail_points.pop(0)
        
        # Deactivate if off screen
        if self.y > 1000 or self.x < -100 or self.x > 1200:
            self.active = False
    
    def draw(self, surface):
        """Draw the meteorite with trail effect"""
        if not self.active:
            return
            
        # Draw trail
        for i, point in enumerate(self.trail_points):
            alpha = int(255 * (i + 1) / len(self.trail_points) * 0.5)
            trail_size = max(1, int(self.radius * (i + 1) / len(self.trail_points) * 0.7))
            trail_color = (150 + alpha//3, 75 + alpha//4, alpha//8)
            pygame.draw.circle(surface, trail_color, (int(point[0]), int(point[1])), trail_size)
        
        # Draw main meteorite
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        # Add bright center
        pygame.draw.circle(surface, (255, 150, 50), (int(self.x), int(self.y)), max(1, self.radius//2))
    
    def get_collision_rect(self):
        """Get collision rectangle for the meteorite"""
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2
        )
    
    def check_collision_with_tile(self, tile):
        """Check collision with a tile and apply impact forces"""
        if not self.active or tile in self.hit_tiles:
            return False
            
        meteorite_rect = self.get_collision_rect()
        tile_rect = tile.get_rect()
        
        if meteorite_rect.colliderect(tile_rect):
            # Calculate impact force based on meteorite mass and velocity
            impact_velocity = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
            impact_force = self.mass * impact_velocity * 0.7  # Scale factor for game balance
            
            # Calculate direction from meteorite to tile center
            dx = tile.position[0] - self.x
            dy = tile.position[1] - self.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > 0:
                # Normalize direction
                dx /= distance
                dy /= distance
                
                # Apply impact to tile based on tile's mass (heavier tiles resist more)
                mass_factor = 1.0 / (1.0 + tile.mass * 0.5)
                
                # Apply velocity to tile
                tile.velocity[0] += dx * impact_force * mass_factor
                tile.velocity[1] += dy * impact_force * mass_factor
                  # Add some rotational impact based on hit position
                # Calculate where on the tile the meteorite hit
                tile_center_x = tile.position[0]
                hit_offset = self.x - tile_center_x
                angular_impact = hit_offset * impact_force * mass_factor * 0.01
                tile.angular_velocity += angular_impact
                
                # Add visual rotation based on meteorite impact direction
                if hit_offset > 0:
                    # Hit right side, rotate right
                    animation_manager.add_tile_rotation(tile, 20)
                else:
                    # Hit left side, rotate left
                    animation_manager.add_tile_rotation(tile, -20)
                  # Apply friction to the impact (resistance)
                friction_factor = tile.friction if hasattr(tile, 'friction') else 0.98
                tile.velocity *= friction_factor
                
                # Add meteorite explosion particle effect
                animation_manager.add_meteorite_explosion((self.x, self.y))
                
                # Mark this tile as hit and deactivate meteorite
                self.hit_tiles.add(tile)
                self.active = False
                return True
                
        return False


class MeteoriteShower:
    """A challenge that spawns multiple meteorites falling from the sky"""
    
    def __init__(self, screen_width, screen_height, trigger_time=1.5, duration=5.0):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.trigger_time = trigger_time
        self.duration = duration
        self.started = False
        self.active = False
        self.finished = False
        self.time_active = 0
        
        # Meteorite properties
        self.meteorites = []
        self.spawn_timer = 0
        self.spawn_interval = 0.1  # Spawn a meteorite every 0.1 seconds
        self.total_meteorites_spawned = 0
        self.max_meteorites = 45  # Maximum number of meteorites to spawn
        
        # Shower properties
        self.meteorite_sizes = [24, 30, 36, 50]  # Different meteorite sizes 
        self.meteorite_masses = [1.0, 2.0, 3.0, 4.0]  # Corresponding masses 
        
    def update(self, dt, simulation_time):
        """Update the meteorite shower"""
        if not self.started and simulation_time >= self.trigger_time:
            self.started = True
            self.active = True
            print("Meteorite shower started!")
            
        if self.active and not self.finished:
            self.time_active += dt
            
            # Spawn new meteorites
            self.spawn_timer += dt
            if (self.spawn_timer >= self.spawn_interval and 
                self.total_meteorites_spawned < self.max_meteorites):
                self._spawn_meteorite()
                self.spawn_timer = 0
                
            # Update existing meteorites
            for meteorite in self.meteorites[:]:
                meteorite.update(dt)
                if not meteorite.active:
                    self.meteorites.remove(meteorite)
            
            # Check if shower should end
            if self.time_active >= self.duration and len(self.meteorites) == 0:
                self.finished = True
                self.active = False
                print("Meteorite shower finished!")
    
    def _spawn_meteorite(self):
        """Spawn a new meteorite with random properties"""
        # Random spawn position across the top of screen
        spawn_x = np.random.uniform(50, self.screen_width - 50)
        spawn_y = -50  # Start above screen
        
        # Random velocity with some horizontal variance
        velocity_x = np.random.uniform(-100, 100)  # Some horizontal movement
        velocity_y = np.random.uniform(150, 300)   # Downward velocity
        
        # Random size and corresponding mass
        size_index = np.random.randint(0, len(self.meteorite_sizes))
        size = self.meteorite_sizes[size_index]
        mass = self.meteorite_masses[size_index]
        
        # Add some random variance to mass
        mass *= np.random.uniform(0.8, 1.2)
        
        meteorite = Meteorite(spawn_x, spawn_y, velocity_x, velocity_y, size, mass)
        self.meteorites.append(meteorite)
        self.total_meteorites_spawned += 1
        
        print(f"Spawned meteorite {self.total_meteorites_spawned}/{self.max_meteorites} at x={spawn_x:.1f}")
    
    def draw(self, surface):
        """Draw all meteorites and shower effects"""
        if not self.started:
            return
            
        # Draw all meteorites
        for meteorite in self.meteorites:
            meteorite.draw(surface)
        
        # Draw shower progress indicator
        if self.active:
            progress_bar_width = 200
            progress_bar_height = 20
            progress_bar_x = 20
            progress_bar_y = 20
            
            # Background bar
            pygame.draw.rect(surface, (50, 50, 50), 
                           (progress_bar_x, progress_bar_y, progress_bar_width, progress_bar_height))
            
            # Progress bar
            progress_ratio = min(1.0, self.time_active / self.duration)
            progress_width = int(progress_bar_width * progress_ratio)
            color = (255, 100 + int(155 * (1 - progress_ratio)), 0)  # Orange to red
            pygame.draw.rect(surface, color, 
                           (progress_bar_x, progress_bar_y, progress_width, progress_bar_height))
            
            # Label
            font = pygame.font.SysFont('Arial', 16)
            text = font.render("METEORITE SHOWER", True, (255, 255, 255))
            surface.blit(text, (progress_bar_x, progress_bar_y - 25))
            
            # Count indicator
            count_text = font.render(f"Meteorites: {len(self.meteorites)}", True, (255, 255, 255))
            surface.blit(count_text, (progress_bar_x, progress_bar_y + progress_bar_height + 5))
    
    def check_collision_with_tile(self, tile):
        """Check if any meteorite collides with the given tile"""
        for meteorite in self.meteorites:
            if meteorite.check_collision_with_tile(tile):
                return True
        return False


class ChallengeManager:
    """Manages all challenges for a level"""
    
    def __init__(self, level_id, screen_width, screen_height):
        self.level_id = level_id
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.challenges = []
        
        # Initialize challenges based on level
        self._setup_challenges()
    
    def _setup_challenges(self):
        """Setup challenges based on level ID"""
        if self.level_id == 1:  # Earth level
            # Add wrecking ball that triggers at 2 seconds
            wrecking_ball = WreckingBall(self.screen_width, self.screen_height, trigger_time=2.0)
            self.challenges.append(wrecking_ball)
          # Future levels can have different challenges
        elif self.level_id == 2:  # Jupiter level - strong winds
            wind_challenge = Wind(self.screen_width, self.screen_height, trigger_time=1.5, duration=4.0)
            self.challenges.append(wind_challenge)
        elif self.level_id == 3:  # Mars level - meteor shower
            meteor_shower = MeteoriteShower(self.screen_width, self.screen_height, trigger_time=1.0, duration=6.0)
            self.challenges.append(meteor_shower)
    
    def update(self, dt, simulation_time, tiles):
        """Update all challenges and check collisions"""
        for challenge in self.challenges:
            challenge.update(dt, simulation_time)
            
            # Check collisions with tiles
            if hasattr(challenge, 'check_collision_with_tile'):
                for tile in tiles:
                    challenge.check_collision_with_tile(tile)
            
            # Apply wind to tiles if wind challenge is active
            if isinstance(challenge, Wind) and challenge.active:
                challenge.apply_wind_to_tiles(tiles)
    
    def draw(self, surface):
        """Draw all active challenges"""
        for challenge in self.challenges:
            challenge.draw(surface)
    
    def get_warning_text(self, simulation_time):
        """Get warning text for upcoming challenges"""
        warnings = []
        
        for challenge in self.challenges:
            if hasattr(challenge, 'trigger_time'):
                time_until = challenge.trigger_time - simulation_time
                if 0 < time_until <= 1.0 and not challenge.started:
                    if isinstance(challenge, WreckingBall):
                        warnings.append(f"WRECKING BALL INCOMING! {time_until:.1f}s")
                    elif isinstance(challenge, Wind):
                        warnings.append(f"WIND STARTS IN {time_until:.1f}s")
                    elif isinstance(challenge, MeteoriteShower):
                        warnings.append(f"METEORITE SHOWER INCOMING! {time_until:.1f}s")
        
        return warnings
