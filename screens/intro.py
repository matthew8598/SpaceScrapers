import pygame
import time

class IntroScreen:
    def __init__(self, screen):
        self.screen = screen

    def run(self, duration=3):
        start_time = time.time()
        font = pygame.font.SysFont(None, 60)
        while time.time() - start_time < duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
            self.screen.fill((30, 30, 60))
            text = font.render("SpaceScrapers", True, (255, 255, 255))
            self.screen.blit(text, (self.screen.get_width()//2 - text.get_width()//2, self.screen.get_height()//2 - text.get_height()//2))
            pygame.display.flip()
