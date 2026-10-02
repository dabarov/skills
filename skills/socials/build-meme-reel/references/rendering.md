# Rendering with the bundled helpers

Run commands from this skill's folder, or use absolute paths to its scripts. Keep sources, derivatives, and finished media in the project's output directory. Generated CTA caches are local build products.

## Dependencies and engagement assets

The video helper uses Python 3.9+ and FFmpeg/FFprobe with H.264, ProRes, `drawtext`, and the standard video/audio filters. It uses no third-party Python packages. The CTA renderer uses Node 20.9+ and the locked `sharp` dependency.

Install FFmpeg through the system's package manager if needed. Check `ffmpeg -version`, `ffprobe -version`, and `ffmpeg -filters`; an installation without `drawtext` will not render headlines.

```sh
npm ci
node scripts/render_engagement.cjs --tap --platform instagram --action sequence
```

That builds the 8.4-second Follow sequence under `generated/engagement/tap`. For a YouTube version, build the Subscribe sequence:

```sh
node scripts/render_engagement.cjs --tap --platform youtube --action sequence
```

Use `--platform tiktok` if the selected output is TikTok. `--action like|comment|follow` creates a 3.2-second single action only when that narrower prompt is requested. Omit `--tap` for the quiet style, which writes under `generated/engagement`. `--output /path/to/cache` selects another asset directory; pass the same directory to the video helper with `--cta-dir`.

The assets use silent straight-alpha ProRes 4444. Inspect the renderer's preview SVG/PNG files and manifest. A custom `--comment 'Your take?'` must fit the compact pill. Restore the standard Comment wording before reusing a campaign-specific cache for another Reel.

If the personal installation already has approved engagement assets, reuse them with `--cta-dir /path/to/engagement/tap`. There is no need to rebuild identical approved motion. The legacy RecallDeck installation stores those assets under `assets/engagement` and `assets/engagement/tap`.

## Single source

```sh
python3 scripts/build_reel.py \
  --clip-a source.mp4 --start-a 12 --end-a 28 \
  --title-a 'WHEN THE FIRST PROMPT FAILS' \
  --watermark approved-watermark.mov \
  --output output/reel.mp4 \
  --preview-dir output/previews
```

Inputs use source timestamps. Seconds, `MM:SS`, and `HH:MM:SS.mmm` are supported. The output starts at zero. The helper validates the trim, watermark and CTA placement, then prints render details as JSON. Save those details with the output. `--dry-run` prints the planned command without rendering; `--overwrite` permits replacing a derivative.

The helper rejects known non-square-pixel sources so their display proportions cannot be silently squeezed. Check the source's pixel/display aspect ratio and normalize it into a derivative before assembly when needed:

```sh
ffmpeg -i anamorphic-source.mp4 \
  -vf 'scale=trunc(iw*sar/2)*2:ih,setsar=1' \
  -c:v libx264 -crf 18 -c:a copy square-pixel-source.mp4
```

Inspect the resulting face proportions and framing. This is a source compatibility step applied equally to clean and cinema exports, not part of the cinema effect.

`--footage-effect cinema` enables the optional texture. It is off by default. See [cinema.md](cinema.md).

## Two-source comparison

```sh
python3 scripts/build_reel.py \
  --clip-a before.mp4 --start-a 2 --end-a 8 --title-a 'FIRST PROMPT' \
  --clip-b after.mp4 --start-b 1 --end-b 9 --title-b 'SECOND PROMPT' \
  --watermark approved-watermark.mov \
  --output output/comparison.mp4 --preview-dir output/previews
```

Each clip keeps its own dialogue and timing. The helper converts audio to 48 kHz stereo before the hard cut, normalizes loudness, and overlays one engagement sequence across the completed timeline. B's omitted trim uses its whole source.

## Separate audio or clean source derivatives

The helper expects video and audio in each clip. When they arrive separately, first create a synchronized derivative. Determine whether audio timestamps refer to the full source or an already trimmed excerpt before cutting; do not guess by applying the video offset to both.

For already aligned full-length inputs:

```sh
ffmpeg -i video.mp4 -i audio.mp4 \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac \
  -shortest combined-source.mp4
```

Inspect duration and sync before trimming. `-shortest` stops at the shorter stream; investigate an unexpected duration difference instead of silently losing a dialogue beat. Crop or mirror only in a specifically requested derivative. Preserve the original files.

## Complete CTA on short clips

Default automatic placement needs at least 11.4 seconds: two seconds before an 8.4-second sequence and one clean second after. An explicit `--cta-at 0` can fit in 9.4 seconds. Try an earlier permitted start before extending anything.

The helper deliberately rejects a sequence that cannot fit. If there is no fixed runtime and the scene can tolerate a hold, trim the intended scene into a derivative and extend its last frame with silent audio padding. For an 8-second trimmed clip that needs an 11.4-second derivative:

```sh
ffmpeg -i trimmed-source.mp4 \
  -vf 'tpad=stop_mode=clone:stop_duration=3.4' \
  -af 'apad' -t 11.4 \
  -c:v libx264 -crf 18 -c:a aac padded-source.mp4
```

Use the actual durations. Report the 3.4-second hold in this example. Do not slow speech, repeat the joke, or truncate the CTA to make it fit. A fixed runtime takes precedence over automatic extension; report the incompatibility if neither placement nor the requested scope permits a complete sequence.

## Text, placement, and timed captions

Use `--font /path/to/bold.ttf` to choose an installed brand font. The helper tries known bold system fonts if one is not specified. It does not bundle commercial fonts.

Headlines are uppercase and limited to two explicit lines. They are not automatically wrapped. Use a shorter provisional headline or intentional line breaks. Exact copy may need `--font-size` or `--title-y` adjustment, followed by inspection. Reject clipping; do not hide it by reducing type below readable size.

`--captions-json` replaces the static title for a single clip. Its list uses output-relative `start`, `end`, `text`, and optional `font_size` and `y`. Ends are exclusive; gaps remain free of captions. Use only when the user requests a timed headline. For dialogue beneath the headline, use additive `--subtitles-json` and read [subtitles.md](subtitles.md).

```json
[
  {"start": 0, "end": 3, "text": "FIRST PROMPT"},
  {"start": 5, "end": 9, "text": "SECOND PROMPT"}
]
```

Watermark position can change with `--watermark-corner`, `--watermark-width`, and `--watermark-margin`. CTA position can change with `--cta-x`, `--cta-y`, and `--cta-width`. Defaults target the 1080 × 1920 layout; recheck all coordinates after a canvas change.

`--preview-dir` exports representative scenes, timed-caption states when applicable, subtitle cues when supplied, and all three CTA states. Inspect them and watch the video with audio. Preview creation is not a substitute for playback. Confirm H.264/AAC, dimensions, frame rate, duration, watermark, subtitles, and full engagement sequence before handoff.

## Verify the installed helpers

After `npm ci`, a synthetic check can confirm the local renderer without requiring movie footage, faces, or a project watermark:

```sh
python3 scripts/verify_reel.py
```

It renders clean and cinema versions plus a two-source comparison, verifies resolution, timing, CTA fit, and audio, and exercises meaningful input rejections. Temporary media is removed after success. Use `--output-dir /path/to/test-output` to keep the files for visual inspection. These test patterns verify mechanics; they are not publishable meme artwork or cover examples.
