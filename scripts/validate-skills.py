#!/usr/bin/env python3
"""Validate agent skills under skills/*/SKILL.md.

Checks the YAML frontmatter fields and that skill-internal files referenced from
SKILL.md exist. Usage: python scripts/validate-skills.py [repo_root]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_DESCRIPTION = 1024
# Skill-internal paths mentioned in prose or backticks, e.g. `reference/category-rules.md`.
INTERNAL_PATH_RE = re.compile(r"(?<![\w./-])((?:reference|scripts|templates)/[\w./-]+\.\w+)")
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
URL_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)


def parse_frontmatter(text: str) -> tuple[dict | None, str, str | None]:
    """Split SKILL.md text into (frontmatter, body, error)."""
    lines = text.split("\n")
    if lines[0].strip() != "---":
        return None, text, "missing YAML frontmatter (file must start with '---')"
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            body = "\n".join(lines[i + 1:])
            try:
                data = yaml.safe_load("\n".join(lines[1:i]))
            except yaml.YAMLError as exc:
                return None, body, f"frontmatter is not valid YAML: {exc}"
            if not isinstance(data, dict):
                return None, body, "frontmatter must be a YAML mapping"
            return data, body, None
    return None, text, "frontmatter is not closed (missing second '---')"


def referenced_paths(body: str) -> set[str]:
    """Relative file paths SKILL.md expects to exist inside its skill directory."""
    paths = set(INTERNAL_PATH_RE.findall(body))
    for target in LINK_RE.findall(body):
        # Skip URLs, in-page anchors, and template placeholders like (<url>).
        if URL_SCHEME_RE.match(target) or target.startswith(("#", "<")):
            continue
        paths.add(target.split("#", 1)[0])
    return {p for p in paths if p}


def validate_skill(skill_dir: Path) -> list[str]:
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return [f"{skill_dir}: missing SKILL.md"]
    # utf-8-sig drops a BOM; text mode normalizes CRLF to LF.
    try:
        text = skill_file.read_text(encoding="utf-8-sig")
    except (UnicodeDecodeError, OSError) as exc:
        return [f"{skill_file}: cannot read as UTF-8: {exc}"]
    data, body, error = parse_frontmatter(text)
    if error:
        return [f"{skill_file}: {error}"]

    errors = []
    name = data.get("name")
    if not isinstance(name, str) or not NAME_RE.match(name):
        errors.append(f"{skill_file}: 'name' must be kebab-case, got {name!r}")
    elif name != skill_dir.name:
        errors.append(f"{skill_file}: 'name' {name!r} does not match directory {skill_dir.name!r}")

    description = data.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(f"{skill_file}: 'description' is required")
    else:
        if not description.startswith("Use when"):
            errors.append(f"{skill_file}: 'description' must start with 'Use when'")
        if len(description) > MAX_DESCRIPTION:
            errors.append(
                f"{skill_file}: 'description' is {len(description)} chars (max {MAX_DESCRIPTION})"
            )

    tools = data.get("allowed-tools")
    if not isinstance(tools, list) or not tools or not all(isinstance(t, str) and t for t in tools):
        errors.append(f"{skill_file}: 'allowed-tools' must be a non-empty list of tool names")

    for rel in sorted(referenced_paths(body)):
        if not (skill_dir / rel).exists():
            errors.append(f"{skill_file}: references missing file {rel!r}")
    return errors


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(".")
    skills_root = root / "skills"
    skill_dirs = sorted(p for p in skills_root.glob("*") if p.is_dir())
    if not skill_dirs:
        print(f"error: no skills found under {skills_root}", file=sys.stderr)
        return 1
    errors = [e for d in skill_dirs for e in validate_skill(d)]
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    if errors:
        return 1
    print(f"ok: {len(skill_dirs)} skill(s) valid")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
