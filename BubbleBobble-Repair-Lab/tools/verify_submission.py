#!/usr/bin/env python3
"""Check that the submission contains the required artefacts and behaviour.

Run from the repository root:

    python tools/verify_submission.py

Exits non-zero if any check fails.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame  # noqa: E402

import game  # noqa: E402

CHECKS = []


def check(name, condition, detail=""):
    CHECKS.append((name, bool(condition), detail))


def ffprobe(path):
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_name,width,height,r_frame_rate,nb_frames",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def main():
    pygame.init()
    game.random.seed(7)
    g = game.Game()

    required = [
        "game.py",
        "legacy/game_before.py",
        "media/before.mp4",
        "media/after.mp4",
        "media/before_poster.png",
        "media/after_poster.png",
        "docs/LLM_CHAT_LOG.md",
        "docs/chat_export.json",
        "docs/REPAIR_REPORT.md",
        "SUBMISSION.md",
        "tests/test_game.py",
    ]
    for relative in required:
        path = ROOT / relative
        check(f"file exists: {relative}", path.is_file(), f"{path.stat().st_size if path.exists() else 0} bytes")

    for mode in ("before", "after"):
        path = ROOT / "media" / f"{mode}.mp4"
        if not path.exists():
            check(f"{mode}.mp4 probe", False, "missing")
            continue
        probe = ffprobe(path)
        stream = (probe.get("streams") or [{}])[0]
        duration = float((probe.get("format") or {}).get("duration", 0))
        frames = int(stream.get("nb_frames", 0))
        check(f"{mode}.mp4 is 10.0 s", abs(duration - 10.0) < 0.05, f"{duration:.3f} s")
        check(f"{mode}.mp4 has 300 frames", frames == 300, f"{frames} frames")
        check(f"{mode}.mp4 is H.264 800x600", stream.get("codec_name") == "h264" and stream.get("width") == 800 and stream.get("height") == 600, str(stream))

    source = (ROOT / "game.py").read_text()
    check("Task 1 uses squared radius", "TRAP_RADIUS * TRAP_RADIUS" in source)
    check("Task 2 implemented", "def bubble_tint" in source and "return None" in source)
    check("Task 3 implemented", "def on_fruit_collected" in source and "fruits_collected += 1" in source)
    check("Task 4 implemented", "def bonus_life_threshold" in source)
    check("bonus threshold is 5000", game.bonus_life_threshold() == 5000, str(game.bonus_life_threshold()))

    bubble = game.Bubble(100, 300, 1)
    bubble.enemy = game.Enemy(100, 400)
    bubble.life = 8.0
    fresh = game.bubble_tint(bubble)
    bubble.life = 2.0
    low = game.bubble_tint(bubble)
    check("bubble_tint returns colours", isinstance(fresh, tuple) and isinstance(low, tuple), f"{fresh} -> {low}")
    check("bubble_tint changes with life", fresh != low, f"{fresh} != {low}")

    g.enemies = []
    g.bubbles = []
    g.fruits = []
    enemy = game.Enemy(500, 570)
    g.enemies = [enemy]
    brush = game.Bubble(500, 536, 1)  # 20 px from the enemy centre
    g.trap_enemies(brush)
    check("20 px brush pass traps", brush.enemy is enemy)

    g.fruits_collected = 0
    g.sparkles = []
    fruit = game.Fruit(400, 300, 100)
    game.on_fruit_collected(fruit)
    check("fruit callback updates counter", g.fruits_collected == 1)
    check("fruit callback spawns sparkles", len(g.sparkles) >= 16, f"{len(g.sparkles)} sparkles")

    chat = (ROOT / "docs" / "LLM_CHAT_LOG.md").read_text(errors="ignore")
    check("chat log contains the user prompt", "complete this se" in chat.lower())
    check("chat log contains tool calls", "Tool call" in chat)

    # Run the unit suite as the final gate.
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    check("automated test suite passes", result.returncode == 0, result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "ok")

    pygame.quit()

    width = max(len(name) for name, _, _ in CHECKS)
    print("\nBubble Bobble submission verification\n" + "=" * 78)
    failures = 0
    for name, ok, detail in CHECKS:
        status = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        print(f"[{status}] {name:<{width}}  {detail}")
    print("=" * 78)
    print(f"{len(CHECKS) - failures}/{len(CHECKS)} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
