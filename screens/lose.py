import pygame

class LoseScreen:
    def __init__(self, screen, level_name):
        self.screen = screen
        self.level_name = level_name
        self.font_large = pygame.font.SysFont(None, 72)
        self.font_medium = pygame.font.SysFont(None, 48)
        self.font_small = pygame.font.SysFont(None, 36)
        
        # Button setup
        self.buttons = {
            "restart": pygame.Rect(0, 0, 200, 60),
            "menu": pygame.Rect(0, 0, 200, 60)
        }
        screen_width, screen_height = screen.get_size()
        self.buttons["restart"].center = (screen_width//2 - 120, screen_height//2 + 100)
        self.buttons["menu"].center = (screen_width//2 + 120, screen_height//2 + 100)

    def run(self):
        """Returns 'restart', 'menu', or None"""
        running = True
        result = None
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.buttons["restart"].collidepoint(event.pos):
                        result = "restart"
                        running = False
                    elif self.buttons["menu"].collidepoint(event.pos):
                        result = "menu"
                        running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        result = "restart"
                        running = False
                    elif event.key == pygame.K_ESCAPE:
                        result = "menu"
                        running = False

            # Draw screen
            self.screen.fill((40, 20, 20))  # Dark red background
            
            # Fail message
            fail_text = self.font_large.render("LEVEL FAILED", True, (255, 100, 100))
            text_rect = fail_text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2 - 100))
            self.screen.blit(fail_text, text_rect)
            
            # Level name
            level_text = self.font_medium.render(f"{self.level_name}", True, (255, 200, 200))
            level_rect = level_text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2 - 40))
            self.screen.blit(level_text, level_rect)
            
            # Failure message
            failure_text = self.font_small.render("Your tower didn't reach the target height or collapsed!", True, (255, 150, 150))
            failure_rect = failure_text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2))
            self.screen.blit(failure_text, failure_rect)
            
            # Draw buttons
            pygame.draw.rect(self.screen, (100, 255, 100), self.buttons["restart"])
            restart_text = self.font_small.render("Try Again", True, (0, 0, 0))
            restart_rect = restart_text.get_rect(center=self.buttons["restart"].center)
            self.screen.blit(restart_text, restart_rect)
            
            pygame.draw.rect(self.screen, (100, 150, 255), self.buttons["menu"])
            menu_text = self.font_small.render("Main Menu", True, (0, 0, 0))
            menu_rect = menu_text.get_rect(center=self.buttons["menu"].center)
            self.screen.blit(menu_text, menu_rect)
            
            # Instructions
            instructions = self.font_small.render("Press R to restart, ESC for Main Menu", True, (100, 100, 100))
            instructions_rect = instructions.get_rect(center=(self.screen.get_width()//2, self.screen.get_height() - 50))
            self.screen.blit(instructions, instructions_rect)

            pygame.display.flip()

        return result
