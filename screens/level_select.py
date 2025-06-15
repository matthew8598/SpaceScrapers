import pygame
from storage.level_storage import LevelStorage

class LevelSelectScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 40)
        self.levels = LevelStorage.load_levels()
        self.button_rects = []
        self.back_rect = pygame.Rect(20, 20, 120, 50)
        self._setup_buttons()

    def _setup_buttons(self):
        y = 150
        for i, level in enumerate(self.levels):
            rect = pygame.Rect(0, 0, 320, 60)
            rect.center = (self.screen.get_width()//2, y)
            self.button_rects.append((rect, level))
            y += 80

    def run(self):
        selecting = True
        selected_level_id = None
        while selecting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.back_rect.collidepoint(event.pos):
                        selecting = False
                        selected_level_id = None
                    for rect, level in self.button_rects:
                        if rect.collidepoint(event.pos):
                            selected_level_id = level['id']
                            selecting = False

            self.screen.fill((30, 30, 60))
            title = self.font.render("Select Level", True, (255, 255, 255))
            self.screen.blit(title, (self.screen.get_width()//2 - title.get_width()//2, 60))

            for rect, level in self.button_rects:
                pygame.draw.rect(self.screen, (180, 180, 100), rect)
                txt = self.font.render(level['name'], True, (0, 0, 0))
                self.screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

            pygame.draw.rect(self.screen, (200, 100, 100), self.back_rect)
            back_txt = self.font.render("Back", True, (0, 0, 0))
            self.screen.blit(back_txt, (self.back_rect.centerx - back_txt.get_width()//2, self.back_rect.centery - back_txt.get_height()//2))

            pygame.display.flip()

        return selected_level_id
