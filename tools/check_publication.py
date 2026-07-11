#!/usr/bin/env python3
"""Fail when tracked files contain obvious secrets or local-only artifacts."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 20 * 1024 * 1024
BLOCKED_FILES = {"config.local.json"}
BLOCKED_PREFIXES = ("repos/english-humanizers/", "tmp_qa_")
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"),
    "GitHub fine-grained token": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    "OpenAI-style token": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "NVIDIA token": re.compile(r"\bnvapi-[A-Za-z0-9_-]{20,}\b"),
    "Google API key": re.compile(r"\bAIza[A-Za-z0-9_-]{30,}\b"),
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def main() -> int:
    failures: list[str] = []
    files = tracked_files()

    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if relative in BLOCKED_FILES or relative.startswith(BLOCKED_PREFIXES):
            failures.append(f"blocked local artifact is tracked: {relative}")
            continue
        if not path.is_file():
            continue
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            failures.append(f"tracked file exceeds 20 MiB: {relative}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                failures.append(f"possible {label} found in: {relative}")

    if failures:
        print("Publication check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Publication check passed: {len(files)} tracked files, no blocked artifacts or known token patterns found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
