"""
SpaceScrapers - A physics-based tower building game
==================================================

Main game module that orchestrates all game systems including:
- Level management and progression
- Physics-based tile placement and collision detection  
- Challenge systems (wrecking balls, meteorites, wind)
- Visual effects and animations
- Game state management (building -> simulation -> results)

Core Game Loop:
1. Show intro and menu screens
2. Player selects level from available space environments
3. Display level objective and controls tutorial
4. Building phase: drag and place tiles to build tower (pixel-perfect collision)
5. Simulation phase: physics simulation + environmental challenges for 6 seconds
6. Results: check if tower reaches target height and survives all challenges

Technical Features:
- Real-time physics simulation with gravity, friction, and collision response
- Pixel-perfect collision detection using pygame masks
- Dynamic support detection for realistic tile stacking
- Visual rotation effects separate from physics collision
- Particle effects and animations for enhanced user feedback
- Challenge system with wrecking balls, meteorites, and wind forces

Controls:
- Mouse: Drag tiles from selection area to build area
- SPACE: Start simulation phase
- ESC: Return to menu
- R: Reset level (during building phase)

Author: SpaceScrapers Team
"""

import pygame
import sys
import time

# Screen and UI modules
from screens.intro import IntroScreen
from screens.menu import MenuScreen
from screens.level_select import LevelSelectScreen
from screens.win import WinScreen
from screens.lose import LoseScreen

# Game core modules
from storage.level_storage import LevelStorage
from game.level import Level
from tile_placement import TilePlacer
from sprite_manager import sprite_manager
from challenges import ChallengeManager
from animations import animation_manager

def show_objective_screen(screen, level_data):
    """
    Display the level objective and controls before starting gameplay.
    
    Shows:
    - Level name and objective description
    - Game controls (drag tiles, rotate with R, start with SPACE)
    - Can be skipped by pressing any key or clicking
    
    Args:
        screen: Pygame display surface
        level_data: Dictionary containing level configuration
    """
    font_large = pygame.font.SysFont(None, 60)
    font_medium = pygame.font.SysFont(None, 40)
    font_small = pygame.font.SysFont(None, 32)
    
    start_time = time.time()
    duration = 10  # Show for 10 seconds

    while time.time() - start_time < duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return  # Skip to game if user presses any key
        
        screen.fill((30, 30, 60))
        
        # Level name
        level_text = font_large.render(level_data["name"], True, (255, 255, 255))
        level_rect = level_text.get_rect(center=(screen.get_width()//2, 150))
        screen.blit(level_text, level_rect)
        
        # Objective
        objective_text = font_medium.render("OBJECTIVE:", True, (200, 200, 255))
        obj_rect = objective_text.get_rect(center=(screen.get_width()//2, 220))
        screen.blit(objective_text, obj_rect)
        
        # Objective description
        obj_desc = font_small.render(level_data.get("objective", "Build and survive!"), True, (200, 200, 200))
        desc_rect = obj_desc.get_rect(center=(screen.get_width()//2, 270))
        screen.blit(obj_desc, desc_rect)
        
        # Controls
        controls = [
            "CONTROLS:",
            "Drag tiles from bottom panel to build",
            "SPACE - Start physics simulation",
            "",
            "Click anywhere to continue..."
        ]
        
        y = 350
        for i, control in enumerate(controls):
            if i == 0:
                color = (255, 200, 100)  # Header color
            elif control == "":
                y += 15
                continue
            else:
                color = (180, 180, 180)
            
            control_text = font_small.render(control, True, color)
            control_rect = control_text.get_rect(center=(screen.get_width()//2, y))
            screen.blit(control_text, control_rect)
            y += 35
        
        pygame.display.flip()

def run_game_level(screen, level_data):
    """
    Main game level execution with three distinct phases.
    
    Phase 1 - Building: Player drags tiles from bottom panel to build tower
    Phase 2 - Simulation: 6-second physics simulation with challenges
    Phase 3 - Results: Check if tower reaches target height and survives
    
    Game Features:
    - Pixel-perfect collision detection between tiles
    - Realistic physics (gravity, friction, tumbling)
    - Visual rotation feedback when tiles become unstable
    - Level-specific challenges (wrecking ball, meteorites, wind)
    - Particle effects and animations
    
    Args:
        screen: Pygame display surface
        level_data: Dictionary containing level configuration
        
    Returns:
        String indicating result: "win", "lose", or "menu"
    """    # === GAME INITIALIZATION ===
    # Create level renderer with background and ground
    level = Level(level_data, screen.get_size())
    
    # Initialize tile placement system with level-specific tile counts
    tile_placer = TilePlacer(level_data["id"], screen.get_height())
    
    # Setup challenge system (wrecking balls, meteorites, wind effects)
    challenge_manager = ChallengeManager(level_data["id"], screen.get_width(), screen.get_height())
    
    # Clear any existing animations and initialize for this level
    animation_manager.clear_all()
    
    # === GAME STATE VARIABLES ===
    game_phase = "building"  # Phases: "building" -> "simulating" -> "finished"
    simulation_start_time = 0
    simulation_duration = 12  # Players must survive 12 seconds of challenges
    countdown_time = 0
    
    # === TARGET HEIGHT SETUP ===
    target_height = level_data.get("target_height", 200)
    ground_y = screen.get_height() - 100
    target_line_y = ground_y - target_height
    
    # Setup animated pulsing target line
    animation_manager.set_pulsing_target_line(screen.get_width(), target_line_y)
      # === MAIN GAME LOOP ===
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Arial', 24)
    font_large = pygame.font.SysFont('Arial', 48)
    font_warning = pygame.font.SysFont('Arial', 32)
    
    while True:
        dt = clock.tick(60) / 1000.0  # Delta time for smooth physics
        mouse_pos = pygame.mouse.get_pos()
        
        # Update all visual effects and animations
        animation_manager.update(dt)
        
        # === EVENT HANDLING ===
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # Building phase: handle tile placement and rotation
            if game_phase == "building":
                tile_placer.handle_event(event, mouse_pos)
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and tile_placer.placed_tiles:
                        # Start physics simulation if tiles are placed
                        game_phase = "simulating"
                        simulation_start_time = time.time()
                    elif event.key == pygame.K_d:
                        # Toggle debug visualization for collision detection
                        import tiles
                        tiles.DEBUG_MODE = not tiles.DEBUG_MODE
            
            # ESC key returns to main menu at any time
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
          # === PHYSICS SIMULATION PHASE ===
        if game_phase == "simulating":
            # Run physics simulation: gravity, collisions, tumbling
            tile_placer.simulate(dt, ground_y)
            
            elapsed_time = time.time() - simulation_start_time
            countdown_time = max(0, simulation_duration - elapsed_time)
            
            # Update level-specific challenges (wrecking balls, meteorites, etc.)
            challenge_manager.update(dt, elapsed_time, tile_placer.placed_tiles)
            
            # Check if simulation time is complete
            if elapsed_time >= simulation_duration:
                game_phase = "finished"        # === RENDERING ===
        # Draw level background and ground
        level.draw(screen)
        
        # Draw all placed tiles with physics and visual effects
        tile_placer.draw_placed_tiles(screen)
        
        # Draw level-specific challenges
        challenge_manager.draw(screen)
        
        # Draw all animations and particle effects
        animation_manager.draw(screen)
          # Draw target height text with better visibility
        target_text = font.render(f"Target Height: {target_height}px", True, (255, 255, 0))
        target_bg = pygame.Surface((target_text.get_width() + 10, target_text.get_height() + 5), pygame.SRCALPHA)
        target_bg.fill((0, 0, 0, 180))  # Semi-transparent background
        screen.blit(target_bg, (5, target_line_y - 35))
        screen.blit(target_text, (10, target_line_y - 30))
          # === PHASE-SPECIFIC UI ===
        if game_phase == "building":
            # Draw tile selection area at bottom of screen
            tile_placer.draw_selection_area(screen)
            tile_placer.draw_dragged_tile(screen, mouse_pos)
            
            # Show building instructions
            instructions = [
                "Drag tiles to build your tower",
                "SPACE - Start simulation"
            ]
            y = 10
            for instruction in instructions:
                text = font.render(instruction, True, (200, 200, 200))
                screen.blit(text, (10, y))
                y += 25
        
        elif game_phase == "simulating":
            # Show countdown timer
            countdown_text = font_large.render(f"Time left: {countdown_time:.1f}s", True, (255, 100, 100))
            countdown_rect = countdown_text.get_rect(center=(screen.get_width()//2, 50))
            screen.blit(countdown_text, countdown_rect)            # Show tower height progress with color-coded feedback
            current_height = tile_placer.get_tower_height(ground_y)
            progress_ratio = min(1.0, current_height / target_height)
            
            if progress_ratio >= 0.9:
                # Close to target - green text
                height_color = (100, 255, 100)
                progress_text = "Almost there!"
            elif progress_ratio >= 0.7:
                # Good progress - yellow text
                height_color = (255, 255, 100)
                progress_text = "Good progress!"
            else:
                # Normal progress - white text
                height_color = (200, 200, 200)
                progress_text = f"Progress: {progress_ratio:.1%}"
            
            height_text = font.render(f"Tower Height: {current_height:.0f}px", True, height_color)
            screen.blit(height_text, (10, 80))
            
            progress_label = font.render(progress_text, True, height_color)
            screen.blit(progress_label, (10, 105))
            
            # Display challenge warning messages
            elapsed_time = time.time() - simulation_start_time
            warnings = challenge_manager.get_warning_text(elapsed_time)
            warning_y = 120
            for warning in warnings:
                warning_text = font_warning.render(warning, True, (255, 255, 0))
                warning_rect = warning_text.get_rect(center=(screen.get_width()//2, warning_y))
                screen.blit(warning_text, warning_rect)
                warning_y += 40
        
        elif game_phase == "finished":
            # Determine win/lose condition based on final tower height
            current_height = tile_placer.get_tower_height(ground_y)
            if current_height >= target_height:
                return "win"
            else:
                return "lose"
        
        pygame.display.flip()

def main():
    """
    Main application entry point.
    
    Orchestrates the complete game flow:
    1. Initialize Pygame and load game assets
    2. Show intro sequence
    3. Main menu loop with level selection
    4. Level gameplay loop with win/lose handling
    5. Clean shutdown
    """    # === PYGAME INITIALIZATION ===
    pygame.init()
    screen = pygame.display.set_mode((1200, 1000))
    pygame.display.set_caption("SpaceScrapers")
    
    # Load sprite assets for tile graphics
    sprite_manager.load_spritesheet("blocks", "sprites/scifi_platformTiles_32x32.png", 96, 96)
    
    # Show intro sequence
    intro = IntroScreen(screen)
    intro.run(duration=3)
    
    # === MAIN GAME LOOP ===
    while True:
        # Show main menu
        menu = MenuScreen(screen)
        menu.run()
        
        # Level selection screen
        selector = LevelSelectScreen(screen)
        selected_level_id = selector.run()
        if selected_level_id is None:
            break  # Exit if no level selected
        
        # Load selected level data
        level_data = LevelStorage.get_level_by_id(selected_level_id)
        if not level_data:
            continue  # Skip if level data not found
        
        # === LEVEL GAMEPLAY LOOP ===
        while True:  # Level retry loop
            # Show level objective and controls
            show_objective_screen(screen, level_data)
            
            # Run the main gameplay
            result = run_game_level(screen, level_data)
            
            # Handle win condition
            if result == "win":
                win_screen = WinScreen(screen, level_data["name"])
                choice = win_screen.run()
                if choice == "menu":
                    break  # Return to main menu
                elif choice == "levels":
                    break  # Return to level selection
                else:
                    break  # Default: return to menu
                    
            # Handle lose condition
            elif result == "lose":
                lose_screen = LoseScreen(screen, level_data["name"])
                choice = lose_screen.run()
                if choice == "restart":
                    continue  # Retry the same level
                elif choice == "menu":
                    break  # Return to main menu
                else:
                    break  # Default: return to menu
                    
            # Handle escape to menu
            elif result == "menu":
                break  # Return to main menu
            
            break  # Exit level retry loop
    
    # === CLEAN SHUTDOWN ===
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
