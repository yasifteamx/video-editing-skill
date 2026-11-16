# effects-kit — transition effects, SFX & waveform toolkit

The effects layer on top of raw ffmpeg. Runs headless (ffmpeg 6.1+, Python
3.10+). **No paid keys, no accounts, no credentials anywhere.**

## What is installed

| Thing | What it is | Licence | Where |
|---|---|---|---|
| `xfade-easing/` | scriptituk/xfade-easing — easing curves + 40+ ported GLSL transitions for stock ffmpeg (custom expressions, no rebuild) | MIT | `xfade-easing/` |
| `sfx-kit/` | wyzowl/sfx-kit — catalogue + docs for 320 original SFX, each with sync point + level metadata | **CC0** (no attribution, commercial OK) | `sfx-kit/` (audio files NOT included — fetch from upstream) |
| `sfx/` | The 5 sounds actually used in production, copied from sfx-kit + licence | CC0 | `sfx/*.wav` |
| `effects.py` | Our own toolkit: Ken Burns grammar, burst FX, SFX mixing, waveform overlay, loudnorm, pre-flight | MIT (ours) | `effects.py` |
| `test_effects.py` | End-to-end test: 9.5 s sample + all verifications | MIT (ours) | `test_effects.py` |

## SFX inventory (`sfx/`)

| File | Duration | Source in sfx-kit | Use |
|---|---|---|---|
| `whoosh-fast-medium.wav` | 0.25 s | sounds/whooshes/whoosh-fast-medium.wav | Transition change, at −18 dB, placed 3–5 frames before the cut |
| `whoosh-fast-soft.wav` | 0.25 s | sounds/whooshes/whoosh-fast-soft.wav | Soft scene change, −20 dB |
| `click.wav` | 0.017 s | sounds/interface/click-button-medium.wav | Card / beat accent, −18 dB |
| `riser.wav` | 1.22 s | sounds/risers-and-fallers/riser-1s-strong.wav | Tension build before a reveal, −22 dB |
| `reverse-whoosh.wav` | 0.84 s | sounds/reverse-whooshes/reverse-whoosh-medium-strong.wav | Build into a cut (reverse whoosh) |

The full kit (320 sounds) is catalogued in `sfx-kit/sounds.json` (sync point,
level, when-to-use). If you need another sound, fetch it from upstream —
never download random SFX from the web without checking the licence.

**Synth fallback:** if an SFX file is missing, `effects.sfx_path()` builds
one procedurally (numpy: filtered-noise whoosh, noise-burst click, rising
sweep riser) — zero samples, zero copyright risk.

## Effects — exact commands

```python
from effects import (assign_effects, render_still_file, mix_sfx_argv,
                     waveform_overlay_argv, loudnorm16_argv,
                     xfade_fragment, xfade_easing_expr, preflight)

# 1. Assign one effect per scene change (no repeats in a row):
plan = assign_effects(n_changes)
preflight(plan, sfx_events)        # raises if an SFX file is missing

# 2. Render a still with a burst on the cut (burst lands at burst_t0):
render_still_file(image, "seg.mp4", dur=10.0, move=3,
                  burst="glitch", burst_t0=9.6)
#    burst: 'glitch' | 'jitter' | 'distorted' | None
#    move:  1..8 Ken Burns grammar

# 3. Join two segments with a transition (xfade, 0.5 s):
#    hard_cut = concat, crossfade/slide/zoom_in/zoom_out = xfade built-ins
#    filter_complex: [0:v]settb=AVTB,fps=30[v0];[1:v]settb=AVTB,fps=30[v1];
#                    [v0][v1]xfade=transition=slideleft:duration=0.5:offset=9.5[v]
#    (both inputs need settb=AVTB,fps=30 — xfade requires matching timebase)

# 4. Fancy GLSL transition (stock ffmpeg, slow — <=0.5 s only, -threads 1):
expr = xfade_easing_expr("CIRCLECROP")   # names from expr/*.txt
#    xfade=transition=custom:duration=0.5:offset=9.5:expr='<expr>'

# 5. Mix SFX exactly on the cuts:
run(mix_sfx_argv("bed.wav", [("whoosh", 9.5, -18),
                             ("click", 4.0, -18)], "audio-mix.m4a"))

# 6. Waveform strip on a full-voice island (clip voice as audio waves):
run(waveform_overlay_argv("island.mp4", "island-audio.wav", "island-waves.mp4"))
#    90 px showwaves strip, bottom of frame, white line

# 7. Delivery loudness:
run(loudnorm16_argv("video.mp4", "video-loud.mp4"))  # -16 LUFS, -1.5 dBTP
```

### Effect reference

| Effect | How it is done | When to use |
|---|---|---|
| hard_cut | plain concat | ~70% of changes |
| crossfade | `xfade=transition=fade:duration=0.5` | location / era change |
| slide | `xfade=transition=slideleft` (or slideright/smoothleft) | sideways move between scenes |
| zoom_in / zoom_out | `xfade=transition=zoomin` | push into / pull out of a scene |
| glitch | 0.4 s window cut into 0.1 s slices, constant rgbashift +14/−12/+8/0 + noise | shock reveal, arrest, DNA hit |
| jitter | crop window wobbles 9–11 Hz for 0.3 s (`scale=1292:732` first) | handheld / impact moment |
| distorted | 0.5 s slices, rgbashift ±22 + contrast 1.4 / saturation 1.8 + lagfun smear | warped flash, confusion, twist |
| (GLSL) | xfade-easing custom expr, e.g. CIRCLECROP, SWIRL | signature transitions, sparingly |
| whoosh / click / riser | SFX mixed at −18 dB on the cut | every change (whoosh), card accent (click), pre-reveal (riser) |

## Gotcha — rgbashift does NOT take expressions on this build

`rgbashift`'s rh/bh are plain integers, not expressions — even
`rh='10+5*sin(t)'` errors on ffmpeg 8.1.2. `eq` and `crop` DO accept time
expressions (verified). So glitch/distorted are implemented as **slice
passes**: the burst window is cut into 0.1 s slices, each with a different
CONSTANT rgbashift, then concatenated (`effects._apply_burst_slices`).

## Test results (`python3 test_effects.py`)

ALL CHECKS PASS. Sample: 9.63 s, 1280×720.

- Effect rotation: 12 changes, no repeats in a row
- Segments rendered: zoom-in + glitch burst, pan + distorted burst, jitter
- Slide xfade join (0.5 s); frame diff across the cut: 57.0 / 29.0 (mean abs
  pixel diff — real motion, not a static frame)
- Jitter burst frame diff 0.9→1.1 s = 2.7 (visible shake)
- Audio: whoosh window mean −17.0 dB vs bed window −18.2 dB (whoosh audible
  exactly on the cut, mixed at −18 dB)
- Waveform strip + loudnorm: final **−15.55 LUFS, true peak −1.95 dBTP**
  (target −16 LUFS / −1.5 dBTP)
- blackdetect: clean, no black segments
- Custom GLSL xfade (CIRCLECROP expr, `-threads 1`): renders, 9.5 s
