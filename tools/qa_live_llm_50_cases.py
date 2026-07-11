#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_server():
    spec = importlib.util.spec_from_file_location("humanizer_server_live", ROOT / "server.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load server.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


server = load_server()


LIVE_CASES = [
    {
        "name": "generic AI business prose",
        "text": (
            "In today's rapidly evolving digital landscape, organizations are increasingly leveraging AI to streamline workflows "
            "and unlock unprecedented value across departments. This paper aims to explore the significant impact of AI adoption "
            "on operational efficiency, knowledge management, and long-term business transformation.\n\n"
            "Furthermore, it is important to note that successful implementation requires a holistic approach that combines "
            "technical infrastructure, employee training, ethical governance, and continuous improvement. In conclusion, AI has "
            "the potential to revolutionize modern organizations and drive sustainable competitive advantage."
        ),
        "anchors": ["AI"],
    },
    {
        "name": "technical release note",
        "text": (
            "During the v2.3.1 canary rollout, the platform team first ran `bin/migrate --tenant=prod --dry-run` and then verified "
            "that `DB_SCHEMA_VERSION=20260412` matched production. This process significantly improved system stability and created "
            "a strong foundation for future iterations.\n\n"
            "If the logs show `schema mismatch on orders_v2`, do not broaden the remediation plan immediately. Check the config, "
            "migration script, and rollback window first, then decide whether the release should continue."
        ),
        "anchors": ["v2.3.1", "DB_SCHEMA_VERSION=20260412", "schema mismatch on orders_v2"],
    },
    {
        "name": "academic abstract",
        "text": (
            "This study examines the efficiency of community-based eldercare service provision using panel data from 2018 to 2023. "
            "It constructs a multi-indicator evaluation framework to analyze resource allocation, service accessibility, and resident "
            "satisfaction. The results indicate that digital platforms improve information matching but remain limited in their coverage "
            "of younger seniors, offline coordination, and privacy protection.\n\n"
            "Further analysis shows that adding platform features alone does not automatically improve service experience. Response time "
            "from community workers, participation from family caregivers, and stable grassroots funding all affect the final outcome."
        ),
        "anchors": ["2018", "2023"],
    },
]


META_MARKERS = (
    "Detection result",
    "AI detection",
    "AI score",
    "Human score",
    "Rewrite notes",
    "Revision notes",
    "Analysis report",
    "Quality check",
    "Changes made",
    "Here is",
    "Below is",
)


def wordish_chars(text: str) -> int:
    return len(re.findall(r"[A-Za-z]", text))


def check_live_output(adapter: dict[str, Any], case: dict[str, Any], step: Any) -> list[str]:
    source = case["text"]
    output = step.output.strip()
    issues: list[str] = []
    if not step.ok:
        issues.append(f"node failed: {step.note[:260]}")
    if not output:
        issues.append("empty output")
        return issues

    if wordish_chars(output) < 40:
        issues.append("not enough prose")
    for marker in META_MARKERS:
        if marker.lower() in output.lower():
            issues.append(f"metadata leaked: {marker}")
            break
    if "```" in output:
        issues.append("code fence leaked")
    if re.search(r"^\s*(?:[-*]|\d+[.)])\s+", output, re.M):
        issues.append("list/rules format leaked")
    if "|" in output and re.search(r"\|.+\|", output):
        issues.append("table format leaked")

    src_paragraphs = server.paragraph_count(source)
    out_paragraphs = server.paragraph_count(output)
    if src_paragraphs != out_paragraphs:
        issues.append(f"paragraph count changed: {src_paragraphs} -> {out_paragraphs}")

    ratio = len(output) / max(len(source), 1)
    if ratio < 0.55:
        issues.append(f"output too short: {ratio:.0%}")
    if ratio > 1.95:
        issues.append(f"output too long: {ratio:.0%}")

    for anchor in case.get("anchors", []):
        if anchor not in output:
            issues.append(f"anchor missing: {anchor}")

    quality = server.quality_issues(output, source)
    critical_quality = [item for item in quality if "too long" not in item]
    if critical_quality:
        issues.append("quality gate still reports: " + "; ".join(critical_quality))

    return issues


def main() -> int:
    config = server.load_config()
    if not (config.get("nvidia_api_key") or ""):
        print("FAIL missing local NVIDIA API key; live QA cannot run.", flush=True)
        return 1

    adapters = server.load_adapters()
    total = len(adapters) * len(LIVE_CASES)
    if total < 50:
        print(f"FAIL live case count below 50: {total}", flush=True)
        return 1

    print(f"Live QA start: {len(adapters)} adapters x {len(LIVE_CASES)} cases = {total} cases", flush=True)
    print(f"Model: {config.get('nvidia_model')} | Endpoint: {config.get('nvidia_url')}", flush=True)

    report_path = ROOT / "tmp_live_qa_failures.json"
    if report_path.exists():
        report_path.unlink()

    failures: list[dict[str, Any]] = []
    started_all = time.time()
    index = 0
    for adapter in adapters:
        for case in LIVE_CASES:
            index += 1
            started = time.time()
            step = server.run_adapter(
                adapter,
                case["text"],
                user_note=(
                    "live QA: output natural prose only. Preserve paragraph count, citations, numbers, commands, "
                    "config keys, versions, and error messages. Do not output detection, scoring, explanations, lists, or headings."
                ),
            )
            issues = check_live_output(adapter, case, step)
            elapsed = int((time.time() - started) * 1000)
            label = f"{index:03d}/{total} {adapter['id']} :: {case['name']}"
            if issues:
                failures.append({
                    "case": label,
                    "issues": issues,
                    "warnings": step.warnings,
                    "output": step.output,
                    "note": step.note,
                    "stderr": step.stderr,
                    "elapsed_ms": elapsed,
                })
                print(f"FAIL {label} {elapsed}ms", flush=True)
                for issue in issues:
                    print(f"  - {issue}", flush=True)
            else:
                warn = f" warnings={len(step.warnings)}" if step.warnings else ""
                print(f"PASS {label} {elapsed}ms {len(step.output)} chars{warn}", flush=True)

    duration = int((time.time() - started_all) * 1000)
    print(f"\nRan {total} live cases in {duration}ms, failures: {len(failures)}", flush=True)
    if failures:
        report_path.write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Failure details written to {report_path}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
