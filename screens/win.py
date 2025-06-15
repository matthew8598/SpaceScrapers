import pygame

class WinScreen:
    def __init__(self, screen, level_name):
        self.screen = screen
        self.level_name = level_name
        self.font_large = pygame.font.SysFont(None, 72)
        self.font_medium = pygame.font.SysFont(None, 48)
        self.font_small = pygame.font.SysFont(None, 36)
        
        # Button setup
        self.buttons = {
            "menu": pygame.Rect(0, 0, 200, 60),
            "levels": pygame.Rect(0, 0, 200, 60)
        }
        screen_width, screen_height = screen.get_size()
        self.buttons["menu"].center = (screen_width//2 - 120, screen_height//2 + 100)
        self.buttons["levels"].center = (screen_width//2 + 120, screen_height//2 + 100)

    def run(self):
        """Returns 'menu', 'levels', or None"""
        running = True
        result = None
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.buttons["menu"].collidepoint(event.pos):
                        result = "menu"
                        running = False
                    elif self.buttons["levels"].collidepoint(event.pos):
                        result = "levels"
                        running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        result = "menu"
                        running = False

            # Draw screen
            self.screen.fill((20, 40, 20))  # Dark green background
            
            # Win message
            win_text = self.font_large.render("LEVEL COMPLETE!", True, (100, 255, 100))
            text_rect = win_text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2 - 100))
            self.screen.blit(win_text, text_rect)
            
            # Level name
            level_text = self.font_medium.render(f"{self.level_name}", True, (200, 255, 200))
            level_rect = level_text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2 - 40))
            self.screen.blit(level_text, level_rect)
            
            # Congratulations message
            congrats_text = self.font_small.render("Your tower survived the test!", True, (150, 255, 150))
            congrats_rect = congrats_text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2))
            self.screen.blit(congrats_text, congrats_rect)
            
            # Draw buttons
            pygame.draw.rect(self.screen, (100, 150, 255), self.buttons["menu"])
            menu_text = self.font_small.render("Main Menu", True, (0, 0, 0))
            menu_rect = menu_text.get_rect(center=self.buttons["menu"].center)
            self.screen.blit(menu_text, menu_rect)
            
            pygame.draw.rect(self.screen, (150, 100, 255), self.buttons["levels"])
            levels_text = self.font_small.render("Level Select", True, (0, 0, 0))
            levels_rect = levels_text.get_rect(center=self.buttons["levels"].center)
            self.screen.blit(levels_text, levels_rect)
            
            # Instructions
            instructions = self.font_small.render("Press ESC for Main Menu", True, (100, 100, 100))
            instructions_rect = instructions.get_rect(center=(self.screen.get_width()//2, self.screen.get_height() - 50))
            self.screen.blit(instructions, instructions_rect)

            pygame.display.flip()

        return result
