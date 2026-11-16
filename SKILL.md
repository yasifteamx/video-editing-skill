---
name: video-editing-skill
description: Edit a long-form faceless documentary video to a top-level standard — fast trailer-style hook, hard cuts, scene-matched real visuals, full-voice reference clips, real music low, competitor-style subtitles, and a measured verify pass before handover. Use when the user asks to edit, fix, rebuild or check a video, or to cut a hook, trailer or Short from long-form footage. Local ffmpeg only — no paid keys, no cloud render.
---

# Video Editing Skill — one skill for a top-level edit

This skill edits a finished narration + visuals into a video that holds
attention. It is the single entry point; the vendored tools in `skills/` do
the specialist work. Route to them, don't re-implement them.

## What good looks like

- **The first 1–5 minutes are the trailer.** Fast cuts every 2–4 seconds,
  trailer-style motion graphics with big text, glitch/distorted effects, zoom
  punch-ins. No slow Ken Burns stills in the hook. The hook must grab in the
  first 5 seconds. Check the first 2 minutes for pace and picture before
  handing the video over, and name the exact timestamps you checked.
- **Pacing throughout:** ~3–3.5s average shot, ~16–18 cuts/min, no still held
  longer than 5s. One real cinematic clip with slow push-in, handheld feel
  and film grain every 3–4 minutes, and one in the hook.
- **Hard cuts, no whoosh.** Competitor analysis (528 cuts, avg 3.34s) found
  dry hard cuts throughout — no whooshes, no clicks on cuts, only short low
  booms (≤0.3s) at section beats. So: hard cuts ~99%; a soft click on at most
  ~15% of cuts as a ≤0.05s transient; one low boom at each chapter boundary;
  one red flash (~0.5s) at the hook pivot only. A whoosh that runs under
  narration sounds odd — SFX sit exactly on the cut instant, never under the
  voice. Measure SFX levels in the final mix; a gain value in a build script
  is not a level in the mix.
- **Reference clips are full-voice islands.** When a real clip plays, the
  narrator goes COMPLETELY SILENT for the whole clip and the clip plays at
  full volume. Never talk over a reference clip; never duck its audio under
  narration. Zero burned-in captions inside islands. Verify island sync
  against the AUDIO, never against a plan document: a plan once listed every
  island 10s late and the build trusted it. Check each island with Whisper
  (clip voice audible, narrator silent) AND by looking at a frame inside it.
- **Music is a real track, low.** From NCS or the YouTube Audio Library
  first (free, credit if the licence needs it); a CC-BY composer-library
  track is acceptable only as a recorded exception. Mix ~12–13 dB under
  narration, a touch louder in the hook, silent inside islands. **Never use
  brown/pink noise as a bed** — brown noise low-passed at 400 Hz sounds
  exactly like wind. A bad bed is worse than no bed.
- **Images match the exact second.** Every image must illustrate the exact
  thing being said at that second — no generic repeats, no 4–5 images
  looping. The image count follows the story, never the other way round.
  Look at every image you choose; never trust a filename. Places, objects
  and documents only — no face, no child, no blood.
- **Motion graphics:** hook opener, one intro card per case/section, method
  diagram, timeline, recap, end card — scale-in with a brief glitch head,
  not static fades.
- **Subtitles:** competitor-style burned-in captions, current word
  highlighted yellow, max 7 words/line. Generate from a Whisper
  transcription of the finished narration and fix mis-hearings of names.

## Edit with ffmpeg-skill

`skills/ffmpeg-skill/` is the tool bench: 42 scripts, `python3
skills/ffmpeg-skill/scripts/<name>.py`. Needs ffmpeg 6.1+ and Python 3.10+.
Workflow from its `SKILL.md`: probe first (`probe.py`), plan with
`--dry-run --json`, then run, then verify with `check.py`. Trust `--json`
numbers, not summary lines. Never overwrite a source file.

| Job | Script |
|---|---|
| What is in this file? | `probe.py in.mp4 [--analyze]` |
| Cut / trim / keep parts | `cut.py in.mp4 --start 1:20 --end 2:05` (or `--segments`, `--remove`) |
| Join clips, with crossfade | `join.py a.mp4 b.mp4 --transition fade --duration 0.5` |
| Remove pauses / jump cuts | `silence.py in.mp4` (`--speech-aware`) |
| Speed up / slow-mo / freeze | `fit.py` / `speedramp.py` / `freeze.py` |
| Reframe vertical / square | `fit.py in.mp4 --aspect 9:16 --fit pad` (or `crop`, `blur`) |
| Captions, karaoke, pop | `caption.py in.mp4 --srt subs.srt` (`--transcribe --animate pop --karaoke`) |
| Titles, lower thirds, hook cards | `graphics.py` (`--template lower-third` / `hook` / `sticker` / `meme`); `overlay.py` for logo/text/PiP |
| Music under talking, ducking | `audio.py in.mp4 --music bed.mp3 --duck --fade-out 3` |
| Loudness to -16 LUFS | `loudness.py in.mp4` (check with `--versions streaming,ebu-r128`) |
| Clean audio, denoise, gate | `audio.py in.mp4 --voice` / `--denoise` / `--compress` / `--limit` / `--gate` |
| Colour, LUT, HDR→SDR | `color.py in.mp4 --lut grade.cube` / `--to-sdr` / `--correct` |
| Stabilize / denoise video | `stabilize.py` / `denoise.py` |
| B-roll over narration | `broll.py talk.mp4 --insert product.mp4 --at 12 --end 16 --audio b\|mix` |
| Chapters / metadata | `metadata.py ep.mp4 --chapters chapters.txt` |
| Is this OK to upload? | `check.py final.mp4 --platform youtube` |
| Look at the result | `look.py out.mp4 --tiles 3x2` — view the PNG, name what you see |
| Highlights from a long video | `scenes.py long.mp4 --highlights 6 --target 60 --edl picks.txt` |
| Shorts / Reels export | `render.py --template reels in.mp4 --cues cues.txt` |
| Waveform video | `waveform.py ep.wav -o waveform.mp4` |

Quick probe from the repo root (a tested wrapper around the vendored probe):

```bash
python3 scripts/probe.py <video-file> [--json]
```

## Effects kit

`skills/effects-kit/` is the effects layer on top of raw ffmpeg — see its
`README.md` for the full reference. In short:

- `effects.py` — Ken Burns grammar (8 moves), burst FX (glitch, jitter,
  distorted) as 0.1s constant-shift slices (this ffmpeg build's `rgbashift`
  does NOT accept expressions), SFX mixing exactly on cuts, waveform
  overlay, loudnorm to −16 LUFS, pre-flight checks.
- `xfade-easing/` — 40+ ported GLSL transitions + easing curves as custom
  expressions for stock ffmpeg's `xfade` (MIT, scriptituk). Use sparingly,
  ≤0.5s, `-threads 1` — GLSL transitions are slow.
- `sfx/` — 5 curated CC0 sounds actually used in production (whoosh, soft
  whoosh, click, riser, reverse whoosh). The full 320-sound kit's catalogue
  is in `sfx-kit/` (`sounds.json` with sync point + level metadata); the
  audio files themselves are NOT in this repo — fetch them from the upstream
  wyzowl/sfx-kit (CC0) if you need more than the 5 curated sounds.
- `sfx-kit/` — catalogue + docs for the full kit (see above).

Effect rotation: one effect per scene change, no repeats in a row —
`assign_effects(n)` in `effects.py`. Default mix: hard cut ~70% of changes,
the rest crossfade / slide / zoom / glitch / jitter / distorted, varied.

## Production workflow (jobs, QC, archive)

`skills/video-production-skill/` gives the job-workspace discipline:

```
jobs/<YYYY-MM-DD-HHMM-slug>/
├── assets/      # durable source figures, crops, screenshots
├── audio/       # narration segments + final voiceover
├── frames/      # QC preview frames
├── src/         # build scripts, storyboard, segments.json
├── renders/     # intermediate renders
├── exports/     # final videos for this job
├── logs/
└── manifest.json
```

Initialise a job with
`skills/video-production-skill/skills/video-production/scripts/init_video_job.py`,
archive every finished MP4, and keep a `manifest.json` per job. Its TTS
default is Kokoro and its visuals default is Manim — both optional; the
core rule still applies: treat a video request as a finished deliverable,
not a plan.

## Verify before you hand it over

- **Duration:** ffprobe — check against the target the job set (a long-form
  documentary is usually 34–40 min; longer OK, shorter is a miss).
- **Frames:** extract and LOOK at frames every ~60s plus every cut in the
  first 5 minutes. Every frame must match the narration at that second. No
  black frames (blackdetect), no blurry/generic/era-wrong images.
- **Audio:** loudness ~−16 LUFS measured; SFX only at cuts (short
  transients); music bed present but low; narration clear; islands audible
  with narrator silent; no wind/noise; no dead air >1.5s except natural
  pauses.
- **Words:** Whisper-check the finished file — narration words match the
  script, no narration inside islands, clip voices audible in islands.
- **Subtitles:** SRT audit — 0 cues inside islands; karaoke verified
  visually.
- **Pack:** MP4 + thumbnail + SRT + upload pack, sizes verified byte-for-byte
  against local files.

## Honesty rule

Never call work perfect unless it has been verified. Report measured
numbers, not adjectives, and disclose remaining flaws before the viewer
finds them. If a check failed, say so plainly and say what is missing — do
not paper over the gap.
