#!/usr/bin/env python3
"""Verify the helpers with synthetic footage, audio, and an original test mark.

Requires FFmpeg/FFprobe, Node.js, and this skill's installed npm dependencies.
No movie footage, real faces, or brand assets are used. Outputs are temporary
unless --output-dir is supplied.
"""

from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent


def run(command: list[str], *, expect_failure: str | None = None) -> str:
    result = subprocess.run(command, text=True, capture_output=True)
    if expect_failure is not None:
        if result.returncode == 0 or expect_failure not in result.stderr:
            raise RuntimeError(f"Expected rejection containing {expect_failure!r}:\n{result.stderr}")
    elif result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): {command}\n{result.stderr}")
    return result.stdout


def decode_audio(path: Path, start: float | None = None, duration: float | None = None) -> bytes:
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
    if start is not None:
        command += ["-ss", str(start)]
    command += ["-i", str(path)]
    if duration is not None:
        command += ["-t", str(duration)]
    command += ["-vn", "-ac", "1", "-ar", "48000", "-f", "s16le", "-"]
    return subprocess.run(command, capture_output=True, check=True).stdout


def audio_frequency(path: Path, at: float) -> float:
    samples = array("h")
    samples.frombytes(decode_audio(path, at, 0.5))
    if sys.byteorder != "little":
        samples.byteswap()
    crossings = sum(left <= 0 < right for left, right in zip(samples, samples[1:]))
    return crossings * 48000 / len(samples)


def verify_audio(root: Path) -> dict:
    clean = decode_audio(root / "clean.mp4")
    cinema = decode_audio(root / "cinema.mp4")
    assert hashlib.sha256(clean).digest() == hashlib.sha256(cinema).digest(), "Cinema effect changed audio"
    setup = audio_frequency(root / "comparison.mp4", 2)
    punchline = audio_frequency(root / "comparison.mp4", 8)
    assert math.isclose(setup, 440, abs_tol=3), f"Setup source audio changed: {setup:.2f} Hz"
    assert math.isclose(punchline, 880, abs_tol=3), f"Punchline source audio changed: {punchline:.2f} Hz"
    return {
        "quality_only_audio_identical": True,
        "comparison_setup_frequency_hz": round(setup, 2),
        "comparison_punchline_frequency_hz": round(punchline, 2),
    }


def verify(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    source = root / "source-a.mp4"
    source_b = root / "source-b.mp4"
    watermark = root / "test-watermark.mov"
    cta_dir = root / "cta"
    for filename, duration, frequency in ((source, 12, 440), (source_b, 6, 880)):
        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", f"testsrc2=size=640x360:rate=30:duration={duration}",
            "-f", "lavfi", "-i", f"sine=frequency={frequency}:sample_rate=48000:duration={duration}",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "25",
            "-c:a", "aac", "-ac", "2" if filename == source_b else "1", "-shortest", str(filename),
        ])
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "color=c=blue@0.8:s=240x80:r=30:d=1,format=rgba",
        "-an", "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le",
        str(watermark),
    ])
    run([
        "node", str(SCRIPTS / "render_engagement.cjs"), "--platform", "instagram",
        "--action", "sequence", "--tap", "--output", str(cta_dir), "--overwrite",
    ])
    base = [
        sys.executable, str(SCRIPTS / "build_reel.py"),
        "--clip-a", str(source), "--watermark", str(watermark),
        "--cta-dir", str(cta_dir), "--preset", "ultrafast",
    ]
    reports = {}
    variants = {
        "clean": ["--title-a", "SYNTHETIC\n100% TEST"],
        "cinema": ["--title-a", "SYNTHETIC\n100% TEST", "--footage-effect", "cinema"],
        "comparison": [
            "--end-a", "6", "--title-a", "THE SETUP", "--clip-b", str(source_b),
            "--title-b", "THE PUNCHLINE", "--footage-effect", "cinema",
        ],
    }
    for name, options in variants.items():
        output = root / f"{name}.mp4"
        summary = json.loads(run(base + options + [
            "--output", str(output), "--preview-dir", str(root / f"{name}-previews"), "--overwrite",
        ]))
        assert summary["video"] == {
            "codec": "h264", "width": 1080, "height": 1920, "frame_rate": "30/1",
        }, summary
        assert summary["audio"] == {"codec": "aac", "sample_rate": "48000", "channels": 2}, summary
        assert math.isclose(summary["duration"], 12, abs_tol=0.05), summary
        assert summary["cta"]["action"] == "sequence", summary
        assert math.isclose(summary["cta"]["duration"], 8.4, abs_tol=0.05), summary
        assert summary["cta"]["end"] <= summary["duration"] - 1, summary
        assert len(summary["previews"]) == (5 if name == "comparison" else 4), summary
        reports[name] = summary

    rejection_output = ["--output", str(root / "should-not-exist.mp4"), "--dry-run"]
    run(base + ["--title-a", "TEST", "--end-a", "5"] + rejection_output, expect_failure="too short")
    run(base + ["--title-a", "TEST", "--canvas-width", "1079"] + rejection_output, expect_failure="must be even")
    run(base + ["--title-a", "TEST", "--fps", "0"] + rejection_output, expect_failure="must be positive")
    run(base + ["--title-a", "FIRST LINE\nSECOND LINE", "--title-y", "530"] + rejection_output, expect_failure="overlaps")
    run(base + ["--title-a", "A" * 100] + rejection_output, expect_failure="too wide")
    long_caption = root / "overwide-caption.json"
    long_caption.write_text(json.dumps([{"start": 0, "end": 12, "text": "A" * 100}]), encoding="utf-8")
    run(base + ["--captions-json", str(long_caption)] + rejection_output, expect_failure="Timed caption 1 line 1 is too wide")
    run(base + ["--title-a", "TEST", "--cta-dir", str(root / "missing")] + rejection_output, expect_failure="npm ci --prefix")
    nonsquare = root / "non-square-source.mp4"
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
        "-t", "0.1", "-vf", "setsar=2/1", "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "copy", str(nonsquare),
    ])
    run(base + ["--clip-a", str(nonsquare), "--title-a", "TEST"] + rejection_output, expect_failure="non-square sample aspect ratio 2:1")
    assert not (root / "should-not-exist.mp4").exists()

    # Quality-only treatment must retain static overlay placement and change
    # source pixels. Compare raw frames before the engagement graphic begins.
    frames = {}
    for name in ("clean", "cinema"):
        result = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", "1",
            "-i", str(root / f"{name}.mp4"), "-frames:v", "1",
            "-vf", "format=rgb24", "-f", "rawvideo", "-",
        ], capture_output=True, check=True)
        frames[name] = result.stdout
    assert frames["clean"] != frames["cinema"], "Cinema treatment produced no visual change"
    # H.264 compression can introduce small differences around otherwise
    # identical typography. Check headline glyph positions through high-luma
    # pixels instead of requiring byte-identical compressed frames.
    def white_glyph_positions(frame: bytes) -> set[int]:
        positions = set()
        for y in range(530, 590):
            for x in range(20, 1060):
                offset = (y * 1080 + x) * 3
                if min(frame[offset:offset + 3]) > 230:
                    positions.add(y * 1080 + x)
        return positions
    clean_glyphs = white_glyph_positions(frames["clean"])
    cinema_glyphs = white_glyph_positions(frames["cinema"])
    overlap = len(clean_glyphs & cinema_glyphs) / max(1, len(clean_glyphs | cinema_glyphs))
    assert overlap > 0.95, f"Headline geometry changed: {overlap:.3f} overlap"
    reports["checks"] = {
        "synthetic_sources": True, "quality_only_headline_overlap": round(overlap, 4),
        "rejected_short_clip": True, "rejected_odd_canvas": True,
        "rejected_nonpositive_fps": True, "rejected_headline_overlap": True,
        "rejected_headline_width": True, "missing_asset_setup_guidance": True,
        "rejected_timed_caption_width": True,
        "rejected_non_square_source": True,
        "automatic_two_line_headline": True, "mixed_mono_stereo_comparison": True,
        **verify_audio(root),
    }
    (root / "verification.json").write_text(json.dumps(reports, indent=2) + "\n", encoding="utf-8")
    return reports


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="Keep synthetic outputs in this directory")
    args = parser.parse_args()
    for binary in ("ffmpeg", "ffprobe", "node"):
        if not shutil.which(binary):
            parser.error(f"Required binary unavailable: {binary}")
    if args.output_dir:
        root = args.output_dir.expanduser().resolve()
        reports = verify(root)
        print(f"Synthetic verification passed. Outputs: {root}")
    else:
        with tempfile.TemporaryDirectory(prefix="build-meme-reel-verify-") as temporary:
            reports = verify(Path(temporary))
        print("Synthetic verification passed. Temporary outputs removed.")
    print(json.dumps(reports["checks"], indent=2))


if __name__ == "__main__":
    main()
