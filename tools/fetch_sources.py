#!/usr/bin/env python3
"""Download optional third-party prompt sources without executing their code."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ADAPTERS_FILE = ROOT / "data" / "adapters.json"
DEFAULT_IDS = ("blader_humanizer", "stephenturner_skill_deslop")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def load_adapters() -> list[dict[str, Any]]:
    with ADAPTERS_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def safe_destination(relative_path: str) -> Path:
    candidate = (ROOT / relative_path).resolve()
    source_root = (ROOT / "repos" / "english-humanizers").resolve()
    if candidate.parent != source_root:
        raise ValueError(f"Adapter path is outside the source cache: {relative_path}")
    return candidate


def clone(adapter: dict[str, Any], update: bool) -> bool:
    repo = str(adapter["repo"])
    if not REPO_RE.fullmatch(repo):
        raise ValueError(f"Invalid GitHub repository name: {repo}")

    destination = safe_destination(str(adapter["path"]))
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        if update and (destination / ".git").is_dir():
            print(f"UPDATE {adapter['id']} <- {repo}")
            subprocess.run(
                ["git", "-C", str(destination), "pull", "--ff-only"],
                check=True,
            )
        else:
            print(f"SKIP   {adapter['id']} (already cached)")
        return False

    print(f"FETCH  {adapter['id']} <- https://github.com/{repo}")
    subprocess.run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            f"https://github.com/{repo}.git",
            str(destination),
        ],
        check=True,
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Shallow-clone optional GitHub source repositories used as prompt references. "
            "Downloaded code is not installed or executed."
        )
    )
    parser.add_argument("--id", action="append", dest="ids", help="Adapter ID to fetch; may be repeated")
    parser.add_argument("--all", action="store_true", help="Fetch every configured source repository")
    parser.add_argument("--list", action="store_true", help="List adapter IDs and repositories without downloading")
    parser.add_argument("--update", action="store_true", help="Fast-forward existing shallow clones")
    args = parser.parse_args()

    adapters = load_adapters()
    by_id = {adapter["id"]: adapter for adapter in adapters}

    if args.list:
        for adapter in adapters:
            print(f"{adapter['id']:<52} {adapter['repo']}")
        return 0

    requested = list(by_id) if args.all else (args.ids or list(DEFAULT_IDS))
    unknown = [adapter_id for adapter_id in requested if adapter_id not in by_id]
    if unknown:
        parser.error("unknown adapter ID(s): " + ", ".join(unknown))

    print("Third-party repositories keep their own licenses and are stored in an ignored local cache.")
    print("Review each source before use. This script never installs dependencies or executes repository code.\n")

    fetched = 0
    failures = 0
    for adapter_id in requested:
        try:
            fetched += int(clone(by_id[adapter_id], update=args.update))
        except (OSError, subprocess.CalledProcessError, ValueError) as exc:
            failures += 1
            print(f"ERROR  {adapter_id}: {exc}")

    print(f"\nFinished: {fetched} fetched, {len(requested) - fetched - failures} already cached, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
