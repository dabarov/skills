#!/usr/bin/env python3
"""Check the collection's package fields, local links, catalog, and artwork.

Uses Python's standard library. This is a packaging check, not a full YAML
parser or a substitute for trying a skill on a representative task.
"""

import argparse
import json
import re
import struct
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree


def validate(root):
    root = root.resolve()
    errors = []

    def fail(path, message):
        errors.append(f"{path.relative_to(root)}: {message}")

    skills = sorted((root / "skills").glob("*/*/SKILL.md"))
    if not skills:
        errors.append("No skills found in skills/<category>/<name>/SKILL.md")
    names = set()
    for path in skills:
        content = path.read_text(encoding="utf-8")
        header = re.match(r"\A---\n(.*?)\n---(?:\n|$)", content, re.S)
        if not header:
            fail(path, "missing YAML frontmatter")
            continue
        fields = {}
        for line in header.group(1).splitlines():
            match = re.match(r"^([a-z][a-z-]*):\s*(.*)$", line)
            if match:
                key, value = match.groups()
                if key in fields:
                    fail(path, f"duplicate frontmatter field: {key}")
                fields[key] = value.strip().strip('\"\'')
        name = fields.get("name", "")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
            fail(path, "name must use lowercase letters, numbers, and hyphens")
        if name != path.parent.name:
            fail(path, "name differs from the skill folder")
        if name in names:
            fail(path, "duplicate skill name")
        names.add(name)
        description = fields.get("description", "")
        if not description or len(description) > 1024 or description in {"|", ">"}:
            fail(path, "use a nonempty single-line description of at most 1024 characters")
        if len(content.splitlines()) > 500:
            fail(path, "move conditional detail out of the main skill")
        metadata = path.parent / "agents" / "openai.yaml"
        if metadata.exists():
            prompt = re.search(r"default_prompt:\s*(.+)", metadata.read_text(encoding="utf-8"))
            if prompt and f"${name}" not in prompt.group(1):
                fail(metadata, "default_prompt must mention the skill with its $ name")

    # Check file links only. Public URLs and intra-page anchors are not fetched.
    for path in sorted(root.rglob("*.md")):
        if ".git" in path.relative_to(root).parts:
            continue
        text = path.read_text(encoding="utf-8")
        if "[TODO:" in text:
            fail(path, "unfinished scaffold placeholder")
        if "/Users/" in text or re.search(r"rollout-\d{4}-", text):
            fail(path, "private machine path or transcript reference")
        if "\u2014" in text or "\u2013" in text:
            fail(path, "use plain punctuation instead of em or en dashes")
        for line_no, line in enumerate(text.splitlines(), 1):
            if line.rstrip() != line:
                fail(path, f"trailing whitespace on line {line_no}")
        without_code = re.sub(r"```.*?```", "", text, flags=re.S)
        for target in re.findall(r"\]\(([^\s)]+)\)", without_code):
            target = target.strip("<>")
            parts = urlsplit(target)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            linked = (path.parent / unquote(parts.path)).resolve()
            if not linked.is_relative_to(root):
                fail(path, f"local link escapes the repository: {target}")
            elif not linked.exists():
                fail(path, f"missing local link: {target}")

    catalog = root / "skills.sh.json"
    if not catalog.exists():
        errors.append("skills.sh.json: missing category catalog")
    else:
        try:
            data = json.loads(catalog.read_text(encoding="utf-8"))
            grouped = []
            for group in data.get("groupings", []):
                if not group.get("title") or not group.get("skills"):
                    fail(catalog, "each grouping needs a title and skill list")
                grouped.extend(group.get("skills", []))
            for name in grouped:
                if name not in names:
                    fail(catalog, f"unknown catalog skill: {name}")
            for name in names - set(grouped):
                fail(catalog, f"skill missing from the category catalog: {name}")
            if len(grouped) != len(set(grouped)):
                fail(catalog, "a skill appears in multiple catalog entries")
        except (ValueError, TypeError, AttributeError) as exc:
            fail(catalog, f"invalid catalog: {exc}")

    for path in sorted((root / "docs").rglob("*.svg")):
        try:
            ElementTree.parse(path)
        except ElementTree.ParseError as exc:
            fail(path, f"invalid SVG: {exc}")
    for path in sorted((root / "docs").rglob("*.png")):
        data = path.read_bytes()
        if data[:8] != b"\x89PNG\r\n\x1a\n" or len(data) < 24 or data[12:16] != b"IHDR":
            fail(path, "invalid PNG header")
            continue
        width, height = struct.unpack(">II", data[16:24])
        if width == 0 or height == 0:
            fail(path, "empty PNG dimensions")
        if path.parent.name == "example" and (width, height) != (1080, 1350):
            fail(path, "example slide must be 1080 x 1350")

    return skills, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        parser.error("root must be an existing collection directory")
    skills, errors = validate(root)
    if errors:
        print("Validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"Validated {len(skills)} skill package(s), local links, catalog, and example artwork.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
