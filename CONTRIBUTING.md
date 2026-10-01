# Contributing

I welcome corrections that make a workflow more reliable or easier to use. A small change backed by a real example is useful.

## Improve an existing skill

Describe the prompt you tried, what happened, and what you expected. Include the specific correction that improved the result. A screenshot helps with spacing, hierarchy, or cropping issues.

Keep private conversations, client details, credentials, and personal file paths out of issues and pull requests. Use an anonymized brief or a small public example.

## Add a skill

Open an issue first if the scope needs discussion. A proposed skill should solve a recurring task you have actually used.

- Put it in `skills/<category>/<skill-name>/`.
- Match the folder name to the `name` in `SKILL.md` frontmatter.
- Explain what triggers the skill and what it delivers.
- Keep the main instructions focused. Put detailed guidance in `references/` and reusable materials in `assets/`.
- Document required tools and distinguish editable source files, flattened images, and native editable objects.
- Add a short example prompt and update the README catalog and `skills.sh.json` group.

Use direct language. Avoid em dashes, filler, unsupported claims, and instructions that ask for approval when the user has already authorized the work. Preserve the user's explicit brief over a skill's defaults.

Do not bundle third-party artwork, logos, or licensed resources without permission and clear attribution. Original contributions are made under this repository's [MIT license](LICENSE).

## Check the change

From the repository root, run:

```sh
python3 scripts/validate.py
```

The checks validate the package. Also try a representative prompt in an agent with the tools the skill requires. For a visual workflow, inspect the exported slides at publishing size and at a phone-sized preview.

In the pull request, say what changed, why, and how you checked it. Note any parts you could not verify.
