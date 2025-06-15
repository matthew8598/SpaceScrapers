"""
Level Data Storage and Management
================================

Centralized storage system for all level definitions and configurations.

Level Structure:
- Basic Info: Name, ID, background assets
- Objectives: Target height, survival requirements, special conditions
- Resources: Available tile types and quantities
- Challenges: Environmental hazards specific to each level
- Progression: Unlock requirements and difficulty scaling

Features:
- Static level definitions for consistent gameplay
- Easy level modification and balancing
- Extensible structure for new level types
- Asset path management for backgrounds and sprites

Level Themes:
1. Earth: Gentle introduction with wrecking ball challenge
2. Jupiter: Wind-based challenges testing structural stability  
3. Mars: Meteorite impacts requiring robust construction

"""

class LevelStorage:
    """
    Static storage and retrieval system for all game levels.
    
    Provides:
    - Complete level definitions with all required data
    - Asset path management for backgrounds and sprites
    - Tile allocation and challenge configuration per level
    - Easy access methods for level selection and loading
    
    Currently uses static definitions but designed to be easily
    extended for file-based or database-driven level storage.
    """
    @staticmethod
    def load_levels():
        # In the future, load from file or database
        return [            {
                "name": "Level 1: Earth",
                "id": 1,
                "background_image": "assets/windows-xp-bliss-wallpaper-hq-2560x1440-v0-nbjxvz68exbb1-ezgif.com-webp-to-jpg-converter.jpg",
                "ground_image": (80, 60, 40),
                "target_height": 400,  # Height above ground that tower must reach
                "objective": "Build a tower to reach the target line and survive for 12 seconds. Be careful giant wrecking ball is coming!",
                "tiles": {
                    "rectangle": {"count": 2},
                    "beam": {"count": 2},
                    "square": {"count": 2}
                }
            },
            {
                "name": "Level 2: Jupiter",
                "id": 2,
                "background_image": "assets/surface_of_jupiter_by_xdeathwingx_d9cb06o-fullview.jpg",
                "ground_image": (60, 80, 100),
                "target_height": 500,  # Slightly higher target
                "objective": "Build a tower to reach the target line and survive for 12 seconds with jupiters strong winds",
                "tiles": {
                    "rectangle": {"count": 3},
                    "beam": {"count": 3},
                    "square": {"count": 1}
                }
            },
            {
                "name": "Level 3: Mars",
                "id": 3,
                "background_image": "assets/mars-planeta-opportunity-foto-1792.jpg",
                "ground_image": (100, 60, 60),
                "target_height": 650,  # Highest target
                "objective": "Build a tower to reach the target line and survive for 12 seconds. watch out for the meteor shower!",
                "tiles": {
                    "square": {"count": 2},
                    "rectangle": {"count": 3},
                    "beam": {"count": 4},
                }
            }
        ]

    @staticmethod
    def get_level_by_id(level_id):
        levels = LevelStorage.load_levels()
        for level in levels:
            if level["id"] == level_id:
                return level
        return None
