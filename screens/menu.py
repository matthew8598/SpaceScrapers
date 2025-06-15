import pygame
from screens.level_select import LevelSelectScreen

class MenuScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 48)
        self.buttons = {
            "start": pygame.Rect(0, 0, 260, 60),
            "select": pygame.Rect(0, 0, 260, 60)
        }
        self.buttons["start"].center = (screen.get_width()//2, screen.get_height()//2)
        self.buttons["select"].center = (screen.get_width()//2, screen.get_height()//2 + 90)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.buttons["start"].collidepoint(event.pos):
                        running = False  # Start new game
                    if self.buttons["select"].collidepoint(event.pos):
                        selector = LevelSelectScreen(self.screen)
                        selected_level_id = selector.run()
                        if selected_level_id is not None:
                            running = False  # Proceed to game if a level was selected

            self.screen.fill((40, 40, 80))
            title = self.font.render("Main Menu", True, (255, 255, 255))
            self.screen.blit(title, (self.screen.get_width()//2 - title.get_width()//2, 150))

            pygame.draw.rect(self.screen, (100, 200, 100), self.buttons["start"])
            btn_text = self.font.render("Start Game", True, (0, 0, 0))
            self.screen.blit(btn_text, (self.buttons["start"].centerx - btn_text.get_width()//2, self.buttons["start"].centery - btn_text.get_height()//2))

            pygame.display.flip()
