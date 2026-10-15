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
