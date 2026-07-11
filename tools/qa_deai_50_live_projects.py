#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "tmp_qa_deai_50_live_failures.json"
PASS_REPORT_PATH = ROOT / "tmp_qa_deai_50_live_report.json"
DEFAULT_IDS = [
    "blader_humanizer",
    "stephenturner_skill_deslop",
    "jalaalrd_anti_ai_slop_writing",
    "gabelul_slopbuster",
    "hugolopes45_llmstrip",
]
LIVE_TARGET = 50


def load_server():
    spec = importlib.util.spec_from_file_location("deai_server_under_test", ROOT / "server.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import server.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


server = load_server()


CASE_BANK = [
    {
        "name": "generic ai business prose",
        "text": (
            "In today's rapidly evolving digital landscape, organizations are increasingly leveraging AI to streamline workflows "
            "and unlock unprecedented value across departments. This paper aims to explore the significant impact of AI adoption "
            "on operational efficiency, knowledge management, and long-term business transformation.\n\n"
            "Furthermore, it is important to note that successful implementation requires a holistic approach that combines technical "
            "infrastructure, employee training, ethical governance, and continuous improvement. In conclusion, AI has the potential "
            "to revolutionize modern organizations and drive sustainable competitive advantage."
        ),
        "anchors": ["AI"],
    },
    {
        "name": "technical release note",
        "text": (
            "During the v2.3.1 canary rollout, the platform team ran `bin/migrate --tenant=prod --dry-run` and verified that "
            "`DB_SCHEMA_VERSION=20260412` matched production. This process significantly improved system stability and created "
            "a strong foundation for future iterations.\n\n"
            "If the logs show `schema mismatch on orders_v2`, do not broaden the remediation plan immediately. Check the config, "
            "migration script, and rollback window first, then decide whether the release should continue."
        ),
        "anchors": ["v2.3.1", "DB_SCHEMA_VERSION=20260412", "schema mismatch on orders_v2"],
    },
    {
        "name": "academic abstract",
        "text": (
            "This study examines community-based eldercare service provision using panel data from 2018 to 2023. It constructs "
            "a multi-indicator evaluation framework to analyze resource allocation, service accessibility, and resident satisfaction. "
            "The results indicate that digital platforms improve information matching but remain limited in their coverage of younger "
            "seniors, offline coordination, and privacy protection.\n\n"
            "Further analysis shows that adding platform features alone does not automatically improve service experience. Response time "
            "from community workers, participation from family caregivers, and stable grassroots funding all affect the final outcome."
        ),
        "anchors": ["2018", "2023"],
    },
    {
        "name": "citation dense literature review",
        "text": (
            "Recent work on retrieval-augmented generation argues that knowledge access improves answer quality, yet the evidence remains "
            "mixed when prompts are noisy or documents conflict (Nguyen, 2024; Patel & Rossi, 2025). This section therefore evaluates "
            "whether retrieved context improves traceability rather than assuming it automatically improves reasoning.\n\n"
            "The strongest studies report gains when retrieval is paired with source ranking, contradiction checks, and explicit abstention "
            "rules. The weaker studies often treat retrieval as a single feature flag, which makes their conclusions difficult to compare."
        ),
        "anchors": ["Nguyen, 2024", "Patel & Rossi, 2025"],
    },
    {
        "name": "product incident memo",
        "text": (
            "At 14:32 UTC, the notification worker began retrying stale jobs after Redis failover changed the lock owner. The incident did "
            "not expose customer data, but it delayed 18,420 outbound messages and increased queue latency from 40 seconds to 11 minutes.\n\n"
            "The immediate fix was to pause the worker, clear duplicate job IDs, and deploy lock validation in `worker-notify@1.18.7`. "
            "The follow-up is to add a canary alarm before the next regional failover test."
        ),
        "anchors": ["14:32 UTC", "18,420", "worker-notify@1.18.7"],
    },
    {
        "name": "policy explanation",
        "text": (
            "The new expense policy is designed to create a clear and transparent approval process for travel, meals, and software purchases. "
            "Employees should submit receipts within 14 days, include a short business purpose, and use the correct department code.\n\n"
            "Managers should review requests for accuracy rather than personal preference. If a purchase is unusual but legitimate, the manager "
            "should add context in the approval note instead of rejecting it without explanation."
        ),
        "anchors": ["14 days"],
    },
    {
        "name": "startup investor update",
        "text": (
            "We achieved meaningful traction in Q1 by expanding the pilot from 6 clinics to 19 clinics and increasing weekly active users by 38%. "
            "This growth demonstrates strong market validation and highlights the scalable nature of our platform.\n\n"
            "However, churn in smaller clinics remains higher than expected because onboarding still requires too much manual configuration. "
            "The next product milestone is a self-serve setup flow that reduces implementation time from five days to one day."
        ),
        "anchors": ["Q1", "6", "19", "38%"],
    },
    {
        "name": "customer email",
        "text": (
            "Thank you for reaching out about invoice INV-20481. We understand that billing delays can create unnecessary friction for your "
            "finance team, and we appreciate your patience while we investigate the issue.\n\n"
            "Our records show that the payment was received on April 18, but the receipt email failed because the account contact was set to "
            "`old-ap@example.com`. We have updated the contact and attached a corrected receipt."
        ),
        "anchors": ["INV-20481", "April 18", "old-ap@example.com"],
    },
    {
        "name": "data analysis summary",
        "text": (
            "The April cohort converted at 12.8%, which is higher than the March cohort but still below the 15% target. The largest drop-off "
            "appears between account creation and first project import, suggesting that onboarding friction remains the main constraint.\n\n"
            "Segment analysis shows that teams with fewer than 20 employees respond better to templates, while larger teams need role-based "
            "permissions before they invite colleagues. This difference should shape the next onboarding experiment."
        ),
        "anchors": ["12.8%", "15%", "20"],
    },
    {
        "name": "plain one paragraph",
        "text": (
            "The draft currently sounds polished but generic, with several claims that are directionally true but not grounded in concrete details. "
            "The next revision should keep the same meaning while making the rhythm less formulaic and the examples easier to trust."
        ),
        "anchors": [],
    },
]


META_MARKERS = (
    "Detection result",
    "AI detection",
    "AI score",
    "Human score",
    "Perplexity",
    "Burstiness",
    "Rewrite notes",
    "Revision notes",
    "Analysis report",
    "Quality check",
    "Changes made",
    "Here is",
    "Below is",
    "I cannot",
    "As an AI",
)


def wordish_chars(text: str) -> int:
    return len(re.findall(r"[A-Za-z]", text))


def normalize_for_compare(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()


def select_adapters(adapters: list[dict[str, Any]], target: int = LIVE_TARGET) -> list[dict[str, Any]]:
    by_id = {adapter["id"]: adapter for adapter in adapters}
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(adapter: dict[str, Any] | None) -> None:
        if not adapter or adapter["id"] in seen or len(selected) >= target:
            return
        selected.append(adapter)
        seen.add(adapter["id"])

    for adapter_id in DEFAULT_IDS:
        add(by_id.get(adapter_id))

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for adapter in adapters:
        groups[adapter.get("category", "Other")].append(adapter)
    categories = sorted(groups, key=lambda name: (-len(groups[name]), name))

    while len(selected) < target:
        changed = False
        for category in categories:
            for adapter in groups[category]:
                if adapter["id"] not in seen:
                    add(adapter)
                    changed = True
                    break
            if len(selected) >= target:
                break
        if not changed:
            break
    return selected


def preflight(adapters: list[dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    if len(adapters) < 88:
        issues.append(f"expected at least 88 adapters, got {len(adapters)}")
    ids = [adapter["id"] for adapter in adapters]
    if len(ids) != len(set(ids)):
        issues.append("adapter IDs are not unique")
    for adapter in adapters:
        path = ROOT / adapter["path"]
        if not path.exists():
            issues.append(f"missing adapter path: {adapter['id']} -> {adapter['path']}")
        if adapter.get("kind") != "llm_prompt":
            issues.append(f"unexpected adapter kind: {adapter['id']} -> {adapter.get('kind')}")
        description = adapter.get("description", "")
        if re.match(r"^(?:<|!\[|\[!\[|title\s*:|Access the web version here|What is Humanize AI Text|1\.\s+Copy|Note:\s+Visit|This is a \[Next\.js\]|Major Update)", description, re.I):
            issues.append(f"raw README fragment in description: {adapter['id']}")
    for adapter_id in DEFAULT_IDS:
        if adapter_id not in ids:
            issues.append(f"default adapter missing: {adapter_id}")
    return issues


def check_output(step: Any, case: dict[str, Any]) -> list[str]:
    source = case["text"]
    output = step.output.strip()
    issues: list[str] = []
    if not step.ok:
        issues.append(f"node failed: {step.note[:260]}")
    if not output:
        issues.append("empty output")
        return issues
    if wordish_chars(output) < 60:
        issues.append("not enough prose")
    for marker in META_MARKERS:
        if marker.lower() in output.lower():
            issues.append(f"metadata or refusal leaked: {marker}")
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
    if ratio < 0.65:
        issues.append(f"output too short: {ratio:.0%}")
    if ratio > 1.85:
        issues.append(f"output too long: {ratio:.0%}")
    for anchor in case.get("anchors", []):
        if anchor not in output:
            issues.append(f"anchor missing: {anchor}")
    if len(source) >= 160 and normalize_for_compare(output) == normalize_for_compare(source):
        issues.append("output unchanged from source")
    quality = server.quality_issues(output, source)
    if quality:
        issues.append("quality gate reports: " + "; ".join(quality))
    return issues


def main() -> int:
    config = server.load_config()
    if not (config.get("nvidia_api_key") or ""):
        print("FAIL missing NVIDIA API key in config.local.json", flush=True)
        return 1

    adapters = server.load_adapters()
    preflight_issues = preflight(adapters)
    if preflight_issues:
        print("FAIL preflight", flush=True)
        for issue in preflight_issues:
            print(f"  - {issue}", flush=True)
        return 1

    selected = select_adapters(adapters)
    if len(selected) != LIVE_TARGET:
        print(f"FAIL expected {LIVE_TARGET} selected adapters, got {len(selected)}", flush=True)
        return 1

    if REPORT_PATH.exists():
        REPORT_PATH.unlink()
    if PASS_REPORT_PATH.exists():
        PASS_REPORT_PATH.unlink()

    print(f"De-AI 50 live project tests: {len(selected)} adapters, {len(CASE_BANK)} rotating cases", flush=True)
    print(f"Model: {config.get('nvidia_model')} | Endpoint: {config.get('nvidia_url')}", flush=True)

    failures: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    started_all = time.time()
    for index, adapter in enumerate(selected, start=1):
        case = CASE_BANK[(index - 1) % len(CASE_BANK)]
        started = time.time()
        step = server.run_adapter(
            adapter,
            case["text"],
            user_note=(
                "50-case live QA: rewrite naturally, preserve paragraph count and anchors exactly, "
                "return only prose, no headings, no bullets, no detector scores, no explanations."
            ),
        )
        elapsed = int((time.time() - started) * 1000)
        issues = check_output(step, case)
        label = f"{index:02d}/{LIVE_TARGET} {adapter['id']} :: {case['name']}"
        record = {
            "index": index,
            "adapter_id": adapter["id"],
            "adapter_name": adapter["name"],
            "repo": adapter["repo"],
            "category": adapter.get("category"),
            "integration_mode": adapter.get("integration_mode"),
            "case": case["name"],
            "elapsed_ms": elapsed,
            "ok": not issues,
            "issues": issues,
            "warnings": step.warnings,
            "output_chars": len(step.output),
        }
        results.append(record)
        if issues:
            failures.append({
                **record,
                "note": step.note,
                "stderr": step.stderr,
                "output": step.output,
                "source": case["text"],
            })
            print(f"FAIL {label} {elapsed}ms", flush=True)
            for issue in issues:
                print(f"  - {issue}", flush=True)
        else:
            warn = f" warnings={len(step.warnings)}" if step.warnings else ""
            print(f"PASS {label} {elapsed}ms {len(step.output)} chars{warn}", flush=True)

    duration = int((time.time() - started_all) * 1000)
    summary = {
        "total": LIVE_TARGET,
        "failures": len(failures),
        "duration_ms": duration,
        "results": results,
    }
    PASS_REPORT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRan {LIVE_TARGET} live project tests in {duration}ms, failures: {len(failures)}", flush=True)
    print(f"Report written to {PASS_REPORT_PATH}", flush=True)
    if failures:
        REPORT_PATH.write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Failure details written to {REPORT_PATH}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
