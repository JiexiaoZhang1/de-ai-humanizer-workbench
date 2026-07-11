#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_REPORT = ROOT / "tmp_qa_deai_50_live_report.json"
REPORT_PATH = ROOT / "tmp_qa_deai_50_extra_live_failures.json"
PASS_REPORT_PATH = ROOT / "tmp_qa_deai_50_extra_live_report.json"
LIVE_TARGET = 50
FILL_IDS = [
    "puneethkotha_humanizer_workbench",
    "sgsss998_de_ai_writing_skill",
    "xoxxel_humanize_text",
    "dadananjesha_ai_text_humanizer_app",
    "theclaymethod_unslop",
    "devswha_patina",
    "ademola200_humanize_ai",
    "codeproexpert1_autohumanize_automated_docx_text_humanization",
    "eeman1113_janku_humaneyes",
    "toprak1224_toprak_ai_humanizer",
    "blader_humanizer",
    "stephenturner_skill_deslop",
]


def load_base_qa():
    spec = importlib.util.spec_from_file_location("deai_base_qa", ROOT / "tools" / "qa_deai_50_live_projects.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import qa_deai_50_live_projects.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = load_base_qa()
server = base.server


EXTRA_CASES = [
    {
        "name": "legal operations memo",
        "text": (
            "The vendor review process currently asks teams to complete a security questionnaire, upload the DPA, and confirm whether the tool "
            "stores customer data in the EU. This workflow is useful, but it still sounds more polished than precise because it does not explain "
            "who owns each step or what happens when a vendor fails Section 4.2.\n\n"
            "By May 7, procurement should publish a short checklist that separates legal review from security review. The checklist should also "
            "state whether SOC 2 Type II evidence is required before a pilot can begin."
        ),
        "anchors": ["Section 4.2", "May 7", "SOC 2 Type II"],
    },
    {
        "name": "status page update",
        "text": (
            "We opened INC-4421 after the webhook queue stopped processing events for the billing service. Customers could still create invoices, "
            "but callbacks to https://status.example.com/incidents/INC-4421 were delayed by 27 minutes and some retries were duplicated.\n\n"
            "The mitigation was to restart `worker-billing@2.8.0`, replay the failed events from s3://billing-replay/2026-04-21, and notify "
            "ops@example.com after the replay completed."
        ),
        "anchors": ["INC-4421", "https://status.example.com/incidents/INC-4421", "27 minutes", "worker-billing@2.8.0", "s3://billing-replay/2026-04-21", "ops@example.com"],
    },
    {
        "name": "research limitations",
        "text": (
            "The current study improves on earlier survey work by combining interviews with transaction logs, but the sample remains limited to "
            "42 participants from two regions. As a result, the findings should be treated as evidence of a pattern rather than a definitive "
            "estimate of national behavior.\n\n"
            "A second limitation is that participants self-reported their use of AI writing tools. Future work should compare self-reports with "
            "document histories, revision timestamps, and instructor feedback to understand where recall bias changes the interpretation."
        ),
        "anchors": ["42 participants", "AI"],
    },
    {
        "name": "appeal statement excerpt",
        "text": (
            "I understand why the panel was concerned about similarity in the submitted draft, and I am not trying to dismiss that concern. My "
            "main request is that the panel also considers the outline, dated notes, and version history showing how the argument developed before "
            "submission.\n\n"
            "The file `draft-history/week-06.md` shows that I changed the structure on March 12 after meeting my tutor. I can explain why each "
            "source was used, including Jones (2023), and I am willing to answer questions about the writing process."
        ),
        "anchors": ["draft-history/week-06.md", "March 12", "Jones (2023)"],
    },
    {
        "name": "grant application",
        "text": (
            "This proposal requests $184,500 to build a community energy dashboard for three housing associations. The project has practical value "
            "because residents currently receive delayed usage reports that are difficult to interpret and do not help them change daily behavior.\n\n"
            "The pilot will run from July 2026 to February 2027. Success will be measured through opt-in participation, average weekly dashboard "
            "use, and a 9% reduction in peak-hour electricity consumption."
        ),
        "anchors": ["$184,500", "three housing associations", "July 2026", "February 2027", "9%"],
    },
    {
        "name": "api documentation",
        "text": (
            "The endpoint `POST /v1/projects/{project_id}/exports` creates an asynchronous export job and returns `202 Accepted` with a job ID. "
            "Clients should poll `GET /v1/export_jobs/{job_id}` rather than retrying the POST request when the response is slow.\n\n"
            "If the API returns `EXPORT_LIMIT_EXCEEDED`, wait at least 60 seconds before retrying. Repeated retries can create duplicate queue "
            "pressure even though the export itself has not started."
        ),
        "anchors": ["POST /v1/projects/{project_id}/exports", "202 Accepted", "GET /v1/export_jobs/{job_id}", "EXPORT_LIMIT_EXCEEDED", "60 seconds"],
    },
    {
        "name": "board update",
        "text": (
            "Revenue grew 18% quarter over quarter, but the headline number hides two different stories. Enterprise accounts expanded faster than "
            "expected, while the self-serve funnel lost momentum after the pricing page changed on April 2.\n\n"
            "The team is not recommending another pricing change yet. The immediate plan is to restore the comparison table, run five buyer "
            "interviews, and review conversion by segment before the May board meeting."
        ),
        "anchors": ["18%", "April 2", "five buyer interviews", "May"],
    },
    {
        "name": "support escalation",
        "text": (
            "Customer ACME-17 reported that the CSV import completed but 312 rows were skipped without a clear explanation. The current error "
            "message says the import was partially successful, which is technically true but not helpful for the administrator.\n\n"
            "Support should reply with the skipped-row file, explain that the `external_user_id` column contained duplicate values, and confirm "
            "that no existing user records were changed."
        ),
        "anchors": ["ACME-17", "312 rows", "external_user_id"],
    },
    {
        "name": "privacy notice",
        "text": (
            "The app collects workspace names, project metadata, and audit events so administrators can understand how their teams use the service. "
            "It does not collect document contents unless a user explicitly chooses to upload a file for processing.\n\n"
            "For enterprise customers, audit logs are retained for 400 days by default. A customer can request a shorter retention period by "
            "emailing privacy@example.org with the workspace ID."
        ),
        "anchors": ["400 days", "privacy@example.org"],
    },
    {
        "name": "market analysis",
        "text": (
            "Demand in the mid-market segment is growing, but buyers are becoming more careful about vendor consolidation. They want fewer tools, "
            "clearer integrations, and proof that a new product will not create more administrative work.\n\n"
            "This creates an opportunity for vendors that can show measurable time savings. A useful case study should quantify setup time, weekly "
            "usage, and the specific task that became easier after adoption."
        ),
        "anchors": [],
    },
    {
        "name": "school policy explanation",
        "text": (
            "The policy allows students to use grammar tools, but it requires disclosure when AI tools generate ideas, structure, or wording. That "
            "distinction matters because a student may be allowed to check grammar while still being prohibited from submitting generated analysis.\n\n"
            "The safest response is to describe exactly what was used, when it was used, and how the final draft changed afterward. Vague claims "
            "such as 'I only used it for help' are unlikely to answer the panel's main concern."
        ),
        "anchors": ["AI"],
    },
    {
        "name": "engineering rfc",
        "text": (
            "RFC-109 proposes moving the permissions cache from Redis to Postgres so permission checks can be audited and replayed. The proposal "
            "reduces operational complexity, but it may add latency to high-volume endpoints such as `/api/search`.\n\n"
            "Before approval, the team should benchmark p95 latency with 10,000 projects, document the rollback path, and verify that the migration "
            "does not break `FEATURE_FLAG_PERMISSIONS_V2`."
        ),
        "anchors": ["RFC-109", "/api/search", "p95 latency", "10,000 projects", "FEATURE_FLAG_PERMISSIONS_V2"],
    },
]


def previously_tested_ids() -> set[str]:
    if not BASE_REPORT.exists():
        return set()
    try:
        data = json.loads(BASE_REPORT.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    return {item["adapter_id"] for item in data.get("results", []) if item.get("adapter_id")}


def select_extra_adapters(adapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {adapter["id"]: adapter for adapter in adapters}
    tested = previously_tested_ids()
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(adapter: dict[str, Any] | None) -> None:
        if not adapter or adapter["id"] in seen or len(selected) >= LIVE_TARGET:
            return
        selected.append(adapter)
        seen.add(adapter["id"])

    for adapter in adapters:
        if adapter["id"] not in tested:
            add(adapter)
    for adapter_id in FILL_IDS:
        add(by_id.get(adapter_id))
    for adapter in adapters:
        add(adapter)
    return selected[:LIVE_TARGET]


def main() -> int:
    config = server.load_config()
    if not (config.get("nvidia_api_key") or ""):
        print("FAIL missing NVIDIA API key in config.local.json", flush=True)
        return 1

    adapters = server.load_adapters()
    preflight_issues = base.preflight(adapters)
    if preflight_issues:
        print("FAIL preflight", flush=True)
        for issue in preflight_issues:
            print(f"  - {issue}", flush=True)
        return 1

    selected = select_extra_adapters(adapters)
    if len(selected) != LIVE_TARGET:
        print(f"FAIL expected {LIVE_TARGET} selected adapters, got {len(selected)}", flush=True)
        return 1

    for path in (REPORT_PATH, PASS_REPORT_PATH):
        if path.exists():
            path.unlink()

    previously_tested = previously_tested_ids()
    new_count = sum(1 for adapter in selected if adapter["id"] not in previously_tested)
    print(f"De-AI extra 50 live project tests: {len(selected)} adapters ({new_count} previously untested), {len(EXTRA_CASES)} rotating cases", flush=True)
    print(f"Model: {config.get('nvidia_model')} | Endpoint: {config.get('nvidia_url')}", flush=True)

    failures: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    started_all = time.time()
    for index, adapter in enumerate(selected, start=1):
        case = EXTRA_CASES[(index - 1) % len(EXTRA_CASES)]
        started = time.time()
        step = server.run_adapter(
            adapter,
            case["text"],
            user_note=(
                "Extra 50-case live QA: rewrite naturally while preserving exact anchors, legal/technical terms, "
                "URLs, emails, issue keys, file paths, counts, dates, percentages, and paragraph count. "
                "Return prose only: no headings, bullets, tables, scores, explanations, or before/after text."
            ),
        )
        elapsed = int((time.time() - started) * 1000)
        issues = base.check_output(step, case)
        label = f"{index:02d}/{LIVE_TARGET} {adapter['id']} :: {case['name']}"
        record = {
            "index": index,
            "adapter_id": adapter["id"],
            "adapter_name": adapter["name"],
            "repo": adapter["repo"],
            "category": adapter.get("category"),
            "integration_mode": adapter.get("integration_mode"),
            "previously_tested": adapter["id"] in previously_tested,
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
            freshness = "new" if adapter["id"] not in previously_tested else "retest"
            print(f"PASS {label} {elapsed}ms {len(step.output)} chars {freshness}{warn}", flush=True)

    duration = int((time.time() - started_all) * 1000)
    summary = {
        "total": LIVE_TARGET,
        "previously_untested": new_count,
        "failures": len(failures),
        "duration_ms": duration,
        "results": results,
    }
    PASS_REPORT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRan {LIVE_TARGET} extra live project tests in {duration}ms, failures: {len(failures)}", flush=True)
    print(f"Report written to {PASS_REPORT_PATH}", flush=True)
    if failures:
        REPORT_PATH.write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Failure details written to {REPORT_PATH}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
