# NOTICE — Attribution

This repo combines our own original work with third-party tools. Nothing here
re-licences anyone else's work. Each vendored component keeps its original
licence (copied into its folder where one was supplied) and its original
copyright. Our MIT licence in the repo root (`LICENSE`) covers **our original
work only**.

## Our original work (MIT, this repo)

- The unified skill: `SKILL.md`
- The effects toolkit: `skills/effects-kit/effects.py`, `test_effects.py`
- Glue scripts: `scripts/probe.py`
- Documentation: `README.md`, this `NOTICE.md`, `skills/effects-kit/README.md`

## Vendored components

| Component | Source | Author | Licence | Licence file in repo? |
|---|---|---|---|---|
| `skills/ffmpeg-skill/` | https://github.com/kajisho5/ffmpeg-skill | kajisho5 (2026) | MIT | Yes (`LICENSE`) |
| `skills/video-production-skill/` | https://github.com/Aaryan-Kapoor/video-production-skill | Aaryan Kapoor (2026), v0.2.0 | MIT | Yes (`LICENSE`) |
| `skills/effects-kit/xfade-easing/` | https://github.com/scriptituk/xfade-easing | scriptituk | MIT | Yes (`LICENSE`) |
| `skills/effects-kit/sfx-kit/` (catalogue + docs only) | https://github.com/wyzowl/sfx-kit | Wyzowl | CC0 1.0 | Yes (`LICENSE`) |
| `skills/effects-kit/sfx/` (5 curated sounds) | https://github.com/wyzowl/sfx-kit | Wyzowl | CC0 1.0 | Yes (`LICENSE-CC0.txt`) |

Notes:

- Exclusions (deliberate, noted in `skills/effects-kit/VENDORED.md`):
  ffmpeg-skill's `.git` history (23 MB) and demo media (`docs/demos/*.gif`,
  `demos/footage/*.mp4`, `assets/demo.gif`, `site/media/*`); the
  video-production-skill example videos (43 MB, never copied); xfade-easing's
  `assets/` demo media (121 MB); sfx-kit's `sounds/` audio files (65 MB) —
  the catalogue (`sounds.json`) is included so you can pick a sound and fetch
  it from upstream. The scripts, references, contracts, tests and docs are
  all intact.
- If you fork this repo, fetch any excluded media from upstream; do not
  re-upload it without checking its licence.
