# Vendored: ffmpeg-skill

- **Source:** https://github.com/kajisho5/ffmpeg-skill — by kajisho5.
- **Licence:** MIT — Copyright (c) 2026 kajisho5. Original `LICENSE` file kept in this folder. No re-licensing: this component stays MIT under its original author.
- **What it is:** 42 local ffmpeg scripts (cut, join, captions, overlays, silence removal, sync, loudness, exports, checks, look/scenes, graphics, B-roll, multicam). Needs ffmpeg 6.1+ and Python 3.10+. `SKILL.md` is the router: run `python3 scripts/<name>.py`, plan with `--dry-run --json`, then run, then verify.
- **Kept/changed:** vendored as-is except:
  - `.git/` excluded (23 MB of history — not needed in a vendor copy).
  - `__pycache__/` excluded.
  - Demo media excluded to keep the repo lean: `docs/demos/*.gif` (~14 MB),
    `demos/footage/*.mp4`, `assets/demo.gif`, and `site/media/*` (demo videos).
    The scripts, references, contract, tests and docs are all intact. If you
    want the demos, clone the upstream repo.
- **How we use it in this repo:** see the root `SKILL.md` "Edit with ffmpeg-skill" section and `scripts/probe.py`.
