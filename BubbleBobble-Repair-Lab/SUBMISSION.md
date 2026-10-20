# Submission — Bubble Bobble Repair Lab

**Student:** ___________________________  
**Student ID:** ___________________________  
**GitHub repository:** <https://github.com/TheNonConformist/26_bubbleBobble>  
**Local folder:** `26_bubbleBobble`

This submission contains exactly the three requested items, plus the source and the scripts used to reproduce the evidence.

| # | Deliverable | Direct link | Evidence |
|---|---|---|---|
| 1 | **Before** gameplay video (bug visible) | [`media/before.mp4`](media/before.mp4) | 10.000 s · 300 frames · 800×600 · H.264. Three brush passes, **0 traps**. |
| 2 | **After** gameplay video (fixed + features) | [`media/after.mp4`](media/after.mp4) | 10.000 s · 300 frames · 800×600 · H.264. Trap, tint, fruit sparkles/counter, 1UP at 5000. |
| 3 | Complete LLM chat history | [`docs/LLM_CHAT_LOG.md`](docs/LLM_CHAT_LOG.md) | Full dialogue + tool calls. Raw export: [`docs/chat_export.json`](docs/chat_export.json). |

## Task status

- [x] **Task 1** — fixed squared-distance trap threshold (`24 * 24` instead of `24 * 2`).
- [x] **Task 2** — implemented `bubble_tint(bubble)` with a life-based pink → amber → red gradient and expiry flash.
- [x] **Task 3** — implemented `on_fruit_collected(fruit)` with sparkles, HUD fruit counter, score popup and chime.
- [x] **Task 4** — implemented `bonus_life_threshold()` returning `5000` (1UP every 5000 points).
- [x] **Videos** — both 10-second MP4s are included in `media/`.
- [x] **Chat** — complete transcript and raw session export are included in `docs/`.
- [x] **Tests** — 14 automated checks pass (`python -m unittest discover -s tests -v`).

## Reproduce

```bash
python -m pip install -r requirements.txt
python game.py                               # play
python -m unittest discover -s tests -v      # verify
python tools/verify_submission.py            # check all deliverables
python tools/record_demo.py --mode before --out media/before.mp4
python tools/record_demo.py --mode after  --out media/after.mp4
```

See [`README.md`](README.md) for the full walkthrough and [`docs/REPAIR_REPORT.md`](docs/REPAIR_REPORT.md) for the technical analysis.
