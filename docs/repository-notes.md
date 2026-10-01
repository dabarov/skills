# Repository notes

This collection records workflows I use. The repository gives visitors enough context to try them, inspect them, and suggest a concrete improvement.

## Presentation

[Matt Pocock's skills](https://github.com/mattpocock/skills) opens with a personal explanation and puts installation near the top. This repository follows that order and keeps the introduction short.

[Impeccable](https://github.com/pbakaus/impeccable) connects its promise to usage examples and visible design work. Here, one banner establishes the collection's identity and a clearly labeled illustrative carousel shows the layout direction. It is not presented as a completed Figma demo.

[Corey Haines's marketing skills](https://github.com/coreyhaines31/marketingskills) uses a linked catalog and category navigation. This collection uses a small catalog under Socials, with room for other categories when there are actual skills to add.

## Packaging

The [Agent Skills specification](https://agentskills.io/specification) defines the skill folder, frontmatter, relative references, and optional resources. Each skill here travels as a complete folder. Detailed guidance lives beside the main instructions so agents can read it when needed.

[Vercel's skills CLI](https://github.com/vercel-labs/skills) supports repository installation, named skill selection, and category folders under `skills/`. The README includes both a CLI path and a manual copy. The [discovery implementation](https://github.com/vercel-labs/skills/blob/main/src/skills.ts) documents the bounded scan of skill containers.

[Vercel's agent-skills repository](https://github.com/vercel-labs/agent-skills/blob/main/skills.sh.json) groups its catalog with `skills.sh.json`. This repository uses the same supported configuration to label the first group Socials. The format is defined by the [official schema](https://www.skills.sh/schemas/skills.sh.schema.json).

The [official Codex guide](https://learn.chatgpt.com/docs/build-skills) lists `~/.agents/skills` for personal skill discovery. The manual installation uses that location and copies supporting files with the main instructions.

## Scope and expectations

The format is portable. Tool capabilities still depend on the agent and its connected provider. A Figma workflow requires writable access and the provider's own setup instructions. A placed PNG remains flattened in Figma even when its source layout is editable.

The first skill's publishing cap is 10 slides including the hook and call to action. Its 1080 × 1350 canvas, 64 px safe margin, and 32 px Figma gap are workflow defaults. They can change with a brief; they are not claims about platform requirements.

The meme skill includes the original FFmpeg and vector-engagement helpers, with a locked Node dependency. Generated motion caches are built locally rather than stored as duplicate videos. The optional cinema texture changes footage quality while preserving geometry. Face-led covers and one-paragraph Instagram copy reflect corrections from actual use.

Personal media, private conversation logs, third-party movie stills, and project watermarks are not published. A separate brand profile explains how to supply the approved mark.

The repository distributes original instructions and illustrative artwork under MIT. Referenced third-party visual libraries and brand marks keep their own licensing terms and are not bundled.

The launch keeps badges and popularity claims out of the README. Useful examples, a working install path, and clear dependencies give visitors more to judge than decoration alone.
