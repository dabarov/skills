# Figma production and handoff

The skill supplies decisions and layout guidance. It does not install or grant a Figma connection. Authoring needs a writable integration or an available Figma application session.

## Use the current provider

Inspect the requested file, pages, frames, and current styling before changing it. Preserve unrelated work. When the available tools require prerequisite skills, load those skills before the corresponding call. For the Codex Figma plugin, this includes `figma-use` for `use_figma`, `figma-create-new-file` before `create_new_file`, and `figma-generate-design` when translating a multi-section layout. Follow the installed provider's current instructions rather than copied API details.

Use a new version page for a substantial revision and preserve the previous final page. A small repair can update the requested component when the brief supports that. Name the final frame clearly, such as `FINAL v2 | 9 slides`. Put publishing notes in a separate frame.

## Editable or flattened

Build native text, shapes, and layout when editable Figma content is requested and supported. Use shared components or auto layout for repeated structures. Keep the export frame at the requested pixel dimensions and verify each child.

Placed PNGs are a reliable option for finished artwork when suitable for the request. Each is flattened. Keep an editable content and design source outside Figma and disclose the tradeoff. Do not describe a placed image as editable typography.

For an image import:

1. Export only the publishing slides to an ordered staging folder, using `01-cover.png`, `02-...png`, and so on.
2. Place all slides and explicitly inspect the order. File-picker sorting can differ from filename sorting.
3. Put them in horizontal auto layout with a 32 px gap by default.
4. Verify the cover is first, numbers increase, the close is last, and every child has the expected dimensions.
5. Keep notes and contact sheets outside the publishing strip.

For UI operations, follow the current computer-use documentation and observe fresh application state after actions. Avoid embedding platform-specific key combinations into reusable instructions when a direct integration can do the job.

## Export and inspect

Export the final Figma frames or authoritative local sources as ordered PNGs. Keep a contact sheet and the editable source. Verify the slide count, dimensions, spelling, line breaks, and image appearance. Link the actual final frame, not just the file's home page.

Leave the correct final page selected and the strip visible at a useful zoom when UI access allows it. Confirm the final result from fresh state or a screenshot; a successful tool response alone may not prove every image was placed correctly.

## When access fails

If the write tool reports a quota, permissions problem, expired session, or unavailable capability, stop repeating the same failed call. Finish the local artwork and publishing copy, describe the blocker, and provide an ordered import kit and clear instructions. State whether the Figma file still contains an older version.

Never substitute a local export link for a claim that Figma was updated. Request missing access information only if needed to finish the requested integration. Creating a new account, changing plan, or purchasing access is outside this skill.

When the brief requires native editable Figma layers, keep that acceptance criterion explicit. A local SVG or content source can preserve work for later authoring; placing a PNG cannot satisfy it. Label the handoff as drafted, researched, rendered, or verified in Figma according to what actually happened, and identify the unfinished step.
