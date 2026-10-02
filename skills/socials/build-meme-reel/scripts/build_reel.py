#!/usr/bin/env python3
"""Build a branded vertical meme Reel with a blurred background and engagement graphics."""

from __future__ import annotations

import argparse
import json
import math
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
CTA_ASSETS = SKILL_ROOT / "generated" / "engagement"
TITLE_BOX_PADDING = 28
SUBTITLE_BOX_PADDING = 12
SUBTITLE_OUTLINE = 3

# A quality treatment on the source only. It never changes crop, geometry,
# framing, output resolution, title, watermark, or engagement graphics.
CINEMA_FILTER = (
    "gblur=sigma=0.65,"
    "eq=contrast=0.85:brightness=0.018:saturation=0.76:gamma=1.04,"
    "noise=alls=5:allf=t+u:all_seed=23,"
    "vignette=PI/9,"
    "eq=brightness='0.004*sin(2*PI*7*t)+0.003*sin(2*PI*0.6*t)':eval=frame"
)


def die(message: str) -> None:
    raise SystemExit(message)


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        text=True,
        capture_output=capture,
    )


def parse_time(value: str) -> float:
    try:
        if ":" not in value:
            seconds = float(value)
        else:
            parts = [float(part) for part in value.split(":")]
            if len(parts) == 2:
                seconds = parts[0] * 60 + parts[1]
            elif len(parts) == 3:
                seconds = parts[0] * 3600 + parts[1] * 60 + parts[2]
            else:
                raise ValueError
    except ValueError:
        die(f"Invalid timestamp: {value}")
    if not math.isfinite(seconds) or seconds < 0:
        die(f"Timestamp must be finite and non-negative: {value}")
    return seconds


def probe(path: Path) -> dict:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=index,codec_type,codec_name,width,height,sample_aspect_ratio,r_frame_rate,sample_rate,channels:format=duration,size",
            "-of",
            "json",
            str(path),
        ],
        capture=True,
    )
    return json.loads(result.stdout)


def source_duration(metadata: dict, path: Path) -> float:
    try:
        return float(metadata["format"]["duration"])
    except (KeyError, TypeError, ValueError):
        die(f"Could not determine duration: {path}")


def require_media_streams(metadata: dict, path: Path) -> None:
    types = {stream.get("codec_type") for stream in metadata.get("streams", [])}
    if "video" not in types:
        die(f"No video stream found: {path}")
    if "audio" not in types:
        die(f"No audio stream found: {path}")
    video = next(stream for stream in metadata["streams"] if stream.get("codec_type") == "video")
    sar = video.get("sample_aspect_ratio")
    match = re.fullmatch(r"(\d+)[:/](\d+)", sar) if isinstance(sar, str) else None
    if match:
        numerator, denominator = map(int, match.groups())
        # 0:1 and missing values mean unspecified pixel aspect. Reject only
        # known non-square pixels, which would otherwise be squeezed later.
        if numerator > 0 and denominator > 0 and numerator != denominator:
            die(
                f"Source has non-square sample aspect ratio {sar}: {path}. "
                "Normalize its display aspect to square pixels in a separate derivative before assembly; "
                "preserve the source file and audio."
            )


def clip_duration(start: float, end_value: str | None, total: float, label: str) -> float:
    end = parse_time(end_value) if end_value is not None else total
    if start >= total:
        die(f"{label} start ({start:.3f}s) is past the source duration ({total:.3f}s)")
    if end > total + 0.05:
        die(f"{label} end ({end:.3f}s) is past the source duration ({total:.3f}s)")
    duration = min(end, total) - start
    if duration <= 0:
        die(f"{label} end must be after its start")
    return duration


def find_font(requested: str | None) -> Path:
    if requested:
        candidate = Path(requested).expanduser().resolve()
        if candidate.is_file():
            return candidate
        die(f"Font not found: {candidate}")

    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
        Path("/Library/Fonts/Arial Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    die("No supported bold font found. Pass --font /path/to/font.ttf")


def filter_quote(value: Path) -> str:
    escaped = str(value).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    return f"'{escaped}'"


def measure_text(font: Path, text_file: Path, size: int) -> tuple[float, float]:
    """Measure with the same FFmpeg/font stack that renders the headline."""
    result = run(
        [
            "ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "info",
            "-f", "lavfi", "-i", "color=c=black:s=16x16:d=0.04",
            "-vf", (
                f"drawtext=fontfile={filter_quote(font)}:textfile={filter_quote(text_file)}:"
                f"expansion=none:fontsize={size}:x='print(text_w)':y='print(text_h)'"
            ),
            "-frames:v", "1", "-f", "null", "-",
        ],
        capture=True,
    )
    # FFmpeg releases either prefix print() values with [Eval @ ...] or
    # print them as bare numbers. The first two values are width and height.
    values = re.findall(r"^(?:\[Eval[^\]]*\]\s*)?(-?\d+(?:\.\d+)?)\s*$", result.stderr, re.M)
    if len(values) < 2:
        die("FFmpeg could not measure headline text. Check the drawtext filter and font.")
    return float(values[0]), float(values[1])


def subtitle_srt(cues: list[dict]) -> str:
    """Export the same output-relative cues used by the burned dialogue layer."""
    def timestamp(seconds: float) -> str:
        milliseconds = round(seconds * 1000)
        hours, milliseconds = divmod(milliseconds, 3600000)
        minutes, milliseconds = divmod(milliseconds, 60000)
        seconds, milliseconds = divmod(milliseconds, 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
    return "".join(
        f"{index}\n{timestamp(cue['start'])} --> {timestamp(cue['end'])}\n{cue['text']}\n\n"
        for index, cue in enumerate(cues, start=1)
    )


def even(value: float) -> int:
    result = int(round(value))
    return result if result % 2 == 0 else result - 1


def cta_start_time(total: float, duration: float, requested: str | None) -> float:
    """Keep the complete prompt inside the video with a clean final second."""
    latest_start = total - duration - 1.0
    if latest_start < -0.000001:
        die(
            f"Reel is too short for the complete {duration:.2f}s CTA: needs at least "
            f"{duration + 1:.2f}s with --cta-at 0, or {duration + 3:.2f}s for automatic placement."
        )
    start = parse_time(requested) if requested is not None else max(2.0, min(total * 0.35, total - duration - 1.0))
    if start + duration > total - 1.0 + 0.000001:
        if requested is None:
            die(
                f"Reel is too short for this CTA: automatic placement needs at least {duration + 3:.2f}s. "
                f"Set an earlier --cta-at at or before {latest_start:.2f}s to leave a clean final second."
            )
        die(f"CTA must finish at least 1 second before the Reel ends; latest --cta-at is {latest_start:.2f}s")
    return start


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--clip-a", required=True, type=Path)
    result.add_argument("--start-a", default="0")
    result.add_argument("--end-a")
    result.add_argument("--title-a")
    result.add_argument("--captions-json", type=Path, help="Single-clip timed captions; replaces --title-a")
    result.add_argument(
        "--subtitles-json", type=Path,
        help="Add dialogue subtitles below the headline; start/end seconds are relative to the complete trimmed output",
    )
    result.add_argument("--subtitle-font-size", type=int, help="Dialogue type size (default: 46 px at 1080 px canvas width)")
    result.add_argument("--subtitle-y", type=int, help="Dialogue text top edge (default: 64 px above the sharp footage bottom)")
    result.add_argument("--subtitle-max-width", type=int, help="Maximum subtitle box width including padding (default: 840 px at 1080 px canvas width)")
    result.add_argument("--clip-b", type=Path)
    result.add_argument("--start-b", default="0")
    result.add_argument("--end-b")
    result.add_argument("--title-b")
    result.add_argument("--output", required=True, type=Path)
    result.add_argument("--preview-dir", type=Path)
    result.add_argument("--font")
    result.add_argument("--font-size", type=int, default=76)
    result.add_argument("--title-y", type=int)
    result.add_argument("--canvas-width", type=int, default=1080)
    result.add_argument("--canvas-height", type=int, default=1920)
    result.add_argument("--main-width", type=int, default=1000)
    result.add_argument("--fps", type=int, default=30)
    result.add_argument("--background-blur", type=int, default=24)
    result.add_argument("--background-brightness", type=float, default=-0.18)
    result.add_argument(
        "--footage-effect", choices=("clean", "cinema"), default="clean",
        help="Optional source quality treatment; cinema adds softness, grain, washed blacks, and flicker",
    )
    result.add_argument(
        "--watermark", type=Path, required=True,
        help="Path to the approved looping transparent brand watermark; no brand asset is bundled",
    )
    result.add_argument("--watermark-width", type=int, default=270, help="Watermark width in canvas pixels")
    result.add_argument(
        "--watermark-corner",
        choices=("bottom-left", "bottom-right", "top-left", "top-right"),
        default="bottom-left", help="Corner inside the sharp main footage",
    )
    result.add_argument("--watermark-margin", type=int, default=90, help="Inset from the sharp footage edges (default: 90 px, clearing common cinematic bars)")
    result.add_argument("--cta", choices=("like", "comment", "follow", "sequence"), default="sequence", help="Engagement graphics (default: complete Like, Comment, Follow sequence)")
    result.add_argument(
        "--cta-dir", type=Path,
        help="Directory containing generated CTA MOVs; defaults to generated/engagement/tap for tap, generated/engagement for quiet",
    )
    result.add_argument("--cta-style", choices=("quiet", "tap"), default="tap", help="CTA animation: arrow cursor click with state feedback (tap, default), or quiet")
    result.add_argument("--platform", choices=("instagram", "tiktok", "youtube"), default="instagram", help="CTA platform (default: instagram; YouTube follow means subscribe)")
    result.add_argument("--cta-at", help="CTA start time relative to the complete trimmed Reel; default: about 35%% through")
    result.add_argument("--cta-x", type=int, help="CTA left edge in canvas pixels (default: horizontally centered)")
    result.add_argument("--cta-y", type=int, help="CTA top edge in canvas pixels (default: 1280)")
    result.add_argument("--cta-width", type=int, help="CTA surface width in canvas pixels (default: native asset width)")
    result.add_argument("--crf", type=int, default=18)
    result.add_argument("--preset", default="medium")
    result.add_argument("--overwrite", action="store_true")
    result.add_argument("--dry-run", action="store_true")
    return result


def main() -> None:
    args = parser().parse_args()
    for binary in ("ffmpeg", "ffprobe"):
        if shutil.which(binary) is None:
            die(f"Required binary is unavailable: {binary}")

    clip_a = args.clip_a.expanduser().resolve()
    clip_b = args.clip_b.expanduser().resolve() if args.clip_b else None
    output = args.output.expanduser().resolve()
    subtitle_sidecar = output.with_suffix(".srt") if args.subtitles_json else None
    if bool(clip_b) != bool(args.title_b):
        die("Pass --clip-b and --title-b together, or omit both for a single-clip Reel")
    if clip_b is None and (args.start_b != "0" or args.end_b is not None):
        die("--start-b and --end-b require --clip-b")
    sources = [clip_a] + ([clip_b] if clip_b else [])
    cta_platform = args.platform
    cta_style = args.cta_style
    cta_assets = args.cta_dir.expanduser().resolve() if args.cta_dir else (
        CTA_ASSETS / "tap" if cta_style == "tap" else CTA_ASSETS
    )
    cta_path = cta_assets / f"{cta_platform}-{args.cta}.mov"
    if not cta_path.is_file():
        renderer = SKILL_ROOT / "scripts" / "render_engagement.cjs"
        render_command = [
            "node", str(renderer), "--platform", cta_platform, "--action", args.cta,
            "--output", str(cta_assets),
        ] + (["--tap"] if cta_style == "tap" else [])
        die(
            f"CTA asset not found: {cta_path}\n"
            "Install the renderer's locked dependencies, then generate it:\n"
            f"  npm ci --prefix {shlex.quote(str(SKILL_ROOT))}\n"
            f"  {shlex.join(render_command)}"
        )
    watermark_path = args.watermark.expanduser().resolve()
    if not watermark_path.is_file():
        die(f"Brand watermark not found: {watermark_path}. Pass --watermark with the approved asset's path.")
    if args.captions_json:
        if clip_b or args.title_a:
            die("--captions-json requires a single clip and replaces --title-a")
    elif not args.title_a:
        die("Pass --title-a or --captions-json")
    for source in sources:
        if not source.is_file():
            die(f"Source file not found: {source}")
    protected_paths = sources + [watermark_path, cta_path]
    protected_paths += [path.expanduser().resolve() for path in (args.captions_json, args.subtitles_json) if path]
    if output in protected_paths or (subtitle_sidecar is not None and subtitle_sidecar in protected_paths):
        die("Output must not overwrite a source file")
    if output.exists() and not args.overwrite:
        die(f"Output already exists; pass --overwrite to replace it: {output}")
    if subtitle_sidecar is not None and subtitle_sidecar.exists() and not args.overwrite:
        die(f"Subtitle sidecar already exists; pass --overwrite to replace it: {subtitle_sidecar}")

    meta_a = probe(clip_a)
    require_media_streams(meta_a, clip_a)
    start_a = parse_time(args.start_a)
    duration_a = clip_duration(start_a, args.end_a, source_duration(meta_a, clip_a), "Clip A")
    start_b = 0.0
    duration_b = 0.0
    if clip_b:
        meta_b = probe(clip_b)
        require_media_streams(meta_b, clip_b)
        start_b = parse_time(args.start_b)
        duration_b = clip_duration(start_b, args.end_b, source_duration(meta_b, clip_b), "Clip B")

    if args.canvas_width <= 0 or args.canvas_height <= 0 or args.main_width <= 0:
        die("Canvas and main-clip dimensions must be positive")
    if args.canvas_width % 2 or args.canvas_height % 2 or args.main_width % 2:
        die("Canvas and main-clip dimensions must be even for H.264 export")
    if args.fps <= 0:
        die("Frame rate must be positive")
    if args.main_width > args.canvas_width:
        die("Main clip width cannot exceed the canvas width")
    if args.font_size < 24:
        die("Font size is too small for a social video")

    cta_start = cta_duration = cta_end = None
    cta_x = cta_y = cta_width = cta_height = None
    if cta_path:
        cta_meta = probe(cta_path)
        cta_video = next((stream for stream in cta_meta.get("streams", []) if stream.get("codec_type") == "video"), None)
        if not cta_video or not cta_video.get("width") or not cta_video.get("height"):
            die(f"No usable video stream found in CTA: {cta_path}")
        cta_duration = source_duration(cta_meta, cta_path)
        if not math.isfinite(cta_duration) or cta_duration <= 0:
            die("CTA video must have a finite, positive duration")
        cta_start = cta_start_time(duration_a + duration_b, cta_duration, args.cta_at)
        cta_end = cta_start + cta_duration
        cta_width = args.cta_width if args.cta_width is not None else int(cta_video["width"])
        cta_x = args.cta_x if args.cta_x is not None else (args.canvas_width - cta_width) // 2
        cta_y = args.cta_y if args.cta_y is not None else 1280
        cta_height = max(2, 2 * round(cta_width * cta_video["height"] / cta_video["width"] / 2))
        if cta_width <= 0 or cta_x < 0 or cta_y < 0 or cta_x + cta_width > args.canvas_width or cta_y + cta_height > args.canvas_height:
            die("CTA must fit inside the canvas; adjust --cta-x, --cta-y, or --cta-width")

    main_height = even(args.main_width * 9 / 16)
    main_x = (args.canvas_width - args.main_width) // 2
    main_y = (args.canvas_height - main_height) // 2
    watermark_x = watermark_y = None
    if watermark_path:
        if args.watermark_width <= 0 or args.watermark_margin < 0:
            die("Watermark width must be positive and margin must be non-negative")
        watermark_meta = probe(watermark_path)
        watermark_video = next(
            (stream for stream in watermark_meta.get("streams", []) if stream.get("codec_type") == "video"),
            None,
        )
        if not watermark_video or not watermark_video.get("width") or not watermark_video.get("height"):
            die(f"No usable video stream found in watermark: {watermark_path}")
        if source_duration(watermark_meta, watermark_path) <= 0:
            die("Watermark video must have a positive duration")
        watermark_height = max(2, 2 * round(args.watermark_width * watermark_video["height"] / watermark_video["width"] / 2))
        if (args.watermark_width + 2 * args.watermark_margin > args.main_width
                or watermark_height + 2 * args.watermark_margin > main_height):
            die("Watermark must fit inside the main footage; reduce --watermark-width or --watermark-margin")
        watermark_x = main_x + args.watermark_margin
        watermark_y = main_y + args.watermark_margin
        if args.watermark_corner.endswith("right"):
            watermark_x = main_x + args.main_width - args.watermark_margin - args.watermark_width
        if args.watermark_corner.startswith("bottom"):
            watermark_y = main_y + main_height - args.watermark_margin - watermark_height
    headline_lines = max(
        [1] + [len([line for line in title.splitlines() if line.strip()])
               for title in (args.title_a, args.title_b) if title]
    )
    title_y = args.title_y if args.title_y is not None else max(
        180, main_y - args.font_size - 73 - (headline_lines - 1) * (args.font_size + 20)
    )
    if title_y < 180 or title_y >= main_y:
        die(f"Title Y must stay in the safe area above the main clip: 180 <= y < {main_y}")
    font = find_font(args.font)
    captions = []
    if args.captions_json:
        captions = json.loads(args.captions_json.read_text(encoding="utf-8"))
        if not isinstance(captions, list) or not captions:
            die("Caption JSON must be a non-empty list")
        previous_end = 0.0
        for caption in captions:
            start, end = float(caption["start"]), float(caption["end"])
            size = int(caption.get("font_size", args.font_size))
            y = int(caption.get("y", title_y))
            lines = caption["text"].splitlines()
            if not (math.isfinite(start) and math.isfinite(end) and previous_end <= start < end <= duration_a):
                die("Captions must be ordered, non-overlapping and within the trimmed clip")
            if not 1 <= len(lines) <= 3 or any(not line.strip() for line in lines):
                die("Timed captions require one to three non-empty lines")
            if size < 24 or y < 180 or y + len(lines) * (size + 20) + 28 > main_y:
                die("Timed caption must fit in the safe area above the main clip")
            caption.update(start=start, end=end, font_size=size, y=y)
            previous_end = end
    subtitles = []
    subtitle_size = args.subtitle_font_size if args.subtitle_font_size is not None else round(46 * args.canvas_width / 1080)
    subtitle_y = args.subtitle_y if args.subtitle_y is not None else main_y + main_height - round(64 * args.canvas_height / 1920)
    subtitle_max_width = args.subtitle_max_width if args.subtitle_max_width is not None else round(840 * args.canvas_width / 1080)
    subtitle_padding = max(1, round(SUBTITLE_BOX_PADDING * args.canvas_width / 1080))
    subtitle_outline = max(1, round(SUBTITLE_OUTLINE * args.canvas_width / 1080))
    if args.subtitles_json:
        if subtitle_size < 24:
            die("Subtitle font size is too small for a social video; use at least 24 px")
        if subtitle_max_width <= 2 * subtitle_padding or subtitle_max_width > args.canvas_width:
            die("Subtitle maximum width must fit inside the canvas and allow padding")
        try:
            subtitles = json.loads(args.subtitles_json.expanduser().read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            die(f"Cannot read subtitle JSON: {error}")
        if not isinstance(subtitles, list) or not subtitles:
            die("Subtitle JSON must be a non-empty list")
        previous_end = 0.0
        for subtitle_index, subtitle in enumerate(subtitles, start=1):
            if not isinstance(subtitle, dict):
                die(f"Subtitle {subtitle_index} must be an object with start, end, and text")
            try:
                start, end = float(subtitle["start"]), float(subtitle["end"])
                text = subtitle["text"]
            except (KeyError, TypeError, ValueError):
                die(f"Subtitle {subtitle_index} requires numeric start/end and text")
            if not (math.isfinite(start) and math.isfinite(end) and previous_end <= start < end <= duration_a + duration_b):
                die("Subtitles must be ordered, non-overlapping and within the complete trimmed output")
            if round(start * 1000) >= round(end * 1000):
                die(f"Subtitle {subtitle_index} must span at least one millisecond for its SRT sidecar")
            if not isinstance(text, str):
                die(f"Subtitle {subtitle_index} text must be a string")
            lines = text.splitlines()
            if not 1 <= len(lines) <= 2 or any(not line.strip() for line in lines):
                die("Dialogue subtitles require one or two non-empty lines")
            if len(lines) == 2 and args.subtitle_y is None:
                die("Two-line subtitles require an explicit --subtitle-y with room for both lines")
            # Global placement and type keep all dialogue cues consistent. The
            # input supplies only output-relative timings and verbatim dialogue.
            subtitles[subtitle_index - 1] = {"start": start, "end": end, "text": text}
            previous_end = end
    elif any(value is not None for value in (args.subtitle_font_size, args.subtitle_y, args.subtitle_max_width)):
        die("Subtitle layout options require --subtitles-json")
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="build-meme-reel-") as temporary:
        temporary_path = Path(temporary)
        protected_regions = []

        def add_protected_region(label: str, bounds: tuple[float, float, float, float], start: float, end: float) -> None:
            protected_regions.append({"label": label, "bounds": bounds, "start": start, "end": end})

        if watermark_path:
            add_protected_region("watermark", (watermark_x, watermark_y, args.watermark_width, watermark_height), 0, duration_a + duration_b)
        if cta_path:
            add_protected_region("active CTA", (cta_x, cta_y, cta_width, cta_height), cta_start, cta_end)

        def write_title_files(prefix: str, title: str) -> list[Path]:
            lines = [line.strip() for line in title.upper().splitlines() if line.strip()]
            if not lines:
                die("Title text cannot be empty")
            if len(lines) > 2:
                die("Title text must use at most two lines")
            files = []
            for line_number, line in enumerate(lines):
                title_file = temporary_path / f"title-{prefix}-{line_number}.txt"
                title_file.write_text(line, encoding="utf-8")
                files.append(title_file)
                width, height = measure_text(font, title_file, args.font_size)
                if width + 2 * TITLE_BOX_PADDING > args.canvas_width:
                    die(
                        f"Title {prefix.upper()} line {line_number + 1} is too wide ({width:.0f} px). "
                        "Add a line break, reduce --font-size, or choose a suitable --font."
                    )
                line_y = title_y + line_number * (args.font_size + 20)
                add_protected_region(
                    f"headline {prefix.upper()}",
                    ((args.canvas_width - width) / 2 - TITLE_BOX_PADDING, line_y - TITLE_BOX_PADDING,
                     width + 2 * TITLE_BOX_PADDING, height + 2 * TITLE_BOX_PADDING),
                    0 if prefix == "a" else duration_a,
                    duration_a if prefix == "a" else duration_a + duration_b,
                )
                if line_y + height + TITLE_BOX_PADDING > main_y:
                    die(
                        f"Title {prefix.upper()} line {line_number + 1} overlaps the main footage. "
                        "Move --title-y upward or reduce --font-size."
                    )
            return files

        title_a_files = write_title_files("a", args.title_a) if args.title_a else []
        title_b_files = write_title_files("b", args.title_b) if args.title_b else []
        caption_files = []
        for caption_index, caption in enumerate(captions):
            files = []
            for line_number, line in enumerate(caption["text"].splitlines()):
                caption_file = temporary_path / f"caption-{caption_index}-{line_number}.txt"
                caption_file.write_text(line, encoding="utf-8")
                width, height = measure_text(font, caption_file, caption["font_size"])
                if width + 2 * TITLE_BOX_PADDING > args.canvas_width:
                    die(
                        f"Timed caption {caption_index + 1} line {line_number + 1} is too wide ({width:.0f} px). "
                        "Add a line break, reduce its font_size, or choose a suitable --font."
                    )
                line_y = caption["y"] + line_number * (caption["font_size"] + 20)
                add_protected_region(
                    f"timed headline {caption_index + 1}",
                    ((args.canvas_width - width) / 2 - TITLE_BOX_PADDING, line_y - TITLE_BOX_PADDING,
                     width + 2 * TITLE_BOX_PADDING, height + 2 * TITLE_BOX_PADDING),
                    caption["start"], caption["end"],
                )
                files.append(caption_file)
            caption_files.append(files)

        subtitle_files = []
        safe_left = round(72 * args.canvas_width / 1080)
        safe_top = round(180 * args.canvas_height / 1920)
        safe_bottom = args.canvas_height - round(380 * args.canvas_height / 1920)
        subtitle_line_step = subtitle_size + round(10 * args.canvas_width / 1080)

        def rectangles_overlap(left: tuple[float, float, float, float], right: tuple[float, float, float, float]) -> bool:
            x1, y1, w1, h1 = left
            x2, y2, w2, h2 = right
            return x1 < x2 + w2 and x2 < x1 + w1 and y1 < y2 + h2 and y2 < y1 + h1

        for subtitle_index, subtitle in enumerate(subtitles):
            files = []
            boxes = []
            for line_number, line in enumerate(subtitle["text"].splitlines()):
                subtitle_file = temporary_path / f"subtitle-{subtitle_index}-{line_number}.txt"
                subtitle_file.write_text(line.strip(), encoding="utf-8")
                width, height = measure_text(font, subtitle_file, subtitle_size)
                box = ((args.canvas_width - width) / 2 - subtitle_padding,
                       subtitle_y + line_number * subtitle_line_step - subtitle_padding,
                       width + 2 * subtitle_padding, height + 2 * subtitle_padding)
                if box[2] > subtitle_max_width:
                    die(
                        f"Subtitle {subtitle_index + 1} line {line_number + 1} is too wide ({box[2]:.0f} px including padding). "
                        "Split the dialogue into shorter timed cues or use an explicit two-line layout."
                    )
                if (box[0] < safe_left or box[0] + box[2] > args.canvas_width - safe_left
                        or box[1] < safe_top or box[1] + box[3] > safe_bottom):
                    die(
                        f"Subtitle {subtitle_index + 1} leaves the subtitle safe area. "
                        "Adjust --subtitle-y, shorten the cue, or reduce --subtitle-font-size."
                    )
                for region in protected_regions:
                    if (subtitle["start"] < region["end"] and region["start"] < subtitle["end"]
                            and rectangles_overlap(box, region["bounds"])):
                        die(
                            f"Subtitle {subtitle_index + 1} overlaps the {region['label']}. "
                            "Adjust --subtitle-y or the asset placement; keep the full headline, watermark, and CTA."
                        )
                files.append(subtitle_file)
                boxes.append({"x": round(box[0], 2), "y": box[1], "width": box[2], "height": box[3]})
            subtitle["boxes"] = boxes
            subtitle_files.append(files)

        def video_chain(index: int, prefix: str, title_files: list[Path]) -> str:
            effect = CINEMA_FILTER + "," if args.footage_effect == "cinema" else ""
            chain = (
                f"[{index}:v]setpts=PTS-STARTPTS,{effect}split=2[{prefix}_bg][{prefix}_fg];"
                f"[{prefix}_bg]scale={args.canvas_width}:{args.canvas_height}:force_original_aspect_ratio=increase,"
                f"crop={args.canvas_width}:{args.canvas_height},boxblur={args.background_blur}:5,"
                f"eq=brightness={args.background_brightness}:contrast=0.94:saturation=0.85[{prefix}bg];"
                f"[{prefix}_fg]scale={args.main_width}:{main_height}:force_original_aspect_ratio=decrease,"
                f"pad={args.main_width}:{main_height}:(ow-iw)/2:(oh-ih)/2:black[{prefix}fg];"
                f"[{prefix}bg][{prefix}fg]overlay={main_x}:{main_y},"
                f"drawbox=x={main_x}:y={main_y}:w={args.main_width}:h={main_height}:color=white@0.28:t=3"
            )
            for line_number, title_file in enumerate(title_files):
                line_y = title_y + line_number * (args.font_size + 20)
                chain += (
                    f",drawtext=fontfile={filter_quote(font)}:textfile={filter_quote(title_file)}:"
                    f"expansion=none:fontcolor=white:fontsize={args.font_size}:x=(w-text_w)/2:y={line_y}:"
                    "box=1:boxcolor=black@0.50:boxborderw=28"
                )
            for caption_index, caption in enumerate(captions):
                for line_number, line in enumerate(caption["text"].splitlines()):
                    caption_file = caption_files[caption_index][line_number]
                    line_y = caption["y"] + line_number * (caption["font_size"] + 20)
                    chain += (
                        f",drawtext=fontfile={filter_quote(font)}:textfile={filter_quote(caption_file)}:"
                        f"expansion=none:fontcolor=white:fontsize={caption['font_size']}:x=(w-text_w)/2:y={line_y}:"
                        "box=1:boxcolor=black@0.50:boxborderw=28:"
                        f"enable='gte(t,{caption['start']})*lt(t,{caption['end']})'"
                    )
            return chain + ",setsar=1"

        if clip_b:
            filters = (
                video_chain(0, "a", title_a_files)
                + "[av];"
                + video_chain(1, "b", title_b_files)
                + "[bv];"
                + f"[0:a]atrim=duration={duration_a:.6f},asetpts=PTS-STARTPTS,aresample=48000,"
                  "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a0];"
                + f"[1:a]atrim=duration={duration_b:.6f},asetpts=PTS-STARTPTS,aresample=48000,"
                  "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[a1];"
                + "[av][a0][bv][a1]concat=n=2:v=1:a=1[vcat][acat];"
                + f"[vcat]fps={args.fps}[vbase];"
                + "[acat]loudnorm=I=-16:LRA=11:TP=-1.5[aout]"
            )
        else:
            filters = (
                video_chain(0, "a", title_a_files)
                + f"[av];[av]fps={args.fps}[vbase];"
                + f"[0:a]atrim=duration={duration_a:.6f},asetpts=PTS-STARTPTS,aresample=48000,"
                + "loudnorm=I=-16:LRA=11:TP=-1.5[aout]"
            )

        overlay_base = "vbase"
        if subtitles:
            filters += ";[vbase]"
            subtitle_draws = []
            for subtitle_index, subtitle in enumerate(subtitles):
                for line_number, subtitle_file in enumerate(subtitle_files[subtitle_index]):
                    line_y = subtitle_y + line_number * subtitle_line_step
                    subtitle_draws.append(
                        f"drawtext=fontfile={filter_quote(font)}:textfile={filter_quote(subtitle_file)}:"
                        f"expansion=none:fontcolor=white:fontsize={subtitle_size}:x=(w-text_w)/2:y={line_y}:"
                        f"borderw={subtitle_outline}:bordercolor=black:box=1:boxcolor=black@0.62:boxborderw={subtitle_padding}:"
                        f"enable='gte(t,{subtitle['start']:.6f})*lt(t,{subtitle['end']:.6f})'"
                    )
            filters += ",".join(subtitle_draws) + "[vsubtitled]"
            overlay_base = "vsubtitled"
        if watermark_path:
            watermark_index = len(sources)
            filters += (
                f";[{watermark_index}:v]setpts=PTS-STARTPTS,fps={args.fps},"
                f"scale={args.watermark_width}:{watermark_height}:flags=lanczos,format=rgba,setsar=1[watermark];"
                f"[{overlay_base}][watermark]overlay=x={watermark_x}:y={watermark_y}:"
                "shortest=1:alpha=straight[vmarked]"
            )
            overlay_base = "vmarked"
        if cta_path:
            cta_index = len(sources) + int(watermark_path is not None)
            filters += (
                f";[{cta_index}:v]setpts=PTS-STARTPTS,fps={args.fps},"
                f"scale={cta_width}:{cta_height}:flags=lanczos,format=rgba,setsar=1,"
                f"setpts=PTS+{cta_start:.6f}/TB[cta];"
                f"[{overlay_base}][cta]overlay=x={cta_x}:y={cta_y}:"
                "eof_action=pass:repeatlast=0:shortest=0:alpha=straight:"
                f"enable='gte(t,{cta_start:.6f})*lt(t,{cta_end:.6f})'[vprompt]"
            )
            overlay_base = "vprompt"
        filters += f";[{overlay_base}]format=yuv420p[vout]"

        command = [
            "ffmpeg",
            "-hide_banner",
            "-y" if args.overwrite else "-n",
            "-ss",
            f"{start_a:.6f}",
            "-t",
            f"{duration_a:.6f}",
            "-i",
            str(clip_a),
        ]
        if clip_b:
            command.extend(
                [
                    "-ss",
                    f"{start_b:.6f}",
                    "-t",
                    f"{duration_b:.6f}",
                    "-i",
                    str(clip_b),
                ]
            )
        if watermark_path:
            command.extend(["-stream_loop", "-1", "-i", str(watermark_path)])
        if cta_path:
            command.extend(["-i", str(cta_path)])
        command.extend(
            [
                "-filter_complex",
                filters,
                "-map",
                "[vout]",
                "-map",
                "[aout]",
                "-c:v",
                "libx264",
            "-preset",
            args.preset,
            "-crf",
            str(args.crf),
            "-profile:v",
            "high",
            "-level",
            "4.2",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-t",
            f"{duration_a + duration_b:.6f}",
            "-movflags",
            "+faststart",
                str(output),
            ]
        )

        if args.dry_run:
            print(json.dumps(command, indent=2))
            return
        run(command)
        if subtitle_sidecar is not None:
            subtitle_sidecar.write_text(subtitle_srt(subtitles), encoding="utf-8")

    finished = probe(output)
    video = next(stream for stream in finished["streams"] if stream.get("codec_type") == "video")
    audio = next(stream for stream in finished["streams"] if stream.get("codec_type") == "audio")
    summary = {
        "output": str(output),
        "duration": float(finished["format"]["duration"]),
        "size_bytes": int(finished["format"]["size"]),
        "footage_effect": args.footage_effect,
        "video": {
            "codec": video.get("codec_name"),
            "width": video.get("width"),
            "height": video.get("height"),
            "frame_rate": video.get("r_frame_rate"),
        },
        "audio": {
            "codec": audio.get("codec_name"),
            "sample_rate": audio.get("sample_rate"),
            "channels": audio.get("channels"),
        },
        "subtitles": {
            "source": str(args.subtitles_json.expanduser().resolve()),
            "srt": str(subtitle_sidecar),
            "timing": "complete trimmed output",
            "font_size": subtitle_size,
            "text_y": subtitle_y,
            "max_box_width": subtitle_max_width,
            "box_padding": subtitle_padding,
            "outline": subtitle_outline,
            "safe_area": {"left": safe_left, "right": args.canvas_width - safe_left, "top": safe_top, "bottom": safe_bottom},
            "cues": subtitles,
        } if subtitles else None,
        "watermark": {
            "source": str(watermark_path),
            "width": args.watermark_width,
            "corner": args.watermark_corner,
            "margin": args.watermark_margin,
            "x": watermark_x,
            "y": watermark_y,
        } if watermark_path else None,
        "cta": {
            "source": str(cta_path),
            "platform": cta_platform,
            "action": args.cta,
            "style": cta_style,
            "start": cta_start,
            "end": cta_end,
            "duration": cta_duration,
            "placement": "explicit" if args.cta_at is not None else "automatic",
            "x": cta_x,
            "y": cta_y,
            "width": cta_width,
            "height": cta_height,
        } if cta_path else None,
    }

    if args.preview_dir:
        preview_dir = args.preview_dir.expanduser().resolve()
        preview_dir.mkdir(parents=True, exist_ok=True)
        preview_times = [min(2.0, duration_a / 2)]
        labels = ["first"]
        if captions:
            preview_times = [(caption["start"] + caption["end"]) / 2 for caption in captions]
            labels = [f"caption-{i + 1}" for i in range(len(captions))]
        if subtitles:
            preview_times.extend((subtitle["start"] + subtitle["end"]) / 2 for subtitle in subtitles)
            labels.extend(f"subtitle-{i + 1}" for i in range(len(subtitles)))
        if clip_b:
            preview_times.append(duration_a + min(2.0, duration_b / 2))
            labels.append("second")
        if cta_path:
            # Sample each request in the sequence, including the platform-specific final action.
            prompt_offsets = (1.2, 4.0, 6.8) if args.cta == "sequence" else (1.2,)
            for prompt_index, offset in enumerate(prompt_offsets, start=1):
                preview_times.append(cta_start + min(offset, cta_duration / 2 if args.cta != "sequence" else cta_duration - 0.2))
                labels.append(f"cta-{prompt_index}" if args.cta == "sequence" else "cta")
        preview_paths = []
        for label, timestamp in zip(labels, preview_times):
            preview_path = preview_dir / f"{label}.png"
            run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-ss",
                    f"{timestamp:.6f}",
                    "-i",
                    str(output),
                    "-frames:v",
                    "1",
                    str(preview_path),
                ]
            )
            preview_paths.append(str(preview_path))
        summary["previews"] = preview_paths

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
