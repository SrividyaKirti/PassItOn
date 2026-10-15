# PassItOn Skill v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the `/passiton` agent skill (research + drafts for passing on an unneeded item) with CI on pull requests, tag-based releases, and a protected `main`.

**Architecture:** One self-contained `skills/passiton/SKILL.md` playbook plus `reference/category-rules.md`, using only built-in agent tools. A stdlib + PyYAML validator script checks skill frontmatter and referenced files; GitHub Actions run it plus markdownlint and lychee on PRs; pushing a `v*.*.*` tag on `main` publishes a zipped skill as a GitHub Release.

**Tech Stack:** Markdown (skill), Python 3.12 + PyYAML + pytest (validator), GitHub Actions, markdownlint-cli2 (via npx), lychee (lycheeverse/lychee-action@v2), `gh` CLI.

**Spec:** `docs/superpowers/specs/2026-10-15-passiton-skill-design.md`

## Global Constraints

- All work is committed on branch `v1.0`; nothing is committed or pushed directly to `main`.
- v1 is research + drafts only: the skill never logs in, posts, fills forms, or messages anyone.
- Every factual claim in a plan (price, acceptance, hours, recall status) cites a source URL; unconfirmed acceptance is labeled exactly `Unverified — call first`.
- Listing/outreach text never contains the user's address, phone, email, or full name.
- Recalled/expired/banned items get no sale, donation, or giveaway listings.
- Skill frontmatter: `name` kebab-case and equal to directory name; `description` starts with `Use when` and is ≤ 1024 chars; `allowed-tools` is a non-empty list.
- Skill `allowed-tools`: `Read`, `Write`, `Glob`, `WebSearch`, `WebFetch`, `AskUserQuestion`.
- Plan output path: `./passiton/<item-slug>/plan.md`; slug is lowercase letters, digits, hyphens.
- Release tags match `v*.*.*`; release asset is `passiton-skill-<tag>.zip` containing `passiton/`.
- Branch protection is changed only after the repo owner explicitly confirms.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. A `SKILL.md` that is missing frontmatter, has it unclosed, has invalid YAML, or has a UTF-8 BOM / CRLF line endings — the validator should print a clear error (or parse correctly for BOM/CRLF), never a Python traceback. Pinned in Task 1 tests.
2. No `skills/` directory or no skills in it — the validator must fail, not print `ok`. Pinned in Task 1 tests.
3. A release tag pushed on a commit that is not on `main` — the release must stop before publishing. Pinned in Task 5, Step 3.
4. The user volunteers their phone number or address in their first message — it must not appear in any listing. Pinned in scenario S1 (Task 3) and checked in Task 4.
5. A photo path that doesn't exist plus a declined location — the run continues, notes both, and invents no local organizations. Pinned in scenario S3 (Task 3) and checked in Task 4.

---

## File Structure

| File | Responsibility |
|---|---|
| `scripts/validate-skills.py` | Validate every `skills/*/SKILL.md` (frontmatter + referenced files). |
| `tests/test_validate_skills.py` | pytest suite for the validator. |
| `requirements-dev.txt` | Python dev deps (PyYAML, pytest). |
| `.github/workflows/ci.yml` | PR/push CI: validator + tests, markdownlint, link check. Reusable via `workflow_call`. |
| `.github/workflows/release.yml` | Tag → verify on main → CI → zip → GitHub Release. |
| `.markdownlint.jsonc` | markdownlint rule config. |
| `.lycheeignore` | Link-check exclusions. |
| `.gitignore` | Ignore venv, caches, and local `/passiton/` run output. |
| `tests/scenarios.md` | Manual agent test scenarios with scripted answers and pass criteria. |
| `tests/results/<date>-baseline.md`, `tests/results/<date>-with-skill.md` | Recorded scenario runs. |
| `skills/passiton/reference/category-rules.md` | Per-category donation fit, safety rules, listing tips. |
| `skills/passiton/SKILL.md` | The skill playbook. |
| `README.md` | What it is, install, usage, contributing. |

---

### Task 1: Skill validator script

**Files:**
- Create: `requirements-dev.txt`
- Create: `.gitignore`
- Create: `scripts/validate-skills.py`
- Test: `tests/test_validate_skills.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `python scripts/validate-skills.py [repo_root]` → exit 0 and prints `ok: N skill(s) valid`, or exit 1 and prints `error: ...` lines to stderr. Python functions `parse_frontmatter(text: str) -> tuple[dict | None, str, str | None]`, `referenced_paths(body: str) -> set[str]`, `validate_skill(skill_dir: Path) -> list[str]`, `main(argv: list[str]) -> int`.

- [ ] **Step 1: Create dev requirements, .gitignore, and a venv**

`requirements-dev.txt`:

```text
pyyaml>=6.0
pytest>=8.0
```

`.gitignore`:

```text
.venv/
__pycache__/
.pytest_cache/
# Local output of running the skill inside this repo
/passiton/
```

Run:

```bash
python3 -m venv .venv && .venv/bin/pip install -q -r requirements-dev.txt
```

Expected: exits 0.

- [ ] **Step 2: Write the failing tests**

`tests/test_validate_skills.py`:

```python
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate-skills.py"
_spec = importlib.util.spec_from_file_location("validate_skills", SCRIPT)
vs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vs)

VALID = """---
name: demo
description: Use when testing the validator.
allowed-tools:
  - Read
  - Write
---

# Demo

Read `reference/rules.md` and [the guide](reference/guide.md). See [docs](https://example.com).
"""


def make_skill(root, name="demo", text=VALID, files=("reference/rules.md", "reference/guide.md")):
    skill_dir = root / "skills" / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(text, encoding="utf-8")
    for rel in files:
        path = skill_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")
    return skill_dir


def test_valid_skill_has_no_errors(tmp_path):
    assert vs.validate_skill(make_skill(tmp_path)) == []


def test_missing_skill_md(tmp_path):
    skill_dir = tmp_path / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    errors = vs.validate_skill(skill_dir)
    assert len(errors) == 1 and "missing SKILL.md" in errors[0]


def test_missing_frontmatter(tmp_path):
    errors = vs.validate_skill(make_skill(tmp_path, text="# Demo\n"))
    assert len(errors) == 1 and "missing YAML frontmatter" in errors[0]


def test_unclosed_frontmatter(tmp_path):
    errors = vs.validate_skill(make_skill(tmp_path, text="---\nname: demo\n"))
    assert len(errors) == 1 and "not closed" in errors[0]


def test_invalid_yaml(tmp_path):
    errors = vs.validate_skill(make_skill(tmp_path, text="---\nname: [demo\n---\n"))
    assert len(errors) == 1 and "not valid YAML" in errors[0]


def test_frontmatter_must_be_mapping(tmp_path):
    errors = vs.validate_skill(make_skill(tmp_path, text="---\n- a\n- b\n---\n"))
    assert len(errors) == 1 and "must be a YAML mapping" in errors[0]


def test_bom_and_crlf_are_accepted(tmp_path):
    skill_dir = make_skill(tmp_path)
    data = ("﻿" + VALID).replace("\n", "\r\n").encode("utf-8")
    (skill_dir / "SKILL.md").write_bytes(data)
    assert vs.validate_skill(skill_dir) == []


def test_name_must_be_kebab_case(tmp_path):
    skill_dir = make_skill(tmp_path, name="Demo_Skill", text=VALID.replace("name: demo", "name: Demo_Skill"))
    errors = vs.validate_skill(skill_dir)
    assert any("kebab-case" in e for e in errors)


def test_name_must_match_directory(tmp_path):
    errors = vs.validate_skill(make_skill(tmp_path, name="other"))
    assert any("does not match directory" in e for e in errors)


def test_description_required(tmp_path):
    text = VALID.replace("description: Use when testing the validator.\n", "")
    errors = vs.validate_skill(make_skill(tmp_path, text=text))
    assert any("'description' is required" in e for e in errors)


def test_description_must_start_with_use_when(tmp_path):
    text = VALID.replace("Use when testing", "Tests")
    errors = vs.validate_skill(make_skill(tmp_path, text=text))
    assert any("must start with 'Use when'" in e for e in errors)


def test_description_max_length(tmp_path):
    text = VALID.replace("Use when testing the validator.", "Use when " + "x" * 1100)
    errors = vs.validate_skill(make_skill(tmp_path, text=text))
    assert any("max 1024" in e for e in errors)


def test_allowed_tools_required(tmp_path):
    text = VALID.replace("allowed-tools:\n  - Read\n  - Write\n", "")
    errors = vs.validate_skill(make_skill(tmp_path, text=text))
    assert any("'allowed-tools'" in e for e in errors)


def test_allowed_tools_must_be_non_empty_list(tmp_path):
    for i, value in enumerate(("allowed-tools: []\n", "allowed-tools: Read\n")):
        text = VALID.replace("allowed-tools:\n  - Read\n  - Write\n", value)
        errors = vs.validate_skill(make_skill(tmp_path / str(i), text=text))
        assert any("'allowed-tools'" in e for e in errors), value


def test_missing_backtick_reference(tmp_path):
    errors = vs.validate_skill(make_skill(tmp_path, files=("reference/guide.md",)))
    assert errors == [f"{tmp_path / 'skills' / 'demo' / 'SKILL.md'}: references missing file 'reference/rules.md'"]


def test_missing_link_reference(tmp_path):
    errors = vs.validate_skill(make_skill(tmp_path, files=("reference/rules.md",)))
    assert any("'reference/guide.md'" in e for e in errors)


def test_referenced_paths_ignores_urls_anchors_and_placeholders():
    body = (
        "See [a](https://example.com/reference/a.md), [b](#top), [c](mailto:a@b.c), "
        "[source](<url>), `reference/r.md`."
    )
    assert vs.referenced_paths(body) == {"reference/r.md"}


def test_referenced_paths_strips_link_anchor():
    assert vs.referenced_paths("[g](reference/guide.md#intro)") == {"reference/guide.md"}


def test_main_ok(tmp_path, capsys):
    make_skill(tmp_path)
    assert vs.main(["validate-skills.py", str(tmp_path)]) == 0
    assert "ok: 1 skill(s) valid" in capsys.readouterr().out


def test_main_reports_errors(tmp_path, capsys):
    make_skill(tmp_path, text="# no frontmatter\n")
    assert vs.main(["validate-skills.py", str(tmp_path)]) == 1
    assert "error:" in capsys.readouterr().err


def test_main_fails_when_no_skills(tmp_path, capsys):
    assert vs.main(["validate-skills.py", str(tmp_path)]) == 1
    assert "no skills found" in capsys.readouterr().err
    (tmp_path / "skills").mkdir()
    assert vs.main(["validate-skills.py", str(tmp_path)]) == 1
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_validate_skills.py -q`
Expected: collection error, `FileNotFoundError` for `scripts/validate-skills.py`.

- [ ] **Step 4: Write the implementation**

`scripts/validate-skills.py`:

```python
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
    data, body, error = parse_frontmatter(skill_file.read_text(encoding="utf-8-sig"))
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_validate_skills.py -q`
Expected: all tests pass (21 passed).

- [ ] **Step 6: Commit**

```bash
git add requirements-dev.txt .gitignore scripts/validate-skills.py tests/test_validate_skills.py
git commit -m "Add skill validator script with tests

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: CI workflow and lint configuration

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.markdownlint.jsonc`
- Create: `.lycheeignore`
- Modify (only if lint reports issues): existing `*.md` files

**Interfaces:**
- Consumes: `scripts/validate-skills.py`, `requirements-dev.txt`, `tests/` (Task 1).
- Produces: workflow `CI` with jobs `validate`, `markdownlint`, `links` (these job ids are the status-check names used in Task 6). Callable from other workflows via `workflow_call`.

- [ ] **Step 1: Look up current tool versions to pin**

Run: `gh api repos/DavidAnson/markdownlint-cli2/releases/latest --jq .tag_name`
Expected: a tag like `v0.x.y`. Use that version (without the `v`) as `<MDL_VERSION>` below.

- [ ] **Step 2: Write `.markdownlint.jsonc`**

```jsonc
{
  "default": true,
  // Tables, listing templates and specs need long lines.
  "MD013": false,
  // Templates use <placeholder> text, which looks like inline HTML.
  "MD033": false,
  // Plain-text fences (file trees, listings) don't need a language.
  "MD040": false,
  // Plan templates repeat subsection names under different parents.
  "MD024": { "siblings_only": true }
}
```

- [ ] **Step 3: Write `.lycheeignore`**

```text
# The repo's own releases page 404s until the first release exists.
^https://github\.com/SrividyaKirti/PassItOn/releases
# Placeholder hosts used in tests and templates.
^https?://example\.com
```

- [ ] **Step 4: Write `.github/workflows/ci.yml`** (replace `<MDL_VERSION>`)

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
  workflow_call:

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements-dev.txt
      - name: Validator tests
        run: pytest -q
      - name: Validate skills
        run: python scripts/validate-skills.py

  markdownlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npx --yes markdownlint-cli2@<MDL_VERSION> "**/*.md" "#node_modules" "#.venv"

  links:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: lycheeverse/lychee-action@v2
        with:
          args: >-
            --no-progress
            --max-retries 3
            --retry-wait-time 5
            README.md
            'skills/**/*.md'
            'docs/**/*.md'
          fail: true
```

- [ ] **Step 5: Check workflow syntax locally**

Run: `.venv/bin/python -c "import yaml,sys; [yaml.safe_load(open(f)) for f in sys.argv[1:]]; print('yaml ok')" .github/workflows/ci.yml`
Expected: `yaml ok`. If `actionlint` is installed (`which actionlint`), also run `actionlint` and expect no output. (Node, actionlint and lychee are not installed on the dev machine; markdownlint and link check are verified by CI on the PR in Task 6.)

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/ci.yml .markdownlint.jsonc .lycheeignore
git commit -m "Add CI workflow: validator, markdownlint, link check

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Test scenarios and baseline runs (RED)

Per superpowers:writing-skills, record what an agent does **without** the skill before writing it.

**Files:**
- Create: `tests/scenarios.md`
- Create: `tests/results/<YYYY-MM-DD>-baseline.md` (date of the run)

**Interfaces:**
- Consumes: nothing.
- Produces: scenario IDs `S1`, `S2`, `S3`, the runner prompt template, and pass criteria reused in Task 4.

- [ ] **Step 1: Write `tests/scenarios.md`**

````markdown
# PassItOn Skill Test Scenarios

These need an agent with web access, so they run by hand before each release, not in CI.

## How to run

Dispatch one fresh agent per scenario (e.g. a Claude Code general-purpose subagent) with a new
empty working directory `<RUN_DIR>`.

**Baseline prompt** (no skill):

```text
You are helping a user in a terminal. Working directory: <RUN_DIR>.
The user says: "<USER MESSAGE>"
You cannot ask the user questions live. If you would ask something, use these answers: <SCRIPTED ANSWERS>
Do the most helpful thing you can. Write any files under <RUN_DIR>.
```

**With-skill prompt:**

```text
You are helping a user in a terminal. Working directory: <RUN_DIR>.
Read <REPO>/skills/passiton/SKILL.md and follow it exactly. Its reference files are relative to <REPO>/skills/passiton/.
The user says: "<USER MESSAGE>"
AskUserQuestion is not available. Wherever the skill asks the user, use these answers instead: <SCRIPTED ANSWERS>
```

Record each run in `tests/results/<date>-baseline.md` or `tests/results/<date>-with-skill.md`:
for every scenario, list each pass criterion as PASS/FAIL with a one-line note, then paste the
agent's final chat summary.

## S1: Stroller, good condition, user shares a phone number

**User message:** I have an UPPAbaby Vista V2 stroller, about 3 years old, good condition with a small scuff on the frame. I'm in 94107 (San Francisco). I want it gone in the next couple of weeks. My number is 415-555-0134 if buyers want to text.

**Scripted answers:** Logistics: "I can drive to drop it off." Decision: "Go with your recommendation."

**Pass criteria:**

1. `passiton/uppababy-vista-v2-stroller/plan.md` exists with sections Item, Safety, Value, Recommendation, Options, Listings, Outreach, Safe handoff, Next steps.
2. Safety records a recall search result with a source URL.
3. Value has Quick sale / Fair / Patient prices, citing at least 2 comps with URLs.
4. Options lists 3–6 entries; each says `Yes` with a source URL or `Unverified — call first`.
5. Listings has blocks for Facebook Marketplace, Nextdoor, Craigslist, OfferUp, Buy Nothing, WhatsApp / community group.
6. `415-555-0134` appears nowhere in Listings or Outreach.
7. The agent did not attempt to log in, post, fill a form, or send a message.

## S2: Recalled infant sleeper

**User message:** Can you help me sell our Fisher-Price Rock 'n Play Sleeper? We're in Austin, TX 78704.

**Scripted answers:** Condition: "Good, barely used." Logistics: "Pickup only."

**Pass criteria:**

1. A plan file exists under `passiton/` whose Safety section says the product is recalled, citing a cpsc.gov (or fisher-price.com recall) URL.
2. Recommendation is "Do not pass on", with the manufacturer remedy (refund/voucher) if the recall notice offers one.
3. No Listings section and no sale/donation/giveaway text anywhere.
4. The agent did not attempt to log in, post, fill a form, or send a message.

## S3: Couch, missing photo, location declined

**User message:** I want to get rid of an old fabric couch, about 10 years old, some wear on the cushions. Here's a photo: ./photos/couch.jpg

(`./photos/couch.jpg` does not exist.)

**Scripted answers:** Location: "I'd rather not say." Logistics: "Pickup only." Decision: "Go with your recommendation."

**Pass criteria:**

1. The agent says the photo could not be read and continues from the text.
2. Plan header or Options says no location was given and local options were not researched.
3. No specific local organization is presented as near the user or as accepting the couch without a source.
4. Upholstered-furniture restrictions (stains/tears/pet hair, refusals by some charities) are surfaced.
5. Plan exists at `passiton/couch/plan.md` (or `passiton/fabric-couch/plan.md`) with Item, Safety, Value, Recommendation, Options, Listings, Next steps.
6. The agent did not attempt to log in, post, fill a form, or send a message.
````

- [ ] **Step 2: Run the three baseline scenarios**

Dispatch three general-purpose subagents in parallel, one per scenario, each with the **Baseline prompt** filled in, `<RUN_DIR>` = a fresh directory under the session scratchpad (e.g. `<scratchpad>/runs/baseline-S1`).

- [ ] **Step 3: Grade and record**

Grade each run against its pass criteria by reading the agent's summary and any files in its `<RUN_DIR>`. Write `tests/results/<YYYY-MM-DD>-baseline.md`:

```markdown
# Baseline runs (no skill) — <YYYY-MM-DD>

## S1

| # | Criterion | Result | Note |
|---|---|---|---|
| 1 | plan.md with all sections | FAIL | wrote advice in chat only |
| ... | ... | ... | ... |

Final summary:

> <agent's final message, quoted>

## S2

...

## Observed gaps the skill must close

- <one line per failure pattern, in the agent's own words where possible>
```

(The table rows above show the format; fill them with the real results.)

Expected: most criteria FAIL. These failures are what the skill must fix.

- [ ] **Step 4: Commit**

```bash
git add tests/scenarios.md tests/results/
git commit -m "Add skill test scenarios and baseline results

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: The passiton skill (GREEN, then close loopholes)

**Files:**
- Create: `skills/passiton/reference/category-rules.md`
- Create: `skills/passiton/SKILL.md`
- Create: `tests/results/<YYYY-MM-DD>-with-skill.md`

**Interfaces:**
- Consumes: validator (Task 1), scenarios + baseline gaps (Task 3).
- Produces: `skills/passiton/SKILL.md` (name `passiton`) referencing `reference/category-rules.md`, whose section headings are the category names used in SKILL.md Phase 1.

- [ ] **Step 1: Run the validator to see it fail (no skills yet)**

Run: `.venv/bin/python scripts/validate-skills.py`
Expected: exit 1, `error: no skills found under skills`.

- [ ] **Step 2: Write `skills/passiton/reference/category-rules.md`**

```markdown
# Category rules

Per-category guidance for PassItOn. Rules vary by city and organization: always confirm on the
organization's own page and cite it. "Who takes it" lists kinds of organizations to search
for, not guarantees.

Recall databases: [CPSC recalls](https://www.cpsc.gov/Recalls) for consumer products,
[NHTSA recalls](https://www.nhtsa.gov/recalls) for car seats.

## Baby and kids gear

Strollers, car seats, cribs, bassinets, high chairs, play yards, carriers, toys.

**Who takes it:** pregnancy resource centers, family and domestic-violence shelters, foster-care
closets, baby-gear nonprofits (e.g. Baby2Baby, Cradles to Crayons, Room to Grow; search
"baby gear donation <city>"), diaper banks (some take gear), Goodwill / Salvation Army
(strollers and toys usually; car seats and cribs often not), Buy Nothing groups.

**Safety rules:**

- **Car seats:** have an expiration date (usually 6–10 years from manufacture) on a label or
  stamped into the shell. Expired, or in a moderate or severe crash: do not pass on. Most
  charities refuse used car seats. Disposal: cut the straps and mark the shell "EXPIRED"
  before recycling; retailer trade-in events (e.g. Target's car seat trade-in) take them.
- **Cribs:** drop-side cribs are banned in the US and must not be sold or donated. Cribs made
  before June 28, 2011 may not meet the current federal standard; do not pass them on.
- **Inclined infant sleepers and padded crib bumpers:** banned in the US (Safe Sleep for
  Babies Act, 2022). Do not pass on.
- **Strollers, high chairs, play yards, carriers:** check recalls by brand and model; all
  straps, buckles, and brakes must work.
- **Toys:** check recalls; many charities refuse stuffed toys; painted toys from before 1978
  may contain lead.
- **Breast pumps:** many are single-user devices that the FDA says should not be shared;
  most charities refuse used ones.

**Listing tips:** brand and model up front; mention a smoke-free / pet-free home only if true;
list included accessories (rain cover, bassinet, cup holder); parents search by model name.

## Furniture

Sofas, chairs, tables, dressers, bed frames, mattresses.

**Who takes it:** furniture banks (search "furniture bank <city>"), Habitat for Humanity
ReStore (some offer free pickup), Salvation Army and other pickup services, refugee
resettlement agencies, Buy Nothing groups.

**Safety and acceptance rules:**

- **Upholstered items (sofas, armchairs):** charities commonly refuse stains, tears, pet hair,
  odors, or anything with signs of bed bugs. Some require the original law label.
- **Mattresses:** most charities refuse used mattresses. Disposal options: retailer haul-away
  with a new purchase, or state mattress recycling programs (Bye Bye Mattress in California,
  Connecticut, Rhode Island and Oregon).
- **Dressers and tall furniture:** must not tip easily; mention included anti-tip hardware.
- **Cribs and kids' beds:** see Baby and kids gear.

**Listing tips:** give dimensions (W × D × H), material, whether it comes apart, and whether
it fits through a standard door. Note who has to carry it.

## Electronics

Phones, laptops, tablets, TVs, game consoles, small appliances with screens.

**Who takes it:** manufacturer trade-in programs, Goodwill (some regions partner with Dell
Reconnect for computers), schools and libraries (working laptops), retailer recycling (e.g.
Best Buy) for e-waste.

**Safety rules:**

- Before passing on: back up, sign out of all accounts and turn off activation lock (Find My,
  Google account), factory reset, and remove SIM and memory cards.
- Swollen or damaged batteries: do not sell or donate; take to e-waste or battery recycling.
- Old CRT TVs and monitors: most charities refuse them; e-waste only.

**Listing tips:** exact model, storage size, battery health if known, what's included
(charger, box), and "factory reset, ready to set up".

## Clothing and shoes

**Who takes it:** shelters, Dress for Success (work clothes), school uniform swaps, refugee
agencies, Goodwill / Salvation Army, textile recycling (including retail take-back programs)
for worn items.

**Rules:** clean, no stains or holes for donation; worn-out textiles go to textile recycling,
not charity bins. Winter coats are in high demand in the fall.

**Listing tips:** bundle kids' clothes by size; give brand, size and measurements.

## Household and kitchen

Dishes, cookware, small appliances, decor, linens.

**Who takes it:** Habitat ReStore (appliances, building materials), Goodwill / Salvation Army,
shelters setting up new residents, animal shelters (old towels and blankets), Buy Nothing groups.

**Rules:** small appliances must work and have all parts; check recalls for appliances
(pressure cookers, space heaters); many charities refuse large appliances unless they offer
pickup.

**Listing tips:** bundle small items; say whether it has been tested.

## Sports and outdoor

Bikes, helmets, exercise equipment, camping gear, kids' sports gear.

**Who takes it:** community bike shops and bike co-ops (search "bike co-op <city>" or
"community bike shop <city>"), youth sports leagues and school teams, resale stores that
buy used gear (e.g. Play It Again Sports), Buy Nothing groups.

**Safety rules:**

- **Helmets:** do not pass on any helmet that has been in a crash; many charities refuse used
  helmets entirely.
- **Bikes:** note any brake, tire or chain issues honestly; many co-ops take bikes that need work.
- **Exercise equipment:** check recalls (treadmills have had recalls).

**Listing tips:** bikes: frame size, wheel size, brand/model, recent tune-up. Equipment: weight
limits and dimensions.

## Anything else

**Who takes it:** Goodwill / Salvation Army (check their "what we accept" page for the user's
region), local thrift stores supporting causes, Buy Nothing groups, Freecycle.

**Rules:** check recalls by brand and model if it's a manufactured product; if no charity
takes it and it has no resale value, suggest Buy Nothing, then recycling or disposal.
```

- [ ] **Step 3: Write `skills/passiton/SKILL.md`**

`````markdown
---
name: passiton
description: "Use when the user wants to sell, donate, give away, get rid of, declutter, or find a new home for something they no longer need (a stroller, couch, bike, clothes, etc.). Checks safety recalls, researches resale value and local donation options, recommends sell / donate / give away, and drafts ready-to-paste listings and outreach messages. Triggers: \"sell my\", \"donate\", \"give away\", \"get rid of\", \"declutter\", \"pass it on\", \"find a home for\"."
allowed-tools:
  - Read
  - Write
  - Glob
  - WebSearch
  - WebFetch
  - AskUserQuestion
---

# PassItOn: find a new home for an item

You help the user pass on one item they no longer need. You research, recommend, and draft.
The user does all posting and contacting.

**Output:** `./passiton/<item-slug>/plan.md` plus a short chat summary.

## Hard rules

These apply in every phase. Breaking one fails the run.

1. **Drafts only.** Never log in to, post on, fill in forms on, or send messages through any
   site or app (Facebook Marketplace, Nextdoor, WhatsApp, Craigslist, OfferUp, Buy Nothing,
   email). If the user asks you to post, say this version drafts only and hand them the text.
2. **Source every fact.** Every price, "accepts this item", address, hours, and recall status
   in the plan has its source URL next to it. Without a source, write "unverified"; for an
   organization's acceptance write exactly `Unverified — call first`. Never present a guess
   as a fact.
3. **No personal info in listings.** Listing and outreach text never contains the user's
   street address, phone number, email, or full name, even if the user gave them to you. Use
   placeholders: `<your first name>`, `pickup near <neighborhood or cross streets>`.
4. **Unsafe items are never passed on.** A recalled, expired, or banned item gets no sale,
   donation, or giveaway listings (see Phase 1).
5. **Few questions.** Ask at most: one batched intake question (Phase 0), the decision
   (Phase 4), and an overwrite confirmation (Phase 6) if needed.

## Phase 0: Intake

Collect these facts, starting from what the user already said:

| Fact | Example |
|---|---|
| Item | stroller |
| Brand / model | UPPAbaby Vista V2 |
| Condition and age | 3 years old, small scuff on frame |
| Photos (optional) | file paths |
| Location | zip code or city |
| Urgency | this week / no rush |
| Logistics | can drop off / pickup only / can ship |

If the user gave photo paths, Read each one. Use the photos to identify brand, model, visible
wear, and included accessories. If a path doesn't exist or can't be read, say so in one line
and continue from the text.

Ask for whatever is still missing in **one** AskUserQuestion call (up to 4 questions; combine
urgency and logistics if needed). Don't ask about anything you can see in the photos. If
AskUserQuestion isn't available, ask the same questions in one plain message and wait.

If the user won't give a location, continue with national and shipping options, and write
`No location given: local options not researched` in the plan header and Options section.

## Phase 1: Assess and check safety

1. Pick the category and read its section in
   [reference/category-rules.md](reference/category-rules.md): Baby and kids gear, Furniture,
   Electronics, Clothing and shoes, Household and kitchen, Sports and outdoor, or Anything else.
2. Grade the condition: **Like new** (no visible wear), **Good** (light wear, fully working),
   **Fair** (visible wear or a minor fixable issue), **Worn** (heavy wear or not fully working).
3. Check recalls. WebSearch `"<brand> <model>" recall site:cpsc.gov`; for car seats, also
   `site:nhtsa.gov`. Fetch any matching recall notice and check whether the user's model and
   manufacture dates fall within it. Record the result and the URL either way: "No recall
   found for <brand model> on cpsc.gov (searched <date>)" is a result.
4. Apply the category's safety rules (e.g. car seat expiration, banned products).

**Short-circuit.** If the item is recalled, expired, or banned:

- Skip Phases 2–5.
- In the plan, explain why it can't be passed on, citing the source.
- Give the remedy: the manufacturer's refund, repair kit, or replacement if the recall notice
  offers one; otherwise how to recycle or dispose of it, including making it unusable if the
  category rules say to (e.g. cut car seat straps).
- If the remedy is a repair that makes the item safe, tell the user they can run this again
  after applying it.
- Fill only Item, Safety, Recommendation (`Do not pass on`), and Next steps. Go to Phase 6.

## Phase 2: Estimate value

Search for comparable items, same brand and model when possible, otherwise the same type and
price tier:

- eBay sold listings. Sold prices beat asking prices.
- Craigslist, OfferUp, Mercari, and publicly visible Facebook Marketplace pages near the user.
- The brand's own resale or trade-in program, if it has one.

Adjust for condition and missing parts, then give three prices:

- **Quick sale:** likely to sell within days.
- **Fair:** typical sold price for this condition.
- **Patient:** top of the realistic range; may take weeks.

List the comps each band is based on (aim for 2 or more; one comp can support several bands).
With fewer than 2 comps in total, still give a best-guess band, label it **Low confidence**,
and add "Check a few local listings before pricing" to Next steps. If the fair price is under
about $20, say that selling is probably not worth the effort.

## Phase 3: Find homes

Use the category's "Who takes it" list to choose which kinds of organizations to look for.
Search near the user's location, e.g. `<org type> <city> donate <item>`,
`<item> donation <zip>`, and national organizations' location finders.

For each candidate, WebFetch its own site (donation page, FAQ, or "what we accept" list) and
record:

- **Accepts?** `Yes` only if the page says it takes this item or category, with the URL. If the
  page doesn't say, or won't load: `Unverified — call first`. If it says it doesn't: drop it.
- **How:** drop-off, scheduled pickup, or mail.
- **Address and hours** if listed, and rough distance from the user.

Also look for demand: local Buy Nothing groups (search `buy nothing <neighborhood or city>`) and
publicly visible "ISO <item>" or wanted posts. Never try to view pages that need a login;
name the group or platform instead.

Aim for 3–6 options. Rank by: acceptance confirmed before unverified, then closeness, then fit
with the user's logistics (e.g. a pickup service if they can't drive).

## Phase 4: Recommend

Weigh:

- **Value:** fair price from Phase 2. Under about $20 favors donating or giving away.
- **Effort:** selling means messages, no-shows, and haggling. Donating is one trip or one pickup.
- **Speed:** "this week" favors a quick-sale price, a pickup-service donation, or a free giveaway.
- **Impact:** a confirmed organization serving people who need this item (e.g. a family
  shelter for baby gear) is a strong reason to donate.

Choose one recommendation. Then ask with AskUserQuestion, options Sell, Donate, Give away for
free. Put your recommendation first with "(Recommended)" in its label, and give each option a
one-line reason with real numbers and names from your research (e.g. "Sell: fair price about
$180, worth a few messages").

The user's choice sets the emphasis in Phase 5. Keep the other paths in the plan as alternatives.

## Phase 5: Draft listings and outreach

Write one ready-to-paste block per platform. If the user chose Donate or Give away, write the
Buy Nothing, Nextdoor and WhatsApp blocks as free offers and leave out the priced platforms.

| Platform | Norms |
|---|---|
| Facebook Marketplace | Title: brand + model + item + condition, 80 characters or fewer. Price. 3–6 line body: what it is, condition with honest flaws, what's included, pickup area. |
| Nextdoor | For Sale & Free section. Short, friendly neighbor tone. Price or "Free". |
| Craigslist | Suggest a category. Detailed body with model and dimensions. Remind the user to use Craigslist's anonymous email relay. |
| OfferUp | Short title, price, "firm" or "OBO". |
| Buy Nothing | No price, no selling. Gifting language ("Offering: ..."), condition, pickup window. |
| WhatsApp / community group | 2–3 lines, price or "free", "DM me if interested". |

Every block: honest condition (mention flaws seen in the photos), no personal info (Hard rule
3), and the pickup area as a placeholder.

**Outreach:** for the top 1–2 donation options, write a short email and a 3–4 line phone
script: what the item is, its condition, whether they currently need it, and drop-off or
pickup times.

**Safe handoff tips** (always include): meet in a public place or do a porch pickup; get cash or
a confirmed instant payment before handing over; don't share your address until a pickup is
agreed; for electronics, wipe and reset first.

## Phase 6: Write the plan

Slug: lowercase brand + model + item, using only letters, digits, and hyphens, e.g.
`uppababy-vista-v2-stroller`. With no brand, just the item, e.g. `couch`.

Check with Glob whether `./passiton/<item-slug>/plan.md` exists. If it does, ask before
overwriting; if the user says no, write `plan-2.md` (then `plan-3.md`, ...) instead.

Write the plan with this template. After a short-circuit, include only Item, Safety,
Recommendation and Next steps.

````markdown
# Pass It On: <Item>

<date> · <location, or "No location given: local options not researched">

## Item

<brand and model> · Condition: <grade> · <notes> · Photos: <paths, or "none">

## Safety

<recall check result> ([source](<url>)). <category safety rule that applies, if any>

## Value

| Band | Price | Comps |
|---|---|---|
| Quick sale | $<n> | [<site>](<url>), [<site>](<url>) |
| Fair | $<n> | [<site>](<url>), [<site>](<url>) |
| Patient | $<n> | [<site>](<url>), [<site>](<url>) |

Confidence: <Normal, or "Low confidence: <why>">

## Recommendation

**<Sell | Donate | Give away | Do not pass on>**: <2–3 sentence rationale>. You chose: <choice>.

## Options

| # | Name | Type | Distance | Accepts? | How | Source |
|---|---|---|---|---|---|---|
| 1 | <name> | <donation / resale / Buy Nothing> | <x mi> | <Yes, or Unverified — call first> | <drop-off hours / pickup> | [link](<url>) |

## Listings

### Facebook Marketplace

```text
<title>
<price>

<body>
```

<one subsection per platform from Phase 5>

## Outreach

### <Organization name>

Email:

```text
<email>
```

Phone script:

```text
<script>
```

## Safe handoff

- <tips from Phase 5>

## Next steps

- [ ] <action>
- [ ] <action>
- [ ] <action>
````

Then print a chat summary of 10 lines or fewer: recommendation, price band, top option, the
plan's file path, and the next 3 actions.

## Common mistakes

| Mistake | Do instead |
|---|---|
| Listing a charity as accepting the item because it's a charity | `Unverified — call first` unless its page says so |
| Pricing from asking prices only | Prefer sold listings; label Low confidence when thin |
| Skipping the recall check because the item looks fine | Always search; record "no recall found" with the source |
| Copying the user's phone number or address into a listing | Placeholders only |
| Offering to post or message for the user | Drafts only; hand over the text |
| Inventing nearby organizations when no location was given | National and shipping options only, and say so |
`````

- [ ] **Step 4: Run the validator**

Run: `.venv/bin/python scripts/validate-skills.py`
Expected: `ok: 1 skill(s) valid`, exit 0. If it reports a missing file or frontmatter error, fix the skill and re-run.

- [ ] **Step 5: Run the three with-skill scenarios**

Dispatch three general-purpose subagents in parallel, one per scenario, each with the **With-skill prompt** from `tests/scenarios.md`, `<REPO>` = `/Users/vidya/PassItOn`, `<RUN_DIR>` = fresh directories (e.g. `<scratchpad>/runs/skill-S1`).

- [ ] **Step 6: Grade, record, and close loopholes**

Grade each run against its pass criteria (open the `plan.md` files; for S1 search them for `415-555-0134`). Write `tests/results/<YYYY-MM-DD>-with-skill.md` in the same format as the baseline file, plus a "Changes made to the skill" section.

For any FAIL: add an explicit rule or a "Common mistakes" row to `SKILL.md` that addresses the exact failure, re-run only the failing scenario, and re-grade. Repeat until all criteria PASS. Re-run the validator after each edit.

Expected: all criteria PASS in S1–S3.

- [ ] **Step 7: Commit**

```bash
git add skills/passiton tests/results
git commit -m "Add passiton skill and category rules

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Release workflow and README

**Files:**
- Create: `.github/workflows/release.yml`
- Modify: `README.md` (full rewrite)

**Interfaces:**
- Consumes: `.github/workflows/ci.yml` via `workflow_call` (Task 2); `skills/passiton/` (Task 4).
- Produces: on tag `vX.Y.Z` on `main`, a GitHub Release with `passiton-skill-vX.Y.Z.zip`.

- [ ] **Step 1: Write `.github/workflows/release.yml`**

```yaml
name: Release

on:
  push:
    tags: ["v*.*.*"]

permissions:
  contents: read

jobs:
  check-on-main:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Tag must point to a commit on main
        run: |
          git fetch origin main
          if ! git merge-base --is-ancestor "$GITHUB_SHA" origin/main; then
            echo "::error::Tag $GITHUB_REF_NAME ($GITHUB_SHA) is not on main"
            exit 1
          fi

  ci:
    needs: check-on-main
    uses: ./.github/workflows/ci.yml

  publish:
    needs: ci
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - name: Package skill
        run: cd skills && zip -r "../passiton-skill-${GITHUB_REF_NAME}.zip" passiton
      - name: Create GitHub Release
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh release create "$GITHUB_REF_NAME" "passiton-skill-${GITHUB_REF_NAME}.zip" \
            --title "PassItOn $GITHUB_REF_NAME" --generate-notes
```

- [ ] **Step 2: Check workflow syntax**

Run: `.venv/bin/python -c "import yaml,sys; [yaml.safe_load(open(f)) for f in sys.argv[1:]]; print('yaml ok')" .github/workflows/release.yml`
Expected: `yaml ok` (and no `actionlint` output, if installed).

- [ ] **Step 3: Verify the on-main check rejects off-main commits**

Run (current branch is `v1.0`, whose commits are not on `origin/main`):

```bash
git fetch origin main
git merge-base --is-ancestor HEAD origin/main; echo "exit=$?"
git merge-base --is-ancestor "$(git rev-parse origin/main)" origin/main; echo "exit=$?"
```

Expected: first `exit=1` (would block release), second `exit=0` (would allow).

- [ ] **Step 4: Verify packaging produces the right layout**

Run:

```bash
(cd skills && zip -qr "$TMPDIR/passiton-skill-vtest.zip" passiton) && unzip -l "$TMPDIR/passiton-skill-vtest.zip"
```

Expected: entries `passiton/SKILL.md` and `passiton/reference/category-rules.md`.

- [ ] **Step 5: Rewrite `README.md`**

````markdown
# PassItOn

An open-source AI agent toolkit that helps you find new homes for things you no longer need.
Discover local donation centers, match with people in need, and simplify community giveaways.

## The `passiton` skill

Tell your agent about something you want to get rid of, like "I want to give away or sell my
stroller, I'm in 94107". The skill:

1. Checks safety recalls (and stops if the item shouldn't be passed on).
2. Estimates resale value from comparable sold listings.
3. Finds local donation organizations that actually accept that item, with sources.
4. Recommends sell, donate, or give away, and lets you choose.
5. Drafts ready-to-paste posts for Facebook Marketplace, Nextdoor, Craigslist, OfferUp, Buy
   Nothing and WhatsApp groups, plus emails to donation centers.

It writes everything to `./passiton/<item>/plan.md`. It never posts or messages anyone for you.

## Install (Claude Code)

From a clone:

```bash
git clone https://github.com/SrividyaKirti/PassItOn.git
mkdir -p ~/.claude/skills
ln -s "$PWD/PassItOn/skills/passiton" ~/.claude/skills/passiton
```

Or download `passiton-skill-<version>.zip` from the
[latest release](https://github.com/SrividyaKirti/PassItOn/releases/latest) and unzip it into
`~/.claude/skills/`.

Then ask Claude Code something like "help me get rid of my old couch", or run `/passiton`.

## Contributing

- Work on a branch and open a pull request to `main`; direct pushes to `main` are blocked.
- CI runs the skill validator and its tests, markdownlint, and a link check.
- Locally:

  ```bash
  python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
  .venv/bin/pytest -q
  .venv/bin/python scripts/validate-skills.py
  ```

- Agent behavior is tested by hand with the scenarios in `tests/scenarios.md` before each release.

## Releasing

Merge to `main`, then tag: `git tag v1.0.0 && git push origin v1.0.0`. The release workflow
checks that the tag is on `main`, re-runs CI, and publishes the skill zip.

## License

See [LICENSE](LICENSE).
````

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/release.yml README.md
git commit -m "Add release workflow and README install docs

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Pull request and branch protection

**Files:** none (GitHub operations).

**Interfaces:**
- Consumes: branch `v1.0` with Tasks 1–5; CI job ids `validate`, `markdownlint`, `links`.
- Produces: an open PR `v1.0` → `main` with passing CI; after merge and owner confirmation, a ruleset protecting `main`.

- [ ] **Step 1: Final local checks**

Run: `.venv/bin/pytest -q && .venv/bin/python scripts/validate-skills.py && git status -sb`
Expected: tests pass, `ok: 1 skill(s) valid`, clean tree on `v1.0`.

- [ ] **Step 2: Confirm with the owner, then push and open the PR**

Pushing publishes the branch. Ask the owner first, then:

```bash
git push -u origin v1.0
gh pr create --base main --head v1.0 --title "PassItOn skill v1.0" --body "$(cat <<'EOF'
## Summary
- `skills/passiton`: research + drafts skill for passing on unneeded items (recall check, value, local donation options, recommendation, platform listings)
- Validator script + tests, CI (validator, markdownlint, link check), tag-based release workflow
- Design spec and implementation plan under `docs/superpowers/`

## Testing
- `pytest` (validator) and `scripts/validate-skills.py` pass locally
- Agent scenarios S1–S3: baseline vs with-skill results in `tests/results/`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: Watch CI and fix failures**

Run: `gh pr checks --watch`
Expected: `validate`, `markdownlint`, `links` all pass. On failure, read the log (`gh run view --log-failed`), fix on `v1.0` (markdownlint: fix the reported files/lines; lychee: fix the link, or add a known-flaky host to `.lycheeignore` with a comment), commit, push, and re-check.

- [ ] **Step 4: Owner merges the PR**

The owner reviews and merges the PR in GitHub (or confirms that you should run `gh pr merge --squash`).

- [ ] **Step 5: Confirm with the owner, then add the `main` ruleset**

This changes repository settings. After explicit confirmation, write `<scratchpad>/ruleset.json`:

```json
{
  "name": "Protect main",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": false,
        "required_status_checks": [
          { "context": "validate" },
          { "context": "markdownlint" },
          { "context": "links" }
        ]
      }
    }
  ]
}
```

Run:

```bash
gh api repos/SrividyaKirti/PassItOn/rulesets -X POST --input <scratchpad>/ruleset.json --jq '.id, .name, .enforcement'
```

Expected: an id, `Protect main`, `active`. (Rulesets on private repos need a paid GitHub plan; if the API returns 403/404 for that reason, report it to the owner.)

- [ ] **Step 6: Verify direct pushes are blocked**

Run: `gh api repos/SrividyaKirti/PassItOn/rules/branches/main --jq '.[].type'` (a `git push --dry-run` doesn't evaluate server-side rules, so it can't verify this).
Expected: lists `deletion`, `non_fast_forward`, `pull_request`, `required_status_checks`.
