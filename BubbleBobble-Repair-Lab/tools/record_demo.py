#!/usr/bin/env python3
"""Record the two required 10-second gameplay clips without a desktop.

The script drives the real game loop (``Game.update`` + ``Game.draw``) with
scripted keyboard input, then pipes raw RGB frames to ffmpeg. It is fully
deterministic: ``random`` is seeded and the simulation always steps at 60 Hz,
while the output video is 30 fps (600 simulation steps -> 300 frames).

Usage
-----
    python tools/record_demo.py --mode before --out media/before.mp4
    python tools/record_demo.py --mode after  --out media/after.mp4

``before`` loads ``legacy/game_before.py`` (the untouched original), while
``after`` loads the completed ``game.py`` from the repository root.
"""

import argparse
import importlib.util
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 800, 600
FPS_OUT, FPS_SIM = 30, 60
SECONDS = 10
TOTAL_STEPS = SECONDS * FPS_SIM
CAPTION_TOP = 38


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Keys:
    """Minimal stand-in for pygame's ScancodeWrapper."""

    def __init__(self):
        self.down = set()

    def __getitem__(self, key):
        return 1 if key in self.down else 0


class Recorder:
    def __init__(self, module, mode):
        self.mod = module
        self.mode = mode
        self.game = module.Game()
        self.keys = Keys()
        self.font = pygame.font.Font(None, 28)
        self.small = pygame.font.Font(None, 23)
        self.big = pygame.font.Font(None, 56)
        self.huge = pygame.font.Font(None, 72)
        self.frame = 0
        self.local = 0
        self.scene = "idle"
        self.trap_count = 0
        self.attempt_trapped = False
        self.attempt_index = 0
        self.had_trap = False
        self.flash_timer = 0.0
        self.flash_pos = (0, 0)
        self.flash_text = ""
        self.flash_color = (255, 255, 255)
        self._sound_ok = False
        self.setup_idle()

    # ------------------------------------------------------------------ setup
    def base_reset(self):
        g = self.game
        g.state = "play"
        g.level = 1
        g.score = 0
        g.lives = 3
        g.combo = 0
        g.bonus_awarded = 0
        g.player = self.mod.Player()
        g.player.invulnerable = 99.0
        g.enemies = []
        g.bubbles = []
        g.fruits = []
        for name, value in (
            ("sparkles", []),
            ("toasts", []),
            ("fruits_collected", 0),
            ("bonus_flash", 0.0),
        ):
            if hasattr(g, name):
                setattr(g, name, value)

    def setup_idle(self):
        self.base_reset()
        self.game.player.x, self.game.player.y = 250, 570
        self.game.player.facing = 1
        self.game.enemies = [self.mod.Enemy(500, 570)]
        self.scene = "idle"
        self.local = 0

    def setup_attempt(self):
        self.base_reset()
        self.game.player.x, self.game.player.y = 250, 570
        self.game.player.facing = 1
        self.game.enemies = [self.mod.Enemy(500, 570)]
        self.scene = "attempt"
        self.local = 0
        self.attempt_trapped = False

    def setup_trap_scene(self):
        self.setup_attempt()
        self.scene = "trap"

    def setup_showcase(self):
        self.base_reset()
        self.game.player.x, self.game.player.y = 400, 570
        self.scene = "showcase"
        self.local = 0
        for x, y, life in ((250, 330, 8.0), (400, 300, 5.5), (550, 270, 3.2)):
            bubble = self.mod.Bubble(x, y, 1)
            bubble.enemy = self.mod.Enemy(x, y + 80)
            bubble.life = life
            bubble.age = 2.0
            self.game.bubbles.append(bubble)

    def setup_fruit_scene(self):
        self.base_reset()
        g = self.game
        g.score = 4850
        g.player.x, g.player.y = 400, 330
        g.player.facing = 1
        # A distant spectator keeps the level from advancing when the fruit
        # enemy is cleared, so the whole feature demo stays on one screen.
        g.enemies = [self.mod.Enemy(480, 330), self.mod.Enemy(700, 210)]
        self.scene = "fruit"
        self.local = 0
        self.had_trap = False

    # ------------------------------------------------------------------- input
    def set_keys(self):
        self.keys.down.clear()
        if self.scene == "attempt":
            if self.local < 63:
                self.keys.down.add(pygame.K_RIGHT)
            elif self.local < 90:
                self.keys.down.add(pygame.K_LEFT)
            if 37 <= self.local < 42:
                self.keys.down.add(pygame.K_SPACE)
        elif self.scene == "trap":
            if self.local < 63:
                self.keys.down.add(pygame.K_RIGHT)
            elif self.local < 90:
                self.keys.down.add(pygame.K_LEFT)
            if 37 <= self.local < 42:
                self.keys.down.add(pygame.K_SPACE)
        elif self.scene == "fruit":
            if 8 <= self.local < 32:
                self.keys.down.add(pygame.K_RIGHT)
            if 2 <= self.local < 6:
                self.keys.down.add(pygame.K_SPACE)

    def script_actions(self):
        if self.scene in ("attempt", "trap") and self.local == 36:
            if self.game.player.on_ground:
                self.game.player.vy = self.mod.JUMP_SPEED
        if self.scene == "fruit" and self.local == 72:
            if self.game.player.on_ground:
                self.game.player.vy = self.mod.JUMP_SPEED

    # --------------------------------------------------------------- detection
    def detect(self, dt):
        g = self.game
        self.flash_timer = max(0.0, self.flash_timer - dt)

        if self.mode == "after":
            trapped = next((b for b in g.bubbles if b.enemy is not None), None)
            if trapped is not None and not self.had_trap:
                self.had_trap = True
                self.trap_count += 1
                self.flash_timer = 0.7
                self.flash_pos = (trapped.pos.x, trapped.pos.y)
                self.flash_text = "TRAPPED!"
                self.flash_color = (110, 255, 150)
        else:
            if self.scene == "attempt":
                for bubble in g.bubbles:
                    if bubble.enemy is not None and not self.attempt_trapped:
                        self.attempt_trapped = True
                        self.trap_count += 1
                    if bubble.enemy is None:
                        for enemy in g.enemies:
                            if bubble.pos.distance_to(enemy.center) < 34:
                                self.flash_timer = 0.35
                                self.flash_pos = (
                                    (bubble.pos.x + enemy.center.x) / 2,
                                    (bubble.pos.y + enemy.center.y) / 2,
                                )
                                self.flash_text = "NO TRAP"
                                self.flash_color = (255, 110, 110)

    # ------------------------------------------------------------------ scenes
    def timeline(self):
        if self.mode == "before":
            starts = {54: 1, 216: 2, 378: 3}
            if self.frame in starts:
                self.attempt_index = starts[self.frame]
                self.setup_attempt()
            if self.frame == 540:
                self.scene = "end_before"
        else:
            if self.frame == 54:
                self.setup_trap_scene()
                self.had_trap = False
            elif self.frame == 234:
                self.setup_showcase()
            elif self.frame == 366:
                self.setup_fruit_scene()
            elif self.frame == 558:
                self.scene = "end_after"

    # ---------------------------------------------------------------- overlays
    def caption(self, title, subtitle, color=(255, 255, 255)):
        band = pygame.Surface((WIDTH, 58), pygame.SRCALPHA)
        band.fill((5, 6, 20, 190))
        screen.blit(band, (0, CAPTION_TOP))
        label = self.font.render(title, True, color)
        screen.blit(label, (12, CAPTION_TOP + 4))
        if subtitle:
            sub = self.small.render(subtitle, True, (205, 215, 240))
            screen.blit(sub, (12, CAPTION_TOP + 31))

    def draw_flash(self):
        if self.flash_timer <= 0:
            return
        x, y = int(self.flash_pos[0]), int(self.flash_pos[1])
        pygame.draw.circle(screen, self.flash_color, (x, y), 34, 3)
        label = self.font.render(self.flash_text, True, self.flash_color)
        rect = label.get_rect(center=(x, y - 46))
        pygame.draw.rect(screen, (5, 6, 20), rect.inflate(12, 6), border_radius=4)
        screen.blit(label, rect)

    def draw_title(self):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((6, 8, 24, 205))
        screen.blit(veil, (0, 0))
        if self.mode == "before":
            title = self.huge.render("BEFORE THE FIX", True, (255, 120, 120))
            lines = [
                "Original game.py - untouched",
                "Task: show the bubble-trapping bug",
            ]
            foot = "10-second gameplay clip"
        else:
            title = self.huge.render("AFTER THE FIX", True, (120, 255, 170))
            lines = [
                "Bug fixed + all three features implemented",
                "Same brush pass, same input, corrected build",
            ]
            foot = "10-second gameplay clip"
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 205)))
        for index, text in enumerate(lines):
            label = self.font.render(text, True, (225, 232, 250))
            screen.blit(label, label.get_rect(center=(WIDTH // 2, 285 + index * 34)))
        label = self.small.render(foot, True, (150, 160, 190))
        screen.blit(label, label.get_rect(center=(WIDTH // 2, 390)))

    def draw_end_before(self):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((6, 8, 24, 215))
        screen.blit(veil, (0, 0))
        title = self.big.render("BUG REPRODUCED", True, (255, 120, 120))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 170)))
        rows = [
            ("Brush passes shown:", f"{self.trap_count} traps / 3 attempts"),
            ("Original check:", "distance^2 < 24 * 2   (about 6.9 px)"),
            ("Correct check:", "distance^2 < 24 * 24  (24 px)"),
        ]
        for index, (left, right) in enumerate(rows):
            y = 250 + index * 52
            a = self.font.render(left, True, (190, 200, 225))
            b = self.font.render(right, True, (255, 220, 160))
            screen.blit(a, (150, y))
            screen.blit(b, (430, y))

    def draw_end_after(self):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((6, 8, 24, 215))
        screen.blit(veil, (0, 0))
        title = self.big.render("4/4 TASKS COMPLETE", True, (120, 255, 170))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 130)))
        rows = [
            ("[x] Task 1", "trap check uses 24 * 24"),
            ("[x] Task 2", "bubble_tint() by remaining life"),
            ("[x] Task 3", "sparkles + fruit counter"),
            ("[x] Task 4", "1UP every 5000 points"),
        ]
        for index, (tag, text) in enumerate(rows):
            y = 205 + index * 58
            a = self.font.render(tag, True, (255, 225, 130))
            b = self.font.render(text, True, (225, 232, 250))
            screen.blit(a, (170, y))
            screen.blit(b, (330, y))

    def draw_showcase_labels(self):
        for bubble in self.game.bubbles:
            label = self.small.render(f"{bubble.life:0.1f}s", True, (255, 255, 255))
            rect = label.get_rect(center=(int(bubble.pos.x), int(bubble.pos.y) - 30))
            pygame.draw.rect(screen, (5, 6, 20), rect.inflate(8, 2), border_radius=3)
            screen.blit(label, rect)

    def draw_overlays(self):
        if self.mode == "before":
            if self.frame < 54:
                self.draw_title()
            elif self.scene == "attempt":
                self.caption(
                    f"Attempt {self.attempt_index}: bubble brushes the enemy",
                    "Original build: bubble visibly overlaps, but no trap is triggered.",
                    (255, 170, 150),
                )
            elif self.scene == "end_before":
                self.draw_end_before()
        else:
            if self.frame < 54:
                self.draw_title()
            elif self.scene == "trap":
                self.caption(
                    "Task 1: squared-radius trap check",
                    "distance_squared_to(enemy) < 24 * 24  ->  the brush pass traps the enemy.",
                    (140, 255, 180),
                )
            elif self.scene == "showcase":
                self.caption(
                    "Task 2: bubble_tint() follows the escape timer",
                    "Fresh pink (8 s) -> amber -> red + white flash when the bubble is expiring.",
                    (255, 210, 140),
                )
                self.draw_showcase_labels()
            elif self.scene == "fruit":
                self.caption(
                    "Tasks 3 & 4: fruit sparkles, fruit counter and 1UP",
                    "Pop from above -> fruit -> +100, sparkle burst, count in HUD, 1UP at 5000.",
                    (255, 220, 140),
                )
            elif self.scene == "end_after":
                self.draw_end_after()
        self.draw_flash()

    # -------------------------------------------------------------------- loop
    def step(self, dt):
        self.timeline()
        self.set_keys()
        self.script_actions()
        self.game.update(dt, self.keys)
        self.detect(dt)
        self.local += 1
        self.frame += 1

    def render(self):
        self.game.draw(screen)
        self.draw_overlays()


def main():
    global screen
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("before", "after"), required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--poster", default=None)
    args = parser.parse_args()

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Bubble Bobble demo recorder")
    pygame.mixer.quit()  # deterministic, headless recording
    poster_step = 105 if args.mode == "before" else 115

    if args.mode == "before":
        module = load_module("bb_before", ROOT / "legacy" / "game_before.py")
    else:
        module = load_module("bb_after", ROOT / "game.py")

    # Seed after loading the module so Enemy/Sparkle randomness is stable.
    import random

    random.seed(20261020)

    recorder = Recorder(module, args.mode)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{WIDTH}x{HEIGHT}",
        "-r",
        str(FPS_OUT),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-metadata",
        f"title=Bubble Bobble Repair Lab - {args.mode}",
        str(out_path),
    ]
    encoder = subprocess.Popen(command, stdin=subprocess.PIPE)
    poster_saved = False
    sim_dt = 1.0 / FPS_SIM

    try:
        for step_index in range(TOTAL_STEPS):
            recorder.step(sim_dt)
            if step_index % (FPS_SIM // FPS_OUT) == 0:
                recorder.render()
                if hasattr(pygame.image, "tobytes"):
                    frame_bytes = pygame.image.tobytes(screen, "RGB")
                else:  # older pygame releases
                    frame_bytes = pygame.image.tostring(screen, "RGB")
                encoder.stdin.write(frame_bytes)
                if args.poster and not poster_saved and step_index >= poster_step:
                    pygame.image.save(screen, args.poster)
                    poster_saved = True
    finally:
        encoder.stdin.close()
        encoder.wait()

    print(f"[{args.mode}] wrote {out_path} ({SECONDS}s, {SECONDS * FPS_OUT} frames)")
    print(f"[{args.mode}] traps observed: {recorder.trap_count}")
    if args.mode == "after":
        g = recorder.game
        print(
            f"[{args.mode}] final state: score={g.score} lives={g.lives} "
            f"fruit={g.fruits_collected} bonus_awarded={g.bonus_awarded}"
        )
    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
