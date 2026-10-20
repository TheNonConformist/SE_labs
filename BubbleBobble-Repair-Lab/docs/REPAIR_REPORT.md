# Repair Report — Bubble Bobble Repair Lab

## 1. Scope and method

The brief asks for one bug fix and three feature implementations in a 271-line Pygame program, plus evidence that the original bug was real and the finished build works. The work was done as a short, iterative debugging session with an LLM:

1. Read the original `README.md` and `game.py`; reproduce the required behaviours mentally from the update order.
2. Keep an untouched copy of the original at `legacy/game_before.py`.
3. Make the smallest correct change for Task 1, then implement the three callbacks without changing their required signatures.
4. Add automated checks and record the two videos from the actual game loop so the evidence is reproducible.

The original repository is `SETAPESU26/26_bubbleBobble` at commit `15a6758` (“edit readme for submission reqs”). No art, audio or font assets were added; the game remains a single-file Pygame project.

---

## 2. Task 1 — the bubble-trapping bug

### Root cause

`Bubble.pos` and `Enemy.center` are `pygame.Vector2` objects. The original check was:

```python
if bubble.pos.distance_squared_to(enemy.center) < 24 * 2:
```

`distance_squared_to()` returns **d²**, but `24 * 2 = 48` is not a squared value. The effective trap radius was therefore:

```text
d < sqrt(48) ≈ 6.93 px
```

A 14 px bubble and a 28 px enemy visually touch when their centres are about `14 + 14 = 28 px` apart. The old check only fired on a near pixel-perfect overlap, exactly as the brief describes.

### Fix

```python
TRAP_RADIUS = 24

if bubble.pos.distance_squared_to(enemy.center) < TRAP_RADIUS * TRAP_RADIUS:
```

This gives `d < 24 px`: large enough to catch a clear brush pass, still smaller than the 28 px visual contact distance, so a bubble that merely comes close without touching does not steal an enemy. The constant also makes the radius explicit instead of hiding a magic number in the expression.

### Why not “just use 48”?

`48` is still an unsquared threshold and still means ~6.93 px. The left-hand side must be compared against a squared radius, i.e. `24 ** 2` (or `576`). The test `test_threshold_is_squared_radius` pins this.

### Verification

- A bubble 20 px above an enemy centre now traps it (`test_brush_pass_at_20px_is_trapped`).
- A bubble 30 px away does not (`test_clear_near_miss_outside_24px_is_not_trapped`).
- In the recorded “after” clip the same scripted jump/blow input that produced **0 traps in three attempts** in the original now traps on the first pass.

---

## 3. Task 2 — `bubble_tint(bubble)`

### Design

The function must return an `(r, g, b)` tuple or `None`. Trapped bubbles have an 8-second escape timer (`bubble.life`), so the tint is a two-segment interpolation:

| Remaining life | Colour | Meaning |
|---|---|---|
| 8.0 s → 4.0 s | soft pink `(255, 190, 230)` → amber `(255, 180, 70)` | fresh → half-way |
| 4.0 s → 0 s | amber → red `(255, 45, 45)` | half-way → about to escape |
| < 2.0 s | red, flashing white every ~0.08 s | urgent warning |

```python
def _lerp_color(start, end, amount):
    amount = max(0.0, min(1.0, amount))
    return tuple(int(start[i] + (end[i] - start[i]) * amount) for i in range(3))


def bubble_tint(bubble):
    if bubble.enemy is None:
        return None

    remaining = max(0.0, min(1.0, bubble.life / BUBBLE_LIFE))
    if remaining > 0.5:
        return _lerp_color((255, 190, 230), (255, 180, 70), (1.0 - remaining) * 2.0)
    if remaining < 0.25 and int(bubble.age * 12) % 2 == 0:
        return (255, 250, 250)
    return _lerp_color((255, 180, 70), (255, 45, 45), (0.5 - remaining) * 2.0)
```

Untrapped bubbles return `None`, so the game’s existing cyan default is preserved. The draw code also adds a small escape-timer bar under each trapped bubble, using the same `life / BUBBLE_LIFE` fraction, to make the warning readable for colour-blind players.

### Critical review

- A naive “return red when `life < 2`” only communicates two states. The interpolation gives continuous feedback and matches the brief’s “how close they are to expiring”.
- Using `pygame.time.get_ticks()` for the flash would make the deterministic recordings depend on wall-clock speed. `bubble.age` is simulation time, so the flash is reproducible frame-for-frame.
- Pygame surface alpha is not part of the required RGB return type; fading to the background colour is safer than returning an RGBA tuple.

---

## 4. Task 3 — `on_fruit_collected(fruit)`

### Design

The callback is invoked after the fruit has been scored and removed, and its return value is ignored. It only receives the `Fruit`, not the `Game`, so the running game is published through a module-level reference set in `Game.__init__`:

```python
ACTIVE_GAME = None

def on_fruit_collected(fruit):
    game = ACTIVE_GAME
    if game is None:
        return

    game.fruits_collected += 1
    for _ in range(16):
        game.sparkles.append(Sparkle(fruit.center.x, fruit.center.y))
    game.toasts.append(Toast(f"+{fruit.value}", fruit.center.x, fruit.center.y - 12, (255, 230, 120)))
    game.play_pickup_sound()
```

Effects:

1. **Sparkles** — 16 lightweight particles with random angles/speeds, gravity and a 0.35–0.75 s lifetime.
2. **HUD counter** — `reset()` initialises `fruits_collected = 0`; the HUD renders `Fruit N` next to score/lives/level.
3. **Score popup** — a floating `+100` (or combo value) using the existing font.
4. **Chime** — a two-note 880/1320 Hz wave generated at runtime with `array`, so no external `.wav` file or NumPy dependency. The sound path is wrapped in `try/except`; if the mixer is unavailable (headless recording), gameplay continues silently.

### Critical review

- Changing the callback signature to accept `game` would violate the assignment’s fixed API. A module-level `ACTIVE_GAME` is the smallest compatible bridge.
- Attaching the game to each `Fruit` was considered, but the fruit is already removed from play when the callback runs; the global avoids touching `Fruit`/`pop()` semantics.
- A particle system that allocates per frame was rejected; `Sparkle` objects are created only on pickup and removed when their timer expires.
- Fonts, mixer and display are never assumed to be initialised in tests or video generation.

---

## 5. Task 4 — `bonus_life_threshold()`

```python
BONUS_LIFE_EVERY = 5000

def bonus_life_threshold():
    return BONUS_LIFE_EVERY
```

The existing bookkeeping is kept, but the one-`if` award is replaced with a `while` loop so a large score jump cannot skip a threshold:

```python
threshold = bonus_life_threshold()
if threshold and threshold > 0:
    while self.score // threshold > self.bonus_awarded:
        self.bonus_awarded += 1
        self.lives += 1
        self.bonus_flash = 1.4
        self.toasts.append(Toast(f"1UP!  {self.bonus_awarded * threshold}", ...))
```

The loop also guards against a zero/negative threshold, which would otherwise divide by zero or award lives forever.

---

## 6. Additional polish

- HUD now shows score, lives, level, collected fruit and the reset hint.
- Combo and 1UP are shown both as floating text and as a short centred flash.
- Trapped bubbles have a timer bar; escaping enemies show an `ESCAPED!` popup.
- A trapped bubble that floats off the top of the screen now releases its enemy instead of deleting it, so a level cannot be “cleared” by losing an enemy off-screen.
- Level starts show a `LEVEL N` toast.
- The pickup chime is generated in code and cannot crash the game if audio is unavailable.

---

## 7. Verification

### Automated checks

```text
$ python -m unittest discover -s tests -v
...
Ran 14 tests in 1.073s
OK
```

Coverage:

| Area | Tests |
|---|---|
| Task 1 | 20 px brush traps; 30 px near-miss does not; source uses squared radius |
| Task 2 | untrapped returns `None`; pink/amber/red differ; expiry flash toggles |
| Task 3 | fruit collection updates score, counter and sparkles; callback signature works |
| Task 4 | threshold is 5000; one life awarded after crossing |
| Core loop | trapped enemy escapes on timer; off-screen trapped bubble releases enemy; level advances when cleared; draw smoke test with sparkles, fruit and trapped bubble |

### Video assertions

`tools/record_demo.py` prints the outcome after encoding:

```text
[before] wrote media/before.mp4 (10s, 300 frames)
[before] traps observed: 0

[after] wrote media/after.mp4 (10s, 300 frames)
[after] traps observed: 2
[after] final state: score=5050 lives=4 fruit=1 bonus_awarded=1
```

The “before” count is 0 because the original threshold misses the scripted 21 px brush pass every time. The “after” count includes the Task 1 trap and the fruit-scene trap; the final state proves the fruit was collected and the 5000-point life was awarded.

`ffprobe` on both files reports H.264, 800×600, 30 fps, 300 frames, 10.000 s.

---

## 8. Reproducing the recordings

```bash
python tools/record_demo.py --mode before --out media/before.mp4 --poster media/before_poster.png
python tools/record_demo.py --mode after  --out media/after.mp4  --poster media/after_poster.png
```

The recorder uses `SDL_VIDEODRIVER=dummy`, seeds `random` with `20261020`, steps at 60 Hz and writes every second step at 30 fps to ffmpeg. The before mode imports `legacy/game_before.py`; the after mode imports `game.py`. Captions and markers are drawn on top of the real rendered game, so the MP4s are evidence of the actual behaviour rather than mock-ups.

### Scripted brush pass

- Player starts at `x=250` on the ground; enemy at `x=500`.
- Hold → for ~1.05 s, jump at 0.60 s, blow at ~0.62 s.
- The bubble is created about 21 px above the enemy centre and crosses it while the two circles visibly overlap.
- Original: no trap (distance² ≈ 441 > 48).
- Fixed: trap (441 < 576).

---

## 9. LLM interaction and critical review

The full transcript is in [`LLM_CHAT_LOG.md`](LLM_CHAT_LOG.md); the raw session export is [`chat_export.json`](chat_export.json). The useful iterations were:

| LLM suggestion | Review decision |
|---|---|
| Change `24 * 2` to `48` | Rejected: still unsquared. Used `24 * 24` and named the constant. |
| Return red only when `life < 2` | Rejected: loses continuous feedback. Interpolated pink → amber → red and added a timer bar. |
| Use `pygame.time.get_ticks()` for the flash | Rejected: non-deterministic recordings. Used simulation-time `bubble.age`. |
| Pass the `Game` into `on_fruit_collected` | Rejected: violates the fixed callback signature. Used `ACTIVE_GAME`. |
| Use NumPy/`pygame.sndarray` for the chime | Rejected: unnecessary dependency. Generated samples with `array` and guarded the mixer. |
| Award one life with a single `if` | Rejected: a large score jump can skip thresholds. Used a `while` loop. |
| Record by hand with a screen capture tool | Rejected: hard to reproduce and may not show the 21 px brush pass reliably. Built a deterministic recorder that drives the real loop. |

---

## 10. Limitations / possible next steps

- Enemies still use simple homing/wander AI; no pathfinding.
- Bubbles that are never popped float off-screen (intended by the brief) rather than expiring.
- The pickup chime is intentionally minimal and mono; it is generated at runtime rather than authored.
- The two videos use scripted input and captions to make the 10-second evidence unambiguous; the same build is fully playable interactively with the controls above.
