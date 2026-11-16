"""test_effects.py — prove effects.py works end to end.

Builds a 9.5 s sample: still A (zoom-in, glitch burst on the cut) ->
slide transition -> still B (pan L->R, distorted burst at its start),
whoosh SFX exactly on the cut, click mid-scene, waveform strip of the
narration bed, loudnorm to -16 LUFS. Then verifies:
  * ffprobe: duration, 1280x720, audio stream present
  * frames across the cut actually differ (transition is real motion)
  * audio energy spikes in the whoosh window vs the bed alone
  * blackdetect finds no black segments
Exit 0 = all checks PASS.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from effects import (  # noqa: E402
    W, H, FPS, assign_effects, check_no_repeat,
    kenburns_filter, mix_sfx_argv,
    render_still_file, run, sfx_path, waveform_overlay_argv,
    loudnorm16_argv, xfade_fragment, preflight,
)

HERE = os.path.dirname(os.path.abspath(__file__))
TEST = os.path.join(HERE, "test")
os.makedirs(TEST, exist_ok=True)
# Bed audio for the test: point EFFECTS_TEST_NARRATION at any narration WAV,
# or leave it unset and the test synthesises a 10 s tone bed with ffmpeg
# (no fixture file needed).
NARR = os.environ.get("EFFECTS_TEST_NARRATION", "")


def sh(argv, **kw):
    r = subprocess.run(argv, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(argv[:5])}...\n{r.stderr[-1500:]}")
    return r


def ffprobe(path):
    r = sh(["ffprobe", "-v", "error", "-show_entries",
            "format=duration,size:stream=codec_type,width,height,r_frame_rate",
            "-of", "json", path])
    return json.loads(r.stdout)


def frame_mean(path, t):
    out = os.path.join(TEST, f"frame-{t}.png")
    sh(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", path,
        "-frames:v", "1", out])
    from PIL import Image
    import numpy as np
    return np.asarray(Image.open(out).convert("RGB"), dtype=float)


def main():
    print("== 1. effect rotation ==")
    plan = assign_effects(12)
    assert check_no_repeat(plan), "rotation repeats an effect"
    print("   plan:", plan)

    print("== 2. test stills ==")
    from PIL import Image, ImageDraw
    for name, color, label in [("a", (40, 90, 160), "SCENE A — BOYD"),
                               ("b", (160, 60, 40), "SCENE B — BELL")]:
        img = Image.new("RGB", (W, H), color)
        d = ImageDraw.Draw(img)
        d.rectangle([80, 300, 1200, 420], fill=(255, 255, 255))
        d.text((120, 330), label, fill=(0, 0, 0))
        img.save(os.path.join(TEST, f"still-{name}.png"))
    print("   stills written")

    print("== 3. render segments ==")
    # A: 5 s zoom-in, glitch burst on the last 0.4 s (the cut)
    render_still_file(os.path.join(TEST, "still-a.png"),
                      os.path.join(TEST, "seg-a.mp4"), 5.0, move=1,
                      burst="glitch", burst_t0=4.6)
    # B: 5 s pan L->R, distorted burst at its first 0.5 s
    render_still_file(os.path.join(TEST, "still-b.png"),
                      os.path.join(TEST, "seg-b.mp4"), 5.0, move=6,
                      burst="distorted", burst_t0=0.0)
    # jitter segment (3 s, shake burst at 1.0 s) — proves jitter filter
    render_still_file(os.path.join(TEST, "still-a.png"),
                      os.path.join(TEST, "seg-jitter.mp4"), 3.0, move=2,
                      burst="jitter", burst_t0=1.0)
    print("   segments rendered")

    print("== 4. join A -> B with a slide xfade (0.5 s) ==")
    fc = ("[0:v]settb=AVTB,fps=30[v0];[1:v]settb=AVTB,fps=30[v1];"
          "[v0][v1]" + xfade_fragment("slide", 0.5, 4.5) + "[v]")
    run(["ffmpeg", "-y", "-i", os.path.join(TEST, "seg-a.mp4"),
         "-i", os.path.join(TEST, "seg-b.mp4"),
         "-filter_complex", fc, "-map", "[v]",
         "-c:v", "libx264", "-pix_fmt", "yuv420p",
         os.path.join(TEST, "video-novoice.mp4")])

    print("== 5. audio: narration bed + whoosh on cut + click mid-scene ==")
    bed = os.path.join(TEST, "bed.wav")
    if NARR and os.path.exists(NARR):
        sh(["ffmpeg", "-y", "-v", "error", "-i", NARR, "-t", "9.5",
            "-ar", "48000", "-ac", "2", bed])
    else:
        # No narration fixture: synthesise a 9.5 s tone bed (same shape
        # the level checks need — a steady bed under the SFX).
        sh(["ffmpeg", "-y", "-v", "error",
            "-f", "lavfi", "-i", "sine=frequency=220:duration=9.5",
            "-ar", "48000", "-ac", "2", bed])
    whoosh, wsynth = sfx_path("whoosh")
    click, csynth = sfx_path("click")
    print(f"   whoosh: {whoosh} (synth={wsynth})")
    print(f"   click:  {click} (synth={csynth})")
    events = [("whoosh", 4.9, -18), ("click", 2.5, -18)]
    preflight(plan, events)
    run(mix_sfx_argv(bed, events, os.path.join(TEST, "audio-mix.m4a")))

    print("== 6. mux + waveform strip + loudnorm ==")
    run(["ffmpeg", "-y", "-i", os.path.join(TEST, "video-novoice.mp4"),
         "-i", os.path.join(TEST, "audio-mix.m4a"),
         "-map", "0:v", "-map", "1:a", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k", "-shortest",
         os.path.join(TEST, "sample.mp4")])
    final = os.path.join(TEST, "sample-final.mp4")
    run(waveform_overlay_argv(os.path.join(TEST, "sample.mp4"),
                              os.path.join(TEST, "audio-mix.m4a"), final))
    normed = os.path.join(TEST, "sample-loudnorm.mp4")
    run(loudnorm16_argv(final, normed))

    print("== 7. verify ==")
    info = ffprobe(normed)
    dur = float(info["format"]["duration"])
    streams = {s["codec_type"] for s in info["streams"]}
    print(f"   duration={dur:.2f}s streams={streams}")
    assert 9.0 <= dur <= 10.0, "wrong duration"
    assert "video" in streams and "audio" in streams, "missing stream"
    v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
    assert (v["width"], v["height"]) == (1280, 720), "wrong size"

    # frames across the cut must differ (glitch burst + slide + scene change)
    import numpy as np
    f44, f49, f52 = (frame_mean(normed, t) for t in (4.4, 4.9, 5.2))
    d1 = float(np.abs(f44 - f49).mean())
    d2 = float(np.abs(f49 - f52).mean())
    print(f"   frame diff 4.4->4.9 = {d1:.1f}, 4.9->5.2 = {d2:.1f}")
    assert d1 > 5.0 and d2 > 5.0, "transition produced no visible change"

    # jitter segment: frames inside the shake burst must shift vs outside
    fj09, fj11 = (frame_mean(os.path.join(TEST, "seg-jitter.mp4"), t)
                  for t in (0.9, 1.1))
    dj = float(np.abs(fj09 - fj11).mean())
    print(f"   jitter frame diff 0.9->1.1 = {dj:.1f} (shake burst at 1.0s)")
    assert dj > 1.0, "jitter burst produced no visible shake"

    # audio: whoosh window louder than a plain bed window
    def vol(path, ss, t):
        r = sh(["ffmpeg", "-v", "info", "-ss", str(ss), "-t", str(t),
                "-i", path, "-af", "volumedetect", "-f", "null", "-"])
        for line in r.stderr.splitlines():
            if "mean_volume" in line:
                return float(line.split(":")[1].strip().split()[0])
        raise RuntimeError("no volumedetect output")
    v_whoosh = vol(normed, 4.9, 0.6)
    v_bed = vol(normed, 6.5, 0.6)
    print(f"   mean volume whoosh window={v_whoosh} dB, bed window={v_bed} dB")
    assert v_whoosh > v_bed, "whoosh not audible over bed"

    # no black frames
    r = sh(["ffmpeg", "-v", "info", "-i", normed,
            "-vf", "blackdetect=d=0.5:pix_th=0.10", "-f", "null", "-"])
    assert "black_start" not in r.stderr, "black segment found"
    print("   blackdetect: clean")

    print("\nALL CHECKS PASS")
    print(f"sample: {normed}")


if __name__ == "__main__":
    main()
