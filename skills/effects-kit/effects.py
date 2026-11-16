"""effects.py — transition / SFX / waveform toolkit for long-form
documentary editing.

FFmpeg-native, headless, no paid keys, no accounts.
Built for the one-effect-on-EVERY-pic/clip-change rule: one effect on every
scene change, SFX exactly on the change, reference clips as full-voice
islands (narrator silent, clip at full volume).

Effects (8, rotated, never the same twice in a row):
  hard_cut, crossfade, slide, zoom_in, zoom_out, glitch, jitter, distorted
SFX (CC0, local files in sfx/; synthesized fallback if a file is missing):
  whoosh (transition), click (beat / card), riser (tension build)
Extras:
  waveform_overlay — showwaves of the clip/narration audio, bottom strip
  loudnorm16       — EBU R128 to -16 LUFS / -1.5 dBTP (our delivery level)

Usage (see README.md and test_effects.py):
  from effects import assign_effects, render_still, mix_sfx, ...
  ffmpeg calls are built as argument lists; run them with subprocess.
  `ffmpeg` 8.1.2 on this VM has xfade, zoompan, rgbashift, lagfun, tmix,
  displace, showwaves, loudnorm, ass/subtitles, drawtext — all verified.
"""

import math
import os
import subprocess
import wave

import numpy as np

W, H, FPS = 1280, 720, 30
SFX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx")

# ---------------------------------------------------------------- effects
EFFECTS = [
    "hard_cut",    # plain cut (70% of changes are cuts per Vidrush rule)
    "crossfade",   # 0.5 s dissolve — location / era changes
    "slide",       # sideways slide (xfade slideleft/smoothleft)
    "zoom_in",     # xfade zoomin into next scene
    "zoom_out",    # xfade zoomin reversed (zoom out of previous scene)
    "glitch",      # RGB-split + noise burst + frame stutter on the cut
    "jitter",      # handheld shake burst on the cut
    "distorted",   # heavy RGB-split + contrast/saturation + lag smear
]

# xfade built-ins used by slide / zoom_in / zoom_out / crossfade.
XFADE_MAP = {
    "crossfade": "fade",
    "slide": "slideleft",      # sideways; alternate with slideright via param
    "zoom_in": "zoomin",
    "zoom_out": "zoomin",      # same transition, applied in reverse order
}

# SFX files we expect in sfx/ (CC0, see README.md for sources).
# Copied from wyzowl/sfx-kit (CC0, no attribution needed).
# Each entry: (filename, default level in dB, role)
SFX = {
    "whoosh": ("whoosh-fast-medium.wav", -18, "every transition change"),
    "whoosh_soft": ("whoosh-fast-soft.wav", -20, "soft scene change"),
    "click": ("click.wav", -18, "card / beat accent"),
    "riser": ("riser.wav", -22, "tension build before a reveal"),
}
SFX_LEVEL_DB = -18  # plan §5: SFX mixed at -18 dB exactly on each change


def assign_effects(n, seed=0):
    """Return a list of n effect names, no effect twice in a row.

    Deterministic rotation (seed offsets the start) so a build is
    reproducible; the builder may shuffle with a fixed seed instead.
    Hard cuts are weighted ~70% per the Vidrush 70/30 rule.
    """
    order = ["hard_cut", "glitch", "crossfade", "slide", "hard_cut",
             "zoom_in", "jitter", "hard_cut", "distorted", "zoom_out",
             "hard_cut", "slide", "glitch", "hard_cut", "crossfade"]
    out = []
    for i in range(n):
        out.append(order[(seed + i) % len(order)])
    return out


def check_no_repeat(seq):
    """True if no effect repeats twice in a row (plan pre-flight rule)."""
    return all(seq[i] != seq[i - 1] for i in range(1, len(seq)))


# ------------------------------------------------------- Ken Burns moves
# The 8-move grammar from VIDEO4-PLAN.md §3, as zoompan filter strings.
# zoompan works on a still: d=frames, s=output size, fps=30.
def kenburns_filter(move, dur):
    """zoompan filter for one still, dur seconds, move in 1..8."""
    frames = int(round(dur * FPS))
    z0, z1 = 1.00, 1.20
    # zoompan zooms around the window (x,y) — expressions use 'in'/'on'.
    if move == 1:   # zoom-in centre
        return (f"zoompan=z='min(zoom+0.0015,{z1})':x='iw/2-(iw/zoom/2)':"
                f"y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}")
    if move == 2:   # zoom-out centre
        return (f"zoompan=z='if(eq(on,1),{z1},max(zoom-0.0015,{z0}))':"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={frames}:s={W}x{H}:fps={FPS}")
    if move == 3:   # zoom-in top-left
        return (f"zoompan=z='min(zoom+0.0015,{z1})':x='0':y='0':"
                f"d={frames}:s={W}x{H}:fps={FPS}")
    if move == 4:   # zoom-in bottom-right
        return (f"zoompan=z='min(zoom+0.0015,{z1})':x='iw-iw/zoom':"
                f"y='ih-ih/zoom':d={frames}:s={W}x{H}:fps={FPS}")
    if move == 5:   # zoom-out top-right
        return (f"zoompan=z='if(eq(on,1),{z1},max(zoom-0.0015,{z0}))':"
                f"x='iw-iw/zoom':y='0':d={frames}:s={W}x{H}:fps={FPS}")
    if move == 6:   # pan left->right, constant zoom 1.15
        return (f"zoompan=z=1.15:x='(iw-iw/zoom)*on/{frames}':"
                f"y='(ih-ih/zoom)/2':d={frames}:s={W}x{H}:fps={FPS}")
    if move == 7:   # pan right->left
        return (f"zoompan=z=1.15:x='(iw-iw/zoom)*(1-on/{frames})':"
                f"y='(ih-ih/zoom)/2':d={frames}:s={W}x{H}:fps={FPS}")
    # 8: drift down
    return (f"zoompan=z=1.12:x='(iw-iw/zoom)/2':"
            f"y='(ih-ih/zoom)*on/{frames}':d={frames}:s={W}x{H}:fps={FPS}")


# ------------------------------------------------- per-segment burst FX
# These are applied to a rendered still/clip segment. `t` is local time
# in the segment; the burst window is [t0, t0+dur] seconds.

def _burst_slices(t0, dur, total):
    """Slice boundaries for a burst window [t0, t0+dur] inside a segment
    of length `total`. Returns list of (start, end)."""
    cuts = sorted({0.0, total, max(0.0, t0), min(total, t0 + dur)})
    # subdivide the burst window into 0.1 s slices for the channel-shift
    inner = []
    t = max(0.0, t0)
    end = min(total, t0 + dur)
    while t < end - 1e-6:
        inner.append(round(t, 3))
        t += 0.1
    inner.append(round(end, 3))
    cuts = sorted(set(cuts) | set(inner))
    return [(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1)
            if cuts[i + 1] - cuts[i] > 1e-6]


def _slice_fx(kind, idx_in_burst):
    """Per-slice video filters for a burst slice (constant values only —
    this ffmpeg build's rgbashift does NOT accept expressions)."""
    if kind == "glitch":
        rh = [14, -12, 8, 0][idx_in_burst % 4]
        noise = ",noise=alls=40:allf=t" if idx_in_burst in (1, 2) else ""
        return f"rgbashift=rh={rh}:bh={-rh}{noise},format=yuv420p"
    # distorted
    rh = [22, -22, 14, 0][idx_in_burst % 4]
    return (f"rgbashift=rh={rh}:bh={-rh},"
            f"eq=contrast=1.4:saturation=1.8,lagfun=decay=0.85,"
            f"format=yuv420p")


def _apply_burst_slices(src, out, kind, t0, dur=0.4):
    """Re-render `src` with a glitch/distorted burst at [t0, t0+dur].

    The burst window is cut into 0.1 s slices, each with a different
    CONSTANT rgbashift (this build rejects expressions in rgbashift),
    then concatenated. Outside the window the picture is untouched.
    """
    import json
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", src], capture_output=True, text=True)
    total = float(json.loads(probe.stdout)["format"]["duration"])
    slices = _burst_slices(t0, dur, total)
    fc, labels = [], []
    burst_start, burst_end = max(0.0, t0), min(total, t0 + dur)
    bi = 0
    for i, (s, e) in enumerate(slices):
        in_burst = s >= burst_start - 1e-6 and s < burst_end - 1e-6
        if in_burst:
            fx = _slice_fx(kind, bi)
            bi += 1
        else:
            fx = "format=yuv420p"
        fc.append(f"[0:v]trim=start={s:.3f}:end={e:.3f},"
                  f"setpts=PTS-STARTPTS,{fx}[s{i}]")
        labels.append(f"[s{i}]")
    fc.append(f"{''.join(labels)}concat=n={len(slices)}:v=1:a=0[v]")
    argv = ["ffmpeg", "-y", "-i", src, "-filter_complex", ";".join(fc),
            "-map", "[v]", "-r", str(FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", out]
    run(argv)
    return out


def jitter_filter(t0, dur=0.3, amp=6):
    """Handheld shake burst: crop window wobbles with sin/cos at 9-11 Hz.

    crop DOES accept time expressions on this build (verified), so the
    burst is gated inline with between(t,...). Input is scaled slightly
    larger first (1292x732) so the crop never runs out of frame.
    """
    g = f"between(t,{t0},{t0 + dur})"
    return (
        f"scale=1292:732,"
        f"crop={W}:{H}:x='6+if({g},{amp}*sin(2*PI*t*11),0)':"
        f"y='6+if({g},{amp}*cos(2*PI*t*9),0)'"
    )


def grade_filter():
    """House grade (VIDEO4-PLAN.md §3): muted archival look + grain + vignette."""
    return (f"eq=saturation=0.95:contrast=1.04,"
            f"noise=alls=6:allf=t,"
            f"vignette=PI/5")


def render_still(image, out, dur, move=1, burst=None, burst_t0=0.0):
    """Render one still as a video segment.

    burst: None | 'glitch' | 'jitter' | 'distorted' — applied at burst_t0
    (seconds into the segment, usually dur-0.4 so it lands on the cut).
    glitch/distorted are applied as a slice pass (constant rgbashift per
    0.1 s slice — this build rejects expressions in rgbashift); jitter
    is an inline crop wobble (crop accepts time expressions).
    Returns the ffmpeg argv list for the first pass (caller runs it);
    for glitch/distorted the caller must then run _apply_burst_slices.
    Use render_still_file() to do the whole thing in one call.
    """
    vf = [kenburns_filter(move, dur)]
    if burst == "jitter":
        vf.append(jitter_filter(burst_t0))
    vf.append("format=yuv420p")
    vf.append(grade_filter())
    return ["ffmpeg", "-y", "-loop", "1", "-i", image,
            "-vf", ",".join(vf),
            "-t", str(dur), "-r", str(FPS),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", out]


def render_still_file(image, out, dur, move=1, burst=None, burst_t0=0.0):
    """Render one still segment to `out`, including any burst effect."""
    tmp = out + ".clean.mp4"
    run(render_still(image, tmp, dur, move=move,
                     burst=burst if burst == "jitter" else None,
                     burst_t0=burst_t0))
    if burst in ("glitch", "distorted"):
        _apply_burst_slices(tmp, out, burst, burst_t0)
        os.remove(tmp)
    else:
        os.replace(tmp, out)
    return out


# ------------------------------------------------------------- transitions
def xfade_fragment(transition, duration=0.5, offset=0.0):
    """xfade filter fragment joining two same-size 30fps inputs.

    transition: one of XFADE_MAP keys (or a raw xfade name).
    Note: both inputs need settb=AVTB,fps=30 first (tested in V3/V4).
    """
    name = XFADE_MAP.get(transition, transition)
    return f"xfade=transition={name}:duration={duration}:offset={offset}"


def xfade_easing_expr(transition, easing="easeInOutCubic"):
    """Custom GLSL-transition expression from xfade-easing (if cloned).

    Reads the pre-generated `expr/eased-transitions-yuv420p-inline.txt`
    (name line followed by expression line). Returns the expression
    string, or None if the repo/transition is not present.
    Usage: xfade=transition=custom:duration=D:offset=O:expr='<expr>'.
    Custom expressions are slow (per-pixel eval) — use only for short
    (<=0.5 s) transitions.
    """
    repo = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "xfade-easing")
    path = os.path.join(repo, "expr",
                        "eased-transitions-yuv420p-inline.txt")
    if not os.path.exists(path):
        return None
    want = transition.upper()
    with open(path) as f:
        lines = [ln.rstrip("\n") for ln in f]
    for i, ln in enumerate(lines):
        if ln.strip() == want and i + 1 < len(lines):
            return lines[i + 1].strip()
    return None


# ------------------------------------------------------------------- SFX
def _write_wav(path, samples, sr=48000):
    samples = np.clip(samples, -1.0, 1.0)
    pcm = (samples * 32767).astype(np.int16)
    stereo = np.repeat(pcm[:, None], 2, axis=1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(stereo.tobytes())
    return path


def synth_whoosh(path, dur=0.6, sr=48000, f0=300.0, f1=3200.0):
    """Procedural whoosh: white noise through a time-varying one-pole
    low-pass whose cutoff sweeps f0 -> f1, with a fast attack / long
    decay envelope. Zero copyright risk (no samples at all)."""
    n = int(dur * sr)
    rng = np.random.default_rng(7)
    x = rng.standard_normal(n)
    # one-pole low-pass with sweeping coefficient
    alpha = np.linspace(2 * math.pi * f0 / sr, 2 * math.pi * f1 / sr, n)
    alpha = np.clip(alpha, 0.001, 0.9)
    y = np.zeros(n)
    acc = 0.0
    for i in range(n):
        acc += alpha[i] * (x[i] - acc)
        y[i] = acc
    # envelope: quick rise, exponential fall
    t = np.arange(n) / sr
    env = np.minimum(t / 0.08, 1.0) * np.exp(-3.0 * t / dur)
    y = y * env
    y /= (np.max(np.abs(y)) + 1e-9)
    return _write_wav(path, y * 0.9, sr)


def synth_click(path, dur=0.08, sr=48000, freq=1800.0):
    """Procedural click: 2 ms noise burst + short sine blip, fast decay."""
    n = int(dur * sr)
    rng = np.random.default_rng(3)
    t = np.arange(n) / sr
    burst = rng.standard_normal(n) * np.exp(-t / 0.004)
    blip = np.sin(2 * math.pi * freq * t) * np.exp(-t / 0.012)
    y = 0.7 * burst + 0.5 * blip
    y /= (np.max(np.abs(y)) + 1e-9)
    return _write_wav(path, y * 0.8, sr)


def synth_riser(path, dur=1.5, sr=48000):
    """Procedural riser: noise + rising sine sweep, building to the cut."""
    n = int(dur * sr)
    rng = np.random.default_rng(11)
    t = np.arange(n) / sr
    f = 200.0 * (2.0 ** (3.0 * t / dur))  # 200 Hz -> 1.6 kHz
    phase = 2 * math.pi * np.cumsum(f) / sr
    y = 0.4 * np.sin(phase) + 0.25 * rng.standard_normal(n)
    env = (t / dur) ** 2
    y = y * env
    y /= (np.max(np.abs(y)) + 1e-9)
    return _write_wav(path, y * 0.85, sr)


def sfx_path(name):
    """Resolve an SFX file: bundled CC0 file first, else synth fallback.

    Returns (path, is_synth). Synthesised files are written once into
    sfx/synth/ and reused.
    """
    fname, _level, _role = SFX[name]
    cand = os.path.join(SFX_DIR, fname)
    if os.path.exists(cand):
        return cand, False
    synth_dir = os.path.join(SFX_DIR, "synth")
    os.makedirs(synth_dir, exist_ok=True)
    out = os.path.join(synth_dir, fname.replace(".wav", "-synth.wav"))
    if not os.path.exists(out):
        {"whoosh": synth_whoosh, "whoosh_soft": synth_whoosh,
         "click": synth_click, "riser": synth_riser}[name](out)
    return out, True


# -------------------------------------------------------------- audio mix
def mix_sfx_argv(base_audio, sfx_events, out, base_db=0.0):
    """Build ffmpeg argv mixing SFX onto a base audio track.

    sfx_events: list of (sfx_name, time_s, gain_db). Each SFX is delayed
    to its cut time and mixed at the given level (plan: -18 dB).
    Returns argv; caller runs it with subprocess.
    """
    inputs = ["ffmpeg", "-y", "-i", base_audio]
    filters = []
    labels = ["[0:a]"]
    if base_db:
        filters.append(f"[0:a]volume={base_db}dB[a0]")
        labels = ["[a0]"]
    for i, (name, when, gain) in enumerate(sfx_events):
        path, _synth = sfx_path(name)
        inputs += ["-i", path]
        ms = int(round(when * 1000))
        filters.append(
            f"[{i + 1}:a]adelay={ms}|{ms},volume={gain}dB[s{i}]")
        labels.append(f"[s{i}]")
    n = len(labels)
    filters.append(f"{''.join(labels)}amix=inputs={n}:normalize=0[aout]")
    return inputs + ["-filter_complex", ";".join(filters),
                     "-map", "[aout]", "-c:a", "aac", "-b:a", "192k", out]


def waveform_overlay_argv(video, audio, out, wave_h=90, wave_color="white"):
    """Overlay a showwaves strip of `audio` at the bottom of `video`.

    Used on full-voice islands so the clip's voice shows as an audio
    wave, like the competitor videos Boss referenced.
    """
    fc = (
        f"[1:a]showwaves=s={W}x{wave_h}:mode=line:colors={wave_color}[wv];"
        f"[0:v][wv]overlay=0:{H - wave_h}[v]"
    )
    return ["ffmpeg", "-y", "-i", video, "-i", audio,
            "-filter_complex", fc,
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", out]


def loudnorm16_argv(inp, out):
    """EBU R128 loudness normalisation to our delivery level."""
    return ["ffmpeg", "-y", "-i", inp,
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out]


def run(argv, timeout=600):
    """Run an ffmpeg command, raise on failure with the tail of stderr."""
    r = subprocess.run(argv, capture_output=True, text=True,
                       timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed ({' '.join(argv[:6])}...):\n{r.stderr[-2000:]}")
    return r


def preflight(effect_plan, sfx_events):
    """Plan checks (VIDEO4-PLAN.md §5): SFX files exist, no effect/SFX
    repeats twice in a row. Raises ValueError on failure."""
    if not check_no_repeat(effect_plan):
        raise ValueError("effect plan repeats an effect twice in a row")
    for name, _when, _gain in sfx_events:
        path, synth = sfx_path(name)
        if not os.path.exists(path):
            raise ValueError(f"SFX missing and synth failed: {name}")
    return True
