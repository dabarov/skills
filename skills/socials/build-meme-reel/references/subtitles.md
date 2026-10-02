# Dialogue subtitles

Burn dialogue into the finished MP4 so it remains visible when platform captions are disabled. Preserve the approved cut, speech, pause, headline, watermark, and complete engagement sequence. Reuse the approved covers and platform copy for a subtitle-only repair.

## Wording and timing

Transcribe the selected audio. Speech recognition can provide a draft, but check names, accents, slang, short questions, and punchlines against the source. Correct a misheard line rather than copying an automatic transcript. Preserve spoken grammar and meaning; subtitles are not a rewrite of the dialogue. Identify a genuinely inaudible word instead of inventing it.

Use the finished video's timeline, starting at zero. For multiple source clips, account for every trim and cut before setting cue times. Keep the source and output timestamps separate. Let a short phrase appear with its speech and clear before the next phrase. Leave the scene's silent pause empty, and do not reveal a later response early.

Prefer one line with a few words per cue. Split a long sentence at a natural phrase boundary instead of shrinking the type. Use two lines only when they fit a deliberately chosen clear region. Avoid word-by-word bouncing or highlighted karaoke text unless requested.

Save the corrected cues as JSON and matching SRT. An SRT sidecar supports reuse; it does not replace the visible text in the MP4.

## Placement

At the default 1080 × 1920 layout, start with 46 px bold white type, a dark outline, and 12 px translucent black padding. The helper starts one-line dialogue near the lower edge of the sharp footage, above the engagement animation and below the usual watermark position. These values are layout defaults, not guarantees about platform controls.

Inspect the actual scene and all timed assets. Keep text and its backing clear of the headline, mascot and domain, engagement pills and cursor, eyes, mouths, and the action. Check a phone-size view with room for platform controls and account text. If the default region conflicts, move the subtitles or split the cue; do not cover the assets or reduce text to an unreadable size.

The helper rejects measured subtitle boxes that overlap the headline, watermark, or active engagement animation. This catches layout collisions, but it cannot identify faces or the current platform interface. Check those visually.

## Render

`--subtitles-json` is additive. `--captions-json` remains a timed replacement for the headline and is a separate feature.

```json
[
  {"start": 0.6, "end": 1.8, "text": "Does it pass?"},
  {"start": 4.2, "end": 5.4, "text": "On my machine."}
]
```

```sh
python3 scripts/build_reel.py \
  --clip-a source.mp4 --start-a 12 --end-a 28 \
  --title-a 'WHEN THE TESTS FINALLY PASS' \
  --subtitles-json dialogue.json \
  --watermark approved-watermark.mov \
  --output output/reel-subtitled.mp4 \
  --preview-dir output/subtitle-previews
```

Use `--subtitle-font-size`, `--subtitle-y`, and `--subtitle-max-width` to adjust the subtitle region. Keep the same corrected cues across Instagram, TikTok, and YouTube exports. Switching Follow to Subscribe must not alter dialogue timing.

Inspect every cue preview, especially the longest phrase, the payoff, and cues near an active CTA. Watch the result with sound and verify that the SRT and JSON agree with the burned text. Deliver the revised MP4s and sidecars while retaining the prior approved video when repairing an existing package.
