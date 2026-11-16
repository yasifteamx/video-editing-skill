# Video Editing Skill

One skill for editing a long-form faceless documentary video to a top-level
standard — trailer-style hook, hard cuts, scene-matched real visuals,
full-voice reference clips, real music low, competitor-style subtitles, and
a measured verify pass before handover. Local ffmpeg only: no paid keys, no
cloud render.

## What is in here

| Path | What it is |
|---|---|
| `SKILL.md` | **The unified skill — start here.** The edit standard, the ffmpeg tool routing, the effects kit, the job workflow, the verify checklist. |
| `skills/ffmpeg-skill/` | 42 local ffmpeg scripts — cut, captions, overlays, loudness, exports, checks (MIT, kajisho5). |
| `skills/video-production-skill/` | End-to-end production workflow: job workspace, QC, archive (MIT, Aaryan Kapoor, v0.2.0). |
| `skills/effects-kit/` | Our effects layer: Ken Burns grammar + burst FX (`effects.py`), 40+ GLSL xfade transitions (MIT, scriptituk), 5 curated CC0 SFX + the full 320-sound kit catalogue (CC0, Wyzowl). |
| `scripts/probe.py` | Tested wrapper around the vendored ffmpeg probe. |
| `NOTICE.md` | Attribution for every vendored component — read it before reusing anything. |

## Quick start

```bash
git clone https://github.com/<you>/video-editing-skill.git
cd video-editing-skill

# Requirements
ffmpeg --version   # 6.1+ (we use 8.1.2)
python3 --version  # 3.10+

# Probe a finished video (tests the vendored ffmpeg-skill)
python3 scripts/probe.py path/to/video.mp4 --json
```

Then read `SKILL.md` and follow it: hook as a trailer, hard cuts, islands
silent, music low and real, verify by looking at frames and measuring audio.

## The edit in one paragraph

The first 1–5 minutes are the trailer — cuts every 2–4 seconds, big text,
glitch and zoom punch-ins, no slow stills. After that, ~3.5s average shots
and a real cinematic clip every 3–4 minutes. Hard cuts ~99%, a soft click on
at most ~15% of cuts, one low boom per chapter, one red flash at the hook
pivot — never a whoosh under narration. When a real reference clip plays,
the narrator goes completely silent and the clip plays at full volume.
Music is a real track (NCS / YouTube Audio Library first), ~12–13 dB under
the narration, silent inside islands — never brown or pink noise as a bed.
Verify by looking at frames and measuring audio, never by trusting a build
script's summary.

## What it does NOT do

- **No paid keys required.** Editing is local ffmpeg; SFX default to a
  local CC0 kit.
- **No Premiere on Linux.** This skill is ffmpeg-only by design.
- **No YouTube research, scripting or narration.** That is the companion
  skill — see `youtube-research-skill` — and a channel-specific production
  skill that builds on this one.
- **No magic.** The skill measures and reports; it does not decide what is
  good. A video is done when the checks in `SKILL.md` pass and a human has
  looked at the frames — not before.
- **No re-licensing of other people's work.** Every vendored component keeps
  its original licence and attribution — see `NOTICE.md`. Only our own
  original work is MIT under this repo's `LICENSE`.

## Honesty rule

Never call work perfect unless it has been verified. Report measured numbers,
not adjectives, and disclose remaining flaws before the viewer finds them.

## Licence

Our original work (the unified skill, the effects toolkit, the glue scripts,
this README) is MIT — see `LICENSE`. Vendored components keep their own
licences — see `NOTICE.md` and each `skills/*/VENDORED.md`.
