#!/usr/bin/env python3
"""Validate every skill in skills/ and regenerate the index in README.md and skills.json.

Usage:
    python scripts/build_index.py          # validate + rebuild
    python scripts/build_index.py --check  # validate; exit 1 if generated files are out of date

Requires: PyYAML
"""
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
README = ROOT / "README.md"
JSON_OUT = ROOT / "skills.json"
START, END = "<!-- SKILLS:START -->", "<!-- SKILLS:END -->"

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
STATUSES = ["stable", "draft", "deprecated"]


def parse(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise ValueError("SKILL.md must start with a YAML frontmatter block (--- ... ---)")
    fm = yaml.safe_load(m.group(1)) or {}
    if not isinstance(fm, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return fm


def load():
    skills, errors = [], []
    for d in sorted(p for p in SKILLS.iterdir() if p.is_dir() and not p.name.startswith("_")):
        f = d / "SKILL.md"
        if not f.exists():
            errors.append(f"{d.name}: missing SKILL.md")
            continue
        try:
            fm = parse(f)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{d.name}: {e}")
            continue
        name, desc = fm.get("name"), fm.get("description")
        meta = fm.get("metadata") or {}
        if name != d.name:
            errors.append(f"{d.name}: 'name' must equal the folder name (got {name!r})")
        if not name or not NAME_RE.match(str(name)) or len(str(name)) > 64:
            errors.append(f"{d.name}: name must be lowercase letters/digits/hyphens, max 64 chars")
        if not desc or len(str(desc)) > 1024:
            errors.append(f"{d.name}: 'description' is required (max 1024 chars)")
        if not meta.get("owner"):
            errors.append(f"{d.name}: metadata.owner (full name) is required")
        status = meta.get("status", "draft")
        if status not in STATUSES:
            errors.append(f"{d.name}: metadata.status must be one of {STATUSES}")
        tags = meta.get("tags") or []
        skills.append({
            "name": d.name,
            "description": " ".join(str(desc or "").split()),
            "owner": meta.get("owner", ""),
            "status": status,
            "tags": [str(t) for t in tags],
            "path": f"skills/{d.name}",
        })
    return skills, errors


def esc(s):
    return str(s).replace("|", "\\|")


def render(skills):
    if not skills:
        return "No skills yet. Be the first: see [CONTRIBUTING.md](CONTRIBUTING.md)."
    order = {s: i for i, s in enumerate(STATUSES)}
    skills = sorted(skills, key=lambda s: (order[s["status"]], s["name"]))
    out = [f"**{len(skills)} skill{'s' if len(skills) != 1 else ''}**", "",
           "| Skill | What it does | Owner | Status | Tags |", "|---|---|---|---|---|"]
    for s in skills:
        out.append(f"| [{s['name']}]({s['path']}) | {esc(s['description'])} | {esc(s['owner'])} | "
                   f"{s['status']} | {esc(', '.join(s['tags']))} |")
    return "\n".join(out)


def main():
    check = "--check" in sys.argv
    skills, errors = load()
    if errors:
        print("ERRORS:\n  " + "\n  ".join(errors))
        sys.exit(1)
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print(f"README.md must contain {START} and {END}")
        sys.exit(1)
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    new_readme = f"{head}{START}\n{render(skills)}\n{END}{tail}"
    new_json = json.dumps(skills, indent=2, ensure_ascii=False) + "\n"
    if check:
        if new_readme != text or not JSON_OUT.exists() or new_json != JSON_OUT.read_text(encoding="utf-8"):
            print("Generated files are out of date. Run: python scripts/build_index.py")
            sys.exit(1)
        print("Up to date.")
        return
    README.write_text(new_readme, encoding="utf-8")
    JSON_OUT.write_text(new_json, encoding="utf-8")
    print(f"Validated {len(skills)} skills; wrote README.md and skills.json.")


if __name__ == "__main__":
    main()
