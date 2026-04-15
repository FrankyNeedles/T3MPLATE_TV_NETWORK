import pygame
import threading
from pathlib import Path
from typing import Dict, Any

class Renderer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("T3MPLATE TV Network - Live Broadcast")
        self.clock = pygame.time.Clock()
        self.running = True
        self.sprite_cache = {}
        self.status: Dict[str, Any] = {}
        self.screen_loop_thread = threading.Thread(target=self._screen_loop, daemon=True)
        self.screen_loop_thread.start()
        print("T3MPLATE TV Renderer Ready: 1280x720 60fps w/ authentic sprites + CRT")

    def update_status(self, status: Dict[str, Any]):
        self.status = status

    def load_sprite(self, rel_path: str):
        full_path = Path(__file__).parent.parent / rel_path
        p = str(full_path)
        if p not in self.sprite_cache:
            self.sprite_cache[p] = pygame.image.load(p).convert_alpha()
        return self.sprite_cache[p]

    def tick(self):
        self.screen.fill((10, 10, 30))
        mario_rel = "assets/authentic_sprites/super_mario_world_mario.png"
        if (Path(__file__).parent.parent / mario_rel).exists():
            mario = pygame.transform.scale(self.load_sprite(mario_rel), (128, 128))
            self.screen.blit(mario, (100, 500))
        ness_rel = "assets/ASSETS/sprites/ness_0x3_0x82000.png"
        if (Path(__file__).parent.parent / ness_rel).exists():
            ness = pygame.transform.scale(self.load_sprite(ness_rel), (96, 96))
            self.screen.blit(ness, (300, 520))
        font_l = pygame.font.Font(None, 48)
        title = font_l.render("T3MPLATE TV NETWORK", True, (0, 255, 0))
        self.screen.blit(title, (20, 20))
        font_s = pygame.font.Font(None, 32)
        sub = font_s.render("Gary PD Live - SNES Universe Broadcast", True, (255,255,255))
        self.screen.blit(sub, (20, 70))
        status_t = pygame.font.Font(None, 24).render(f"Phase: {self.status.get('phase', '?')} | Shows: {self.status.get('shows', 0)} | Relationships: {self.status.get('relationships', 0)}", True, (255,255,0))
        self.screen.blit(status_t, (20, 110))
        scan_surf = pygame.Surface((1280, 720), pygame.SRCALPHA)
        for i in range(0, 720, 3):
            alpha = 25 if i % 6 == 0 else 10
            pygame.draw.line(scan_surf, (0,0,0,alpha), (0,i), (1280,i))
        self.screen.blit(scan_surf, (0,0))
        pygame.display.flip()
        self.clock.tick(60)

    def _screen_loop(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            self.tick()
        pygame.quit()

    def format_for_gary(self) -> str:
        return f"Status: {{'phase': '{self.status.get('phase', 'dev')}', 'shows': {self.status.get('shows', 0)}}}"

renderer = Renderer()
