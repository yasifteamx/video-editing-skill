# Vendored: effects-kit

Our own effects layer, assembled from two upstream toolkits plus our own code.

## Contents

- `effects.py` + `test_effects.py` — **ours (MIT, this repo).** Ken Burns
  grammar (8 moves), burst FX (glitch, jitter, distorted) as 0.1s
  constant-shift slices, SFX mixing exactly on cuts, waveform overlay,
  loudnorm to −16 LUFS, pre-flight checks. Test: 9.5s sample, all checks
  pass (final −15.55 LUFS, true peak −1.95 dBTP).
- `xfade-easing/` — **MIT, scriptituk** — https://github.com/scriptituk/xfade-easing.
  Easing curves + 40+ ported GLSL transitions as custom expressions for
  stock ffmpeg's `xfade`. Original `LICENSE` kept. Excluded: `assets/`
  demo media (121 MB) — fetch from upstream if you want the demos.
- `sfx-kit/` — **CC0 1.0, Wyzowl** — https://github.com/wyzowl/sfx-kit.
  Catalogue + docs for 320 original SFX (WAV 48 kHz 24-bit, each with sync
  point + level metadata in `sounds.json`). Original `LICENSE` kept.
  Excluded: `sounds/` audio files (65 MB) — fetch from upstream (or its
  Hugging Face mirror) if you need more than the 5 curated sounds below.
- `sfx/` — 5 sounds copied from sfx-kit and actually used in production,
  with `LICENSE-CC0.txt`: whoosh-fast-medium, whoosh-fast-soft, click,
  riser, reverse-whoosh.

## Gotcha (verified on ffmpeg 8.1.2)

`rgbashift` does NOT accept expressions on this build — its rh/bh are plain
integers, not expressions. So glitch/distorted are implemented as slice
passes: the 0.4–0.5s burst window is cut into 0.1s slices, each with a
different CONSTANT rgbashift, then concatenated
(`effects._apply_burst_slices`). Same visible result, no expressions.

## How we use it in this repo

See the root `SKILL.md` "Effects kit" section and `skills/effects-kit/README.md`.
Effect rotation: one effect per scene change, no repeats in a row
(`effects.assign_effects`). SFX sit exactly on the cut instant, never under
the voice; levels are measured in the final mix.
