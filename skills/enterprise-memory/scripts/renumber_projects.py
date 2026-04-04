#!/usr/bin/env python3
"""
renumber_projects.py — Renumber all EAM projects from 3-digit daily to 4-digit continuous.

Usage: python3 renumber_projects.py
"""
import json
import os
import re
from pathlib import Path

PROJECTS_DIR = Path.home() / ".openclaw" / "EAM-projects"

# Known renumbering map (old exact name -> new 4-digit sequence)
RENUMBER = {
    "SOP-20260402-001-EAM-SOP-Merge": "0001",
    "SOP-20260403-001-Claude-Code-源码泄露事件分析": "0002",
    "SOP-20260403-002-claude-code-leak": "0003",
    "SOP-20260403-003-agent-tool-system": "0004",
    "SOP-20260403-010-memory-system": "0005",
    "SOP-20260403-011-hook-system": "0006",
    "SOP-20260403-012-compaction-system": "0007",
    "SOP-20260403-013-permission-system": "0008",
    "SOP-20260403-014-subagent-system": "0009",
    "SOP-20260403-015-task-system": "0010",
    "SOP-20260403-016-skills-system": "0011",
    "SOP-20260403-017-team-system": "0012",
    "SOP-20260403-018-kairos-system": "0013",
    "SOP-20260403-019-file-state-system": "0014",
    "SOP-20260403-000-agent-architecture": "0015",
}

def build_new_name(old_path, new_seq):
    """Build new directory name with 4-digit sequence."""
    old_name = old_path.name
    parts = old_name.split("-")
    date_part = parts[1]
    name_part = "-".join(parts[3:]) if len(parts) > 3 else parts[-1]
    return old_path.parent / f"SOP-{date_part}-{new_seq}-{name_part}"

def renumber():
    renamed = []
    missing = []
    already_correct = []

    for old_name, new_seq in sorted(RENUMBER.items(), key=lambda x: x[1]):
        old_path = PROJECTS_DIR / old_name
        if not old_path.exists():
            # Try partial match
            found = False
            for existing in PROJECTS_DIR.iterdir():
                if old_name.split("-")[-1] in existing.name and existing.is_dir():
                    new_path = build_new_name(existing, new_seq)
                    if existing != new_path:
                        os.rename(existing, new_path)
                        renamed.append((existing.name, new_path.name))
                    else:
                        already_correct.append(existing.name)
                    found = True
                    break
            if not found:
                missing.append(old_name)
            continue

        new_path = build_new_name(old_path, new_seq)
        if old_path != new_path:
            os.rename(old_path, new_path)
            renamed.append((old_path.name, new_path.name))
        else:
            already_correct.append(old_path.name)

    print(f"\n=== Renumber Results ===")
    print(f"Renamed:   {len(renamed)}")
    for old, new in renamed:
        print(f"  {old[:50]} -> {new[:50]}")
    print(f"Already correct: {len(already_correct)}")
    for name in already_correct:
        print(f"  {name}")
    print(f"Missing (not found): {len(missing)}")
    for name in missing:
        print(f"  {name}")

    # Update GLOBAL-INDEX.md if it exists
    idx_file = PROJECTS_DIR / "GLOBAL-INDEX.md"
    if idx_file.exists():
        content = idx_file.read_text()
        # The new GLOBAL-INDEX.md has been pulled from git, just report
        print(f"\nGLOBAL-INDEX.md is up to date in the repo.")

    print(f"\nNext sequence: 0016")

if __name__ == "__main__":
    print("EAM Project Renumbering Tool")
    print(f"Projects dir: {PROJECTS_DIR}")
    print(f"Found {len(RENUMBER)} projects to renumber")
    renumber()
