#!/usr/bin/env python3
"""probe: thin wrapper around the vendored ffmpeg-skill probe.

Usage:
    python3 scripts/probe.py <video-file> [--json]

Prints the probe result for a finished video. No files are written.
Requires ffmpeg/ffprobe (ffmpeg 6.1+) and Python 3.10+.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE = HERE.parent / "skills" / "ffmpeg-skill" / "scripts" / "probe.py"


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv[1:] else 2
    target = Path(argv[1])
    if not target.exists():
        print(f"Failed: file not found: {target}", file=sys.stderr)
        return 2
    if not PROBE.exists():
        print(f"Failed: vendored probe not found: {PROBE}", file=sys.stderr)
        return 2
    cmd = [sys.executable, str(PROBE), str(target)]
    if "--json" in argv[2:]:
        cmd.append("--json")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
