# Vendored: video-production-skill

- **Source:** https://github.com/Aaryan-Kapoor/video-production-skill — by Aaryan Kapoor, v0.2.0.
- **Licence:** MIT — Copyright (c) 2026 Aaryan Kapoor. Original `LICENSE` file kept in this folder.
- **What it is:** end-to-end narrated-video production workflow: job workspace (`jobs/<date>-<slug>/` with assets/audio/frames/src/renders/exports/logs/manifest.json), segmented narration, TTS, Manim/ffmpeg visuals, timing sync, render + mux, QC frames/audio, archive, optional hosting. Scripts in `skills/video-production/scripts/` (`init_video_job.py`, `archive_video.py`, `host_video.py`, `synth_kokoro.py`). Needs Python 3.10+ and ffmpeg; Manim and Kokoro TTS are optional.
- **Kept/changed:** vendored unchanged (no `.git` was present in the local copy). The 43 MB of example videos from the upstream repo were deliberately never copied into our local install, so they are not here either — see `docs/` in the upstream repo if you want them.
- **How we use it in this repo:** the job-workspace layout and QC discipline. Its TTS default is Kokoro and its visuals default is Manim — both optional; this repo's pipeline uses ffmpeg for the edit. See the root `SKILL.md`.
