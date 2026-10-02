---
name: build-meme-reel
description: Create or repair social meme Reels from source clips, with dialogue subtitles, optional cinema-screen texture, animated engagement prompts, face-led covers, and platform captions. Use for footage-based memes, not general promotional videos or carousels.
---

# Build Meme Reel

Turn a specific scene and joke into a complete social package. Preserve dialogue, timing, and the pause that makes the joke work. Use the bundled FFmpeg workflow for repeatable exports.

## Deliverable and scope

A new Reel includes:

- A finished vertical MP4 with the approved brand watermark and compact animated Like → Comment → Follow sequence. Use Subscribe for YouTube.
- Readable dialogue subtitles burned into each platform version, with matching SRT and timing data. Omit them when the user requests a subtitle-free version or the scene contains no speech.
- Four separate full-size covers: TikTok, Instagram Reel, YouTube Shorts, and a landscape YouTube thumbnail.
- Platform copy saved with the covers. Instagram gets one connected paragraph grounded in this video's premise.
- Preview images and render details so the result can be checked.

An explicit request for only a caption, cover, or repair narrows that scope. Reuse approved footage and copy when editing one part. State a missing deliverable plainly; do not call an incomplete package finished.

Read [rendering.md](references/rendering.md) before using the helpers. Read [covers-and-copy.md](references/covers-and-copy.md) when making covers or platform captions.

## Understand the scene

Inspect the supplied media, including its audio, before choosing the cut or writing the headline. Check whether separate video and audio inputs need combining. Keep source timestamps distinct from the finished Reel timeline.

Identify the setup, recognition moment, and payoff. Preserve the beginning of a question, the response, and any intentional pause. For a comparison, keep each beat legible and use a hard cut unless the user asks for another transition.

Keep prescribed wording intact apart from requested corrections. Tighten provisional wording into one clear sentence, normally no more than two lines. Do not add extra narration, music, or meme labels by default.

## Assemble the Reel

Default layout:

| Element | Starting point |
| --- | --- |
| Canvas | 1080 × 1920 px, 30 fps, square pixels |
| Sharp footage | 1000 × 562 px, centered, aspect ratio preserved |
| Background | Moving blurred fill from the same active footage, darkened but still visibly colored |
| Headline | Bold white uppercase above the footage, centered in a translucent black box |
| Export | H.264, AAC audio, MP4 with fast start |

Use the actual source dimensions and inspect containment. Do not stretch faces. Crop old meme borders, existing titles, or subtitles only when requested or needed to honor an agreed clean-source brief. Mirroring and replacement audio are per-video choices.

Use the project's approved animated watermark. For RecallDeck, use the mascot with exact lowercase `recalldeck.dev`, slightly transparent, inside a corner of the sharp footage. Keep it clear of faces, subtitles, and the action. Read [branding.md](references/branding.md) for the profile and portable setup. Do not substitute a new logo when the approved asset is missing.

Include the complete compact engagement sequence once during the video. Use translucent pills, an arrow cursor, and pressed states: Like → Liked, Comment → Commented, Follow → Following. Keep the pill centered through label changes. It contains no mascot. Default to the tap style; use quiet or a single action only when requested.

The sequence lasts 8.4 seconds and must finish at least one second before the video ends. Try an earlier start for short clips. If a hard runtime is absent, a disclosed final-frame hold with silent audio padding can make room; never stretch dialogue, loop the joke, shorten the sequence, or omit it silently. If runtime is fixed and the sequence cannot fit, report the conflict.

## Dialogue subtitles

Add verified dialogue subtitles to spoken scenes. Use short phrases in bold white type with a dark outline and translucent backing. Keep them separate from the headline, approved watermark, engagement animation, and the faces carrying the joke. Leave an intentional silent pause free of subtitle text.

Read [subtitles.md](references/subtitles.md) before transcribing or placing them. The helper's `--subtitles-json` adds dialogue without replacing the headline. Check phone-size readability and the intended platforms' visible controls; a fixed safe-area rectangle alone is not a platform preview.

## Optional cinema-screen treatment

Use `--footage-effect cinema` only when requested. Default to `clean`.

The effect adds soft focus, subdued saturation, washed blacks, fine grain, a mild vignette, and small exposure flicker to the footage before layout assembly. Headline, watermark, and engagement graphics remain crisp. **Keep picture sizing, placement, aspect ratio, and dialogue timing unchanged.**

Perspective skew, handheld drift, zoom, mirroring, and cropping are separate choices. Do not add them to the default cinema treatment. See [cinema.md](references/cinema.md) for the implemented values and checks.

## Covers and copy

Every cover must contain a visible human face. Prefer a sharp, expressive face from the actual scene. Do not replace it with a diary, object, empty set, silhouette, or unrelated stock portrait just to fill the package.

Use blue, black, and white for cover typography, panels, and overall graphic treatment. Natural skin and footage colors can remain. Do not adopt the film's amber, cream, or green palette as the thumbnail style. Keep the face and headline readable at phone size and in centered portrait crops.

Use the available image-generation tool for finished raster covers, following its own skill. Inspect the reference face first, preserve its identity and expression, and compose each format separately. A generator failure does not relax the face or palette requirements. Follow the fallback rules in [covers-and-copy.md](references/covers-and-copy.md).

Write Instagram copy as **one paragraph** about the on-video caption, scene, and underlying topic. Expand the observation or tension behind the joke. Do not output a generic setup/punchline list, hashtag block, or automatic Like/Comment/Follow closer. A named hashtag belongs only when the user specifically requests it.

## Check and deliver

- Watch the cut with sound. Check the start, payoff, pause, and ending; preserve the intended audio sync.
- Inspect the headline, sharp footage, watermark, and each of the three CTA states. Check that text stays inside its box and the sequence finishes in time.
- Inspect every subtitle cue with the assets active, including the longest phrase and payoff. Check wording, timing, visible bounds, and phone-size readability. Confirm the matching SRT uses the finished video's timeline.
- For cinema exports, compare against the clean layout. Confirm only footage quality changed.
- Open all four cover files at full resolution and at phone size. Verify a visible face, the blue/black/white treatment, readable text, exact branding, and dimensions.
- Read the Instagram paragraph alongside the on-video headline. If it could accompany an unrelated meme unchanged, rewrite it.

Deliver the video, all four covers, and platform copy with direct links. Report runtime, source trim, any hold padding, and whether the cinema option was used. When the host supports reusable writing blocks, put each platform caption in its own social-post block. Do not publish, upload, or message people unless that action is authorized.
