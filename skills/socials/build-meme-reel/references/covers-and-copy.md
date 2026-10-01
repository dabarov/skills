# Covers and platform copy

## Select the face before designing

Extract candidate stills from the cleaned source footage, not from the finished vertical canvas. Look for a recognizable human face with a readable expression. Avoid mid-blinks, motion blur, existing subtitles, and baked-in meme text. View the actual still before using it as a reference.

Choose the expression for the joke: confidence before a bad decision, disbelief at the result, or exhaustion after the task. An object can support the premise, but it cannot replace the face. If the supplied footage has no usable human face, use a relevant portrait supplied or approved for this project. Ask for that missing source if none is available; do not fabricate a specific person's identity or use an unrelated stock face.

```sh
ffmpeg -ss 4.2 -i cleaned-source.mp4 -frames:v 1 face-reference.png
```

Choose a timestamp after inspecting the scene. This command is an example, not a face detector.

## Four separate files

| Output | Size | Filename |
| --- | --- | --- |
| TikTok cover | 1080 × 1920 | `tiktok-cover.jpg` |
| Instagram Reel cover | 1080 × 1920 | `instagram-reel-cover.jpg` |
| YouTube Shorts cover | 1080 × 1920 | `youtube-shorts-cover.jpg` |
| YouTube thumbnail | 1920 × 1080 | `youtube-thumbnail-wide.jpg` |

These are production defaults, not claims about a platform's current upload requirements. Deliver original full-size files, not screenshots, contact sheets, or phone mockups. A contact sheet is useful for review in addition to the individual files.

Build the wide thumbnail as its own composition. Do not crop the portrait cover and call it finished. Keep the face and essential words within the central area of portrait art so centered 3:4 and 4:5 crops remain intelligible. Inspect those crops; a fixed percentage alone is not a check.

Use a short headline that matches the joke without copying the entire video caption. Prefer a clear phrase of two to six words when it carries the meaning. Use strong blue accents, black or navy structure, and white type. RecallDeck's starting colors are blue `#005BB8`, navy `#061B31`, and white `#FFFFFF`; the current approved project tokens take precedence within that palette.

Use contrast and scale to separate the face from the headline. Keep type out of the eyes and mouth. Check tiny-size legibility and intentional line breaks. Do not add platform UI, engagement pills, a fake play button, or a stack of decorative labels.

## Image generation

Use the host's image-generation tool and read its skill before calling it. Include the inspected source face reference, requested dimensions/aspect ratio, exact headline, and blue/black/white graphic treatment. Preserve the person's identity, expression, and scene context. Generate independent compositions for distinct formats; do not ask for a four-panel collage as the final deliverable.

If the generator misses exact type or branding, add those elements with a measured layout after generation. Do not distort generated artwork to force dimensions. Extend the background or crop after checking that the face and headline survive.

If generation is unavailable or fails, make a face-based composition from the inspected source still with the same palette and exact type, and identify it as a source-frame fallback. If the user explicitly requires generated covers, report that limitation and seek approval for the fallback. Never deliver an object-only cover or switch to amber/cream as a workaround.

Save reusable prompts, selected reference timestamps, and final dimensions alongside the output. Keep private source paths and reference photos out of a public repository.

## Instagram paragraph

Write one connected paragraph that expands the specific premise of the on-video caption. Relate the scene's action or dialogue to the observation that makes the meme funny. The paragraph should be understandable without naming a film character and should add something beyond narrating the clip.

For a video caption about an AI tool missing the point on the first prompt, a useful direction is expectations versus instructions:

> You give the model a vague prompt, expect it to read your mind, and start questioning the whole tool when the first answer misses the point. Then you add the context you left out and the second answer suddenly looks impressive. Half the argument about AI quality is really an argument about how clearly we explained the task.

This is an original writing example, not copy to append to every AI meme. For a paid-tokens/free-model joke, discuss that exact downgrade and expectations. For a manager joke, discuss the behavior shown in the scene. Avoid unrelated interview preparation promotions.

No automatic hashtags, blank-line splits, generic engagement closer, or boilerplate brand pitch. A paragraph can be a few sentences; it should not become one long sentence. Preserve requested tone and factual limits.

TikTok copy can be shorter and more immediate. YouTube Shorts gets a title and description appropriate to the same joke. Do not reuse the Instagram paragraph mechanically across all platforms. Save the final copy in `social-covers/captions.md` and show it in the handoff.

## Upload guidance

Only explain current cover selection or publishing steps when requested, and verify those steps against official platform guidance. Cover controls differ by platform, account, and upload route. If a frame-only picker needs a cover embedded into a video, create a separate derivative only when requested and disclose its timing; preserve the approved original.
