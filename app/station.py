"""
T3MPLATE TV Station - FULL_VISION 90s Broadcast Engine
Status: Phase 6 - SNES ROM Decoder + Gary Ticker
"""
import pygame
import random
import logging
from pathlib import Path
from PIL import Image
from typing import Dict
from app.gary import gary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SNES_STATION")

SMW_PALETTE = [  # SMW Sprite Palette 0 (RGB)
    (0, 0, 0), (252, 252, 252), (8, 120, 0), (116, 120, 0),
    (236, 188, 188), (248, 0, 0), (188, 188, 188), (8, 136, 0),
    (0, 168, 0), (0, 0, 252), (248, 56, 0), (160, 168, 0),
    (0, 188, 236), (88, 216, 248), (0, 120, 248), (248, 120, 88),
]

class Station:
    def __init__(self):
        logger.info("Initializing T3MPLATE TV Hardware...")
        
        # 1. Initialize Pygame
        pygame.init()
        self.screen_width = 512
        self.screen_height = 448
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("T3MPLATE TV - LIVE BROADCAST")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Courier", 24, bold=True)
        self.ticker_font = pygame.font.SysFont("Courier", 20)
        
        # 2. Load Assets
        self.sprites = self._load_assets()
        self.active_actor = None
        self.gary_thought = "GARY THINKING..."
        self.current_time = 8.0

        # 3. Audio Mixer
        pygame.mixer.init(frequency=32000, size=-16, channels=1)
        self.current_audio = None

        # 4. State
        self.tick_count = 0
        self.status = {"phase": "6.0", "ready": True, "sprites": len(self.sprites)}

    def decode_snes_sprite(self, bank: int, offset: int, size=(32, 32)) -> pygame.Surface:
        """Decode 4bpp SNES sprite from ROM at bank:offset"""
        try:
            with open(self.rom_path, 'rb') as f:
                f.seek(bank * 0x10000 + offset)
                raw_data = f.read(size[0]*size[1]*4)  # 4bpp = 4 bytes per 8x8 tile
            
            # PIL decode logic (ported from authentic extractor)
            img = Image.new('P', size)
            img.putpalette(sum(SMW_PALETTE, ()) + (0,0,0)* (256 - len(SMW_PALETTE)))
            pixels = img.load()
            
            for ty in range(size[1]//8):
                for tx in range(size[0]//8):
                    tile_off = (ty*4 + tx) * 32  # 32 bytes per tile
                    planes = [raw_data[tile_off + i*8:tile_off + (i+1)*8] for i in range(4)]
                    
                    for row in range(8):
                        for col in range(8):
                            bits = 0
                            for p in range(4):
                                bits |= ((ord(planes[p][row]) >> (7-col)) & 1) << p
                            pixels[tx*8 + col, ty*8 + row] = bits
            
            # PIL to Pygame + 4x scale
            pygame_img = pygame.image.fromstring(img.tobytes(), size, 'P')
            pygame_img.set_palette(SMW_PALETTE)
            scaled = pygame.transform.scale(pygame_img, (size[0]*4, size[1]*4))
            return scaled
            
        except Exception as e:
            logger.error(f"SNES decode failed bank {bank:02X} off {offset:06X}: {e}")
            return pygame.Surface((32*4, 32*4))

    def _load_assets(self) -> Dict[str, pygame.Surface]:
        """Load PNG sprites from assets/sprites (real extracted first), fallback ROM decode."""
        sprite_dict = {}
        
        # Priority 1: Real extracted sprites (new pipeline)
        real_sprite_path = Path("assets/sprites")
        real_count = 0
        if real_sprite_path.exists():
            for img_file in real_sprite_path.glob("*.png"):
                try:
                    name = img_file.stem
                    surface = pygame.image.load(str(img_file)).convert_alpha()
                    surface.set_colorkey((0, 0, 0))
                    scaled = pygame.transform.scale(surface, (128, 128))  # 32x32 * 4x
                    sprite_dict[name] = scaled
                    real_count += 1
                    logger.info(f"Real PNG: {name} ({surface.get_size()})")
                except Exception as e:
                    logger.error(f"PNG load failed {img_file}: {e}")
        
        logger.info(f"Loaded {real_count} real sprites from pipeline")
        
        # Fallback: Old authentic_sprites or ROM decode
        fallback_path = Path("assets/authentic_sprites")
        if fallback_path.exists():
            for img_file in fallback_path.glob("*.png"):
                name = img_file.stem
                if name not in sprite_dict:
                    try:
                        surface = pygame.image.load(str(img_file)).convert_alpha()
                        scaled = pygame.transform.scale(surface, (128, 128))
                        sprite_dict[name] = scaled
                        logger.info(f"Fallback PNG: {name}")
                    except Exception as e:
                        logger.error(f"Fallback PNG failed {img_file}: {e}")
        
        # ROM decode fallback (sample.sfc)
        self.rom_path = "ROM_SOURCE/sample.sfc"
        if Path(self.rom_path).exists():
            logger.info(f"ROM fallback: {self.rom_path}")
            for name in ["mario_0xD_0xAC000"]:
                if name not in sprite_dict:
                    parts = name.rsplit('_', 2)
                    _, bank_str, off_str = parts
                    bank = int(bank_str, 16)
                    offset = int(off_str, 16)
                    surface = self.decode_snes_sprite(bank, offset)
                    sprite_dict[name] = surface
                    logger.info(f"ROM decode: {name}")
        
        logger.info(f"Total sprites loaded: {len(sprite_dict)}")
        return sprite_dict

    def _get_daypart(self, hour: float) -> str:
        if 6 <= hour < 10: return "MORNING NEWS"
        if 10 <= hour < 17: return "DAYTIME CARTOONS"
        if 17 <= hour < 20: return "EVENING NEWS"
        return "PRIME TIME"

    def tick(self, sprites: Dict[str, pygame.Surface] = None, audio: dict = None, val: int = None) -> Dict:
        """Main game loop tick"""
        pygame.event.pump()  # Windows responsiveness

        if val is not None:
            self.tick_count = val
        if sprites is not None:
            logger.info(f"External sprites: {len(sprites)}")

        self.tick_count += 1
        self.current_time = (self.current_time + 0.01) % 24

        # Gary Decision (every 30 seconds)
        if self.tick_count % 1800 == 0:
            try:
                decision = gary.make_decision()
                self.gary_thought = decision.thought if decision.thought else "Gary offline"
                logger.info(f"GARY: {decision.show} - {decision.thought}")
                
                # Audio cue
                if decision.music_cue and 'track' in decision.music_cue:
                    track = decision.music_cue['track'].lower()
                    wav_path = f"assets/audio/{track}.wav"
                    if Path(wav_path).exists():
                        pygame.mixer.music.load(wav_path)
                        pygame.mixer.music.play(-1)
                        logger.info(f"Playing: {track}")
            except Exception as e:
                logger.error(f"Gary decision failed: {e}")
                self.gary_thought = "Gary decision error"

        # Actor selection
        if self.tick_count % 300 == 1 or self.active_actor is None:
            available = [s for s in self.sprites if s != 'ZERO']
            if available:
                actor_name = random.choice(available)
                self.active_actor = (actor_name, self.sprites[actor_name])
                logger.info(f"ON AIR: {actor_name}")

        # Render
        self.screen.fill((16, 16, 48))  # SNES blue
        
        # Scanlines
        for y in range(0, self.screen_height, 3):
            pygame.draw.line(self.screen, (8, 8, 32), (0, y), (self.screen_width, y))

        # Actor
        if self.active_actor:
            name, surf = self.active_actor
            x = (self.screen_width//2) - (surf.get_width()//2)
            y = (self.screen_height//2) - (surf.get_height()//2)
            self.screen.blit(surf, (x, y))
            
            # Name tag
            tag = self.font.render(name.upper(), True, (255, 255, 0))
            self.screen.blit(tag, (x, y - 35))

        # Gary Ticker (bottom)
        ticker_surf = self.ticker_font.render(self.gary_thought[:80], True, (0, 255, 0))
        pygame.draw.rect(self.screen, (0, 0, 0), (0, self.screen_height-35, self.screen_width, 35))
        self.screen.blit(ticker_surf, (10, self.screen_height-30))

        # HUD
        time_str = f"T3MPLATE TV | {int(self.current_time):02d}:00 | Phase 6.0"
        hud = self.font.render(time_str, True, (0, 255, 255))
        self.screen.blit(hud, (10, 10))

        pygame.display.flip()
        self.clock.tick(60)
        
        return {
            "phase": "6.0 - SNES Decoder + Gary Live", 
            "sprites_loaded": len(self.sprites),
            "actor": self.active_actor[0] if self.active_actor else "None",
            "gary_thought": self.gary_thought[:50]
        }

station = Station()
