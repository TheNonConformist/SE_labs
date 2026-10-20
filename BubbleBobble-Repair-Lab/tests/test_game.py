"""Automated checks for the four lab tasks and the core game loop.

Run from the repository root:

    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

import game  # noqa: E402


class NoKeys:
    def __getitem__(self, key):
        return 0


class GameTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        game.random.seed(12345)
        self.g = game.Game()
        self.g.enemies = []
        self.g.bubbles = []
        self.g.fruits = []


class Task1TrapTests(GameTestCase):
    def test_brush_pass_at_20px_is_trapped(self):
        enemy = game.Enemy(500, 570)
        self.g.enemies = [enemy]
        # Enemy centre is (500, 556). This bubble centre is 20 px above it:
        # visually overlapping (14 px bubble + 14 px enemy half-height), and
        # far outside the old sqrt(48) ~= 6.9 px threshold.
        bubble = game.Bubble(500, 536, 1)
        bubble.age = 0.2

        self.g.trap_enemies(bubble)

        self.assertIs(bubble.enemy, enemy)
        self.assertNotIn(enemy, self.g.enemies)
        self.assertLess(bubble.pos.distance_to(enemy.center), game.TRAP_RADIUS)

    def test_clear_near_miss_outside_24px_is_not_trapped(self):
        enemy = game.Enemy(500, 570)
        self.g.enemies = [enemy]
        bubble = game.Bubble(500, 526, 1)  # 30 px above the enemy centre
        bubble.age = 0.2

        self.g.trap_enemies(bubble)

        self.assertIsNone(bubble.enemy)
        self.assertIn(enemy, self.g.enemies)

    def test_threshold_is_squared_radius(self):
        self.assertEqual(game.TRAP_RADIUS, 24)
        source = (ROOT / "game.py").read_text()
        self.assertIn("TRAP_RADIUS * TRAP_RADIUS", source)
        self.assertIn("distance_squared_to(enemy.center)", source)


class Task2BubbleTintTests(GameTestCase):
    def make_bubble(self, life, trapped=True):
        bubble = game.Bubble(300, 300, 1)
        if trapped:
            bubble.enemy = game.Enemy(300, 400)
        bubble.life = life
        bubble.age = 0.1
        return bubble

    def test_untrapped_bubble_uses_default(self):
        self.assertIsNone(game.bubble_tint(self.make_bubble(8.0, trapped=False)))

    def test_trapped_bubble_fades_from_pink_to_red(self):
        fresh = game.bubble_tint(self.make_bubble(8.0))
        mid = game.bubble_tint(self.make_bubble(4.0))
        low = game.bubble_tint(self.make_bubble(2.0))
        self.assertEqual(len(fresh), 3)
        self.assertNotEqual(fresh, mid)
        self.assertNotEqual(mid, low)
        self.assertGreater(fresh[1], low[1])  # green channel drops as it expires
        self.assertGreater(fresh[2], low[2])  # blue channel drops as it expires

    def test_flash_when_about_to_escape(self):
        bubble = self.make_bubble(0.5)
        bubble.age = 0.1  # int(0.1 * 12) % 2 == 1, the non-flash frame
        self.assertNotEqual(game.bubble_tint(bubble), (255, 250, 250))
        bubble.age = 0.2  # int(0.2 * 12) % 2 == 0, the flash frame
        self.assertEqual(game.bubble_tint(bubble), (255, 250, 250))


class Task3FruitTests(GameTestCase):
    def test_fruit_collection_updates_counter_sparkles_and_score(self):
        self.g.player.x, self.g.player.y = 400, 570
        fruit = game.Fruit(400, 552, 100)
        self.g.fruits = [fruit]

        self.g.update(1 / 60, NoKeys())

        self.assertEqual(self.g.score, 100)
        self.assertEqual(self.g.fruits_collected, 1)
        self.assertEqual(len(self.g.fruits), 0)
        self.assertGreaterEqual(len(self.g.sparkles), 16)

    def test_pickup_callback_is_reachable_with_fixed_signature(self):
        self.assertIs(game.ACTIVE_GAME, self.g)
        fruit = game.Fruit(400, 300, 250)
        game.on_fruit_collected(fruit)
        self.assertEqual(self.g.fruits_collected, 1)
        self.assertGreaterEqual(len(self.g.sparkles), 16)


class Task4BonusLifeTests(GameTestCase):
    def test_threshold_value(self):
        self.assertEqual(game.bonus_life_threshold(), 5000)

    def test_one_life_awarded_when_score_crosses_threshold(self):
        self.g.score = 4900
        self.g.lives = 3
        self.g.player.x, self.g.player.y = 400, 570
        self.g.fruits = [game.Fruit(400, 552, 100)]
        self.g.enemies = [game.Enemy(700, 210)]  # keep the level alive

        self.g.update(1 / 60, NoKeys())  # fruit: 4900 -> 5000
        self.assertEqual(self.g.score, 5000)
        self.assertEqual(self.g.lives, 3)

        self.g.update(1 / 60, NoKeys())  # crossing is recognised next frame
        self.assertEqual(self.g.lives, 4)
        self.assertEqual(self.g.bonus_awarded, 1)


class CoreLoopTests(GameTestCase):
    def test_trapped_enemy_escapes_when_timer_expires(self):
        enemy = game.Enemy(300, 400)
        bubble = game.Bubble(300, 300, 1)
        bubble.enemy = enemy
        bubble.life = 0.01
        self.g.bubbles = [bubble]

        self.g.update(1 / 60, NoKeys())

        self.assertEqual(self.g.bubbles, [])
        self.assertIn(enemy, self.g.enemies)
        self.assertEqual(enemy.speed, 130)

    def test_trapped_enemy_is_released_if_bubble_floats_off_top(self):
        enemy = game.Enemy(300, 400)
        bubble = game.Bubble(300, 0, 1)
        bubble.enemy = enemy
        bubble.life = 6.0
        bubble.pos.y = -30  # already above the screen, timer still running
        self.g.bubbles = [bubble]

        self.g.update(1 / 60, NoKeys())

        self.assertEqual(self.g.bubbles, [])
        self.assertIn(enemy, self.g.enemies)

    def test_clearing_enemies_advances_level(self):
        self.g.enemies = []
        self.g.bubbles = []
        self.g.fruits = []
        self.g.level = 1

        self.g.update(1 / 60, NoKeys())

        self.assertEqual(self.g.level, 2)
        self.assertEqual(len(self.g.enemies), min(8, 2 + 2))

    def test_draw_smoke_test(self):
        self.g.player.x, self.g.player.y = 400, 570
        self.g.fruits = [game.Fruit(500, 500, 100)]
        bubble = game.Bubble(300, 300, 1)
        bubble.enemy = game.Enemy(300, 400)
        bubble.life = 1.0
        self.g.bubbles = [bubble]
        game.on_fruit_collected(self.g.fruits[0])

        surface = pygame.Surface((game.WIDTH, game.HEIGHT))
        self.g.draw(surface)  # must not raise


if __name__ == "__main__":
    unittest.main()
