# Brand profile

## Portable use

The renderer requires `--watermark /path/to/approved-watermark.mov`. Supply the current project's approved transparent animated mark. Source clips, brand marks, and rendered engagement videos are not distributed with this skill.

Use an alpha-capable video such as ProRes 4444 MOV. The helper loops it throughout the Reel and scales it proportionally. It does not invent a missing brand asset. Check alpha, visible scale, placement, and any baked-in opacity before exporting.

The original CTA renderer is included as editable vector motion. Build the required platform/action once, then reuse the generated local assets. The complete sequence contains no brand mascot and is safe to use with another project's own approved mark.

## RecallDeck profile

Use the approved animated mascot plus exact lowercase `recalldeck.dev`, with roughly 80% visible opacity. Reuse the authorized project's existing watermark. When updating a personal installation that already contains `assets/recalldeck-watermark.mov`, preserve that asset and pass its path explicitly. Do not substitute a still logo or recreate the mascot without a request.

Starting placement at the default canvas size:

- Width 270 px, with height proportional to the supplied asset.
- Inside the sharp footage, bottom-left, inset 90 px.
- Move to another footage corner if a face, subtitle, or important action occupies that area.

These are defaults, not fixed safe zones. Inspect actual frames. The watermark must remain visible without becoming the main subject.

Cover graphics use blue `#005BB8`, navy `#061B31`, white `#FFFFFF`, and black when needed for contrast. Natural skin and footage colors are allowed. Preserve current project typography and approved mascot assets when provided.

Keep licensed source footage, reference portraits, project watermarks, generated covers, and their local paths in the project output directory. Publishing this skill does not grant rights to those assets.
