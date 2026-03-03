#!/usr/bin/env python3
"""Validate all vllm-omni skills for structural correctness, reference integrity, and content quality."""

import os
import re
import sys
import py_compile
import subprocess
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"
MAX_NAME_LEN = 64
MAX_DESC_LEN = 1024
MAX_BODY_LINES = 500
NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


class ValidationError:
    def __init__(self, skill: str, check: str, message: str):
        self.skill = skill
        self.check = check
        self.message = message

    def __str__(self):
        return f"[{self.skill}] {self.check}: {self.message}"


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Split SKILL.md into frontmatter dict and body string."""
    if not content.startswith("---"):
        return {}, content
    end = content.find("---", 3)
    if end == -1:
        return {}, content
    fm_text = content[3:end].strip()
    body = content[end + 3:].strip()
    fm = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm, body


def validate_structure(skill_dir: Path) -> list[ValidationError]:
    errors = []
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        errors.append(ValidationError(skill_name, "structure", "SKILL.md not found"))
        return errors

    content = skill_md.read_text()
    fm, body = parse_frontmatter(content)

    if not fm:
        errors.append(ValidationError(skill_name, "structure", "No YAML frontmatter found"))
        return errors

    name = fm.get("name", "")
    if not name:
        errors.append(ValidationError(skill_name, "structure", "Missing 'name' field"))
    elif len(name) > MAX_NAME_LEN:
        errors.append(ValidationError(skill_name, "structure", f"Name exceeds {MAX_NAME_LEN} chars"))
    elif not NAME_PATTERN.match(name):
        errors.append(ValidationError(skill_name, "structure", "Name must be lowercase letters/digits/hyphens"))

    desc = fm.get("description", "")
    if not desc:
        errors.append(ValidationError(skill_name, "structure", "Missing 'description' field"))
    elif len(desc) > MAX_DESC_LEN:
        errors.append(ValidationError(skill_name, "structure", f"Description exceeds {MAX_DESC_LEN} chars"))

    body_lines = body.splitlines()
    if len(body_lines) > MAX_BODY_LINES:
        errors.append(ValidationError(
            skill_name, "structure",
            f"Body has {len(body_lines)} lines (max {MAX_BODY_LINES})"
        ))

    allowed_keys = {"name", "description"}
    extra = set(fm.keys()) - allowed_keys
    if extra:
        errors.append(ValidationError(skill_name, "structure", f"Extra frontmatter fields: {extra}"))

    if name and name != skill_name:
        errors.append(ValidationError(
            skill_name, "consistency",
            f"Directory name '{skill_name}' != frontmatter name '{name}'"
        ))

    return errors


def validate_references(skill_dir: Path) -> list[ValidationError]:
    errors = []
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return errors

    content = skill_md.read_text()
    _, body = parse_frontmatter(content)

    linked_files = set()
    for _text, href in LINK_PATTERN.findall(body):
        if href.startswith("http") or href.startswith("#"):
            continue
        target = skill_dir / href
        if not target.exists():
            errors.append(ValidationError(skill_name, "reference", f"Broken link: {href}"))
        linked_files.add(href)

    refs_dir = skill_dir / "references"
    if refs_dir.is_dir():
        for ref_file in refs_dir.iterdir():
            if ref_file.is_file():
                rel = f"references/{ref_file.name}"
                if rel not in linked_files:
                    errors.append(ValidationError(
                        skill_name, "reference",
                        f"Orphaned file not linked from SKILL.md: {rel}"
                    ))

    return errors


def validate_content(skill_dir: Path) -> list[ValidationError]:
    errors = []
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return errors

    content = skill_md.read_text()
    fm, _ = parse_frontmatter(content)
    desc = fm.get("description", "")

    if desc and "use when" not in desc.lower() and "when " not in desc.lower():
        errors.append(ValidationError(skill_name, "content", "Description missing WHEN context (trigger scenarios)"))

    if desc and (desc.startswith("I ") or desc.startswith("You ")):
        errors.append(ValidationError(skill_name, "content", "Description should be in third person"))

    return errors


def validate_scripts(skill_dir: Path) -> list[ValidationError]:
    errors = []
    skill_name = skill_dir.name
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.is_dir():
        return errors

    for script in scripts_dir.iterdir():
        if not script.is_file():
            continue
        if script.suffix == ".py":
            try:
                py_compile.compile(str(script), doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(ValidationError(skill_name, "script", f"Python syntax error in {script.name}: {e}"))
        elif script.suffix == ".sh":
            result = subprocess.run(
                ["bash", "-n", str(script)],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                errors.append(ValidationError(
                    skill_name, "script",
                    f"Shell syntax error in {script.name}: {result.stderr.strip()}"
                ))

    return errors


def validate_skill(skill_dir: Path) -> list[ValidationError]:
    errors = []
    errors.extend(validate_structure(skill_dir))
    errors.extend(validate_references(skill_dir))
    errors.extend(validate_content(skill_dir))
    errors.extend(validate_scripts(skill_dir))
    return errors


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None

    if target:
        target_path = Path(target)
        if not target_path.is_dir():
            print(f"Error: {target} is not a directory", file=sys.stderr)
            sys.exit(1)
        skill_dirs = [target_path]
    else:
        if not SKILLS_DIR.is_dir():
            print(f"Error: skills directory not found at {SKILLS_DIR}", file=sys.stderr)
            sys.exit(1)
        skill_dirs = sorted(
            d for d in SKILLS_DIR.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

    all_errors = []
    for skill_dir in skill_dirs:
        errors = validate_skill(skill_dir)
        all_errors.extend(errors)

    if all_errors:
        print(f"\nValidation failed with {len(all_errors)} error(s):\n", file=sys.stderr)
        for err in all_errors:
            print(f"  FAIL  {err}", file=sys.stderr)
        print(file=sys.stderr)
        sys.exit(1)
    else:
        print(f"All {len(skill_dirs)} skill(s) passed validation.")
        sys.exit(0)


if __name__ == "__main__":
    main()
