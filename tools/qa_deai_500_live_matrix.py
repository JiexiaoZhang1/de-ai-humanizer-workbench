#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "tmp_qa_deai_500_live_report.json"
FAILURE_PATH = ROOT / "tmp_qa_deai_500_live_failures.json"
LIVE_TARGET = 500


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = load_module("deai_base_qa_500", ROOT / "tools" / "qa_deai_50_live_projects.py")
extra = load_module("deai_extra_qa_500", ROOT / "tools" / "qa_deai_50_extra_live_projects.py")
server = base.server


MORE_CASES = [
    {
        "name": "procurement exception",
        "text": (
            "The procurement exception for PO-7718 is not a shortcut around review. It documents why the analytics vendor must be renewed before "
            "the quarter closes, even though the standard vendor comparison was not completed.\n\n"
            "The renewal is capped at $12,450 and depends on receiving ISO 27001 evidence by June 3. If that evidence is not received, the team "
            "should switch to the fallback export process rather than extending the contract informally."
        ),
        "anchors": ["PO-7718", "$12,450", "ISO 27001", "June 3"],
    },
    {
        "name": "hr policy note",
        "text": (
            "The remote-work policy should explain how approvals are made instead of sounding like a broad statement of trust. Employees can work "
            "outside their primary country for up to 20 working days, but the request must be reviewed for payroll, tax, and security implications.\n\n"
            "For employee E-2048, the approval should state the exact location, the dates, and the manager responsible for confirming coverage. "
            "That level of detail protects the employee and the company if questions come up later."
        ),
        "anchors": ["20 working days", "E-2048"],
    },
    {
        "name": "community report",
        "text": (
            "The community food program served 8,300 meals in March, which is a strong outcome but not a complete measure of impact. The report "
            "should also explain how many households returned, how many new volunteers were trained, and whether weekend demand changed.\n\n"
            "The next report should include a short note on Route 6 because that delivery route had the highest cancellation rate. The operations "
            "team believes the issue is scheduling, not lack of demand."
        ),
        "anchors": ["8,300 meals", "March", "Route 6"],
    },
    {
        "name": "database migration note",
        "text": (
            "The migration adds `tax_region` to the invoices table so finance can separate VAT, GST, and sales-tax reporting. The change is small, "
            "but it touches export code used by both the billing dashboard and the monthly close workflow.\n\n"
            "Before merging, run `ALTER TABLE invoices ADD COLUMN tax_region text` in staging, compare the export from `reports/monthly-close.sql`, "
            "and confirm that no values are written for archived invoices."
        ),
        "anchors": ["tax_region", "ALTER TABLE invoices ADD COLUMN tax_region text", "reports/monthly-close.sql"],
    },
    {
        "name": "security advisory",
        "text": (
            "The security advisory for CVE-2026-12345 should avoid panic while still being specific about affected versions. The vulnerable path is "
            "only reachable when legacy SSO is enabled and the callback domain is configured manually.\n\n"
            "Customers running v4.8.2 should upgrade to v4.8.3 before May 14. If they cannot upgrade immediately, they should disable legacy SSO "
            "and rotate the `SSO_CALLBACK_SECRET` after the mitigation is applied."
        ),
        "anchors": ["CVE-2026-12345", "v4.8.2", "v4.8.3", "May 14", "SSO_CALLBACK_SECRET"],
    },
    {
        "name": "doi citation summary",
        "text": (
            "The paper with DOI 10.1145/3613904.3642200 is useful because it separates interface effects from model effects. That distinction "
            "matters when teams claim that a better prompt alone explains improved performance.\n\n"
            "For the literature review, compare this result with Rivera (2024) and Chen & Malik (2025). The paragraph should describe the disagreement "
            "plainly rather than pretending the studies all reach the same conclusion."
        ),
        "anchors": ["10.1145/3613904.3642200", "Rivera (2024)", "Chen & Malik (2025)"],
    },
    {
        "name": "accessibility audit",
        "text": (
            "The accessibility audit found that the onboarding modal meets most keyboard requirements, but the focus order becomes confusing after "
            "the user opens the role selector. This is not just a polish issue because screen-reader users may miss the confirmation message.\n\n"
            "The next release should target WCAG 2.2 AA, add a visible focus state for the role list, and retest the flow with VoiceOver before "
            "shipping the redesigned modal."
        ),
        "anchors": ["WCAG 2.2 AA", "VoiceOver"],
    },
    {
        "name": "finance risk memo",
        "text": (
            "The risk memo should distinguish between revenue concentration and collection risk. Customer Northstar accounts for 31% of annual "
            "recurring revenue, but it has paid invoices on time for 11 consecutive quarters.\n\n"
            "The higher concern is that three smaller customers moved from annual payment to quarterly payment after their budgets were cut. That "
            "change does not create an immediate cash problem, but it weakens forecast confidence for Q3."
        ),
        "anchors": ["31%", "11 consecutive quarters", "Q3"],
    },
    {
        "name": "curriculum update",
        "text": (
            "Module 3 should spend less time defining basic terms and more time showing how students can critique a weak argument. The current "
            "lesson sounds complete, but it gives students too few chances to practice judgment.\n\n"
            "Add one worked example, two short peer-review prompts, and a final reflection question. The reflection should ask students to explain "
            "what evidence would change their mind, not just whether they agree with the author."
        ),
        "anchors": ["Module 3", "two short peer-review prompts"],
    },
    {
        "name": "lab protocol",
        "text": (
            "The lab protocol for PCR-204 should say why samples are excluded, not only list the exclusion criteria. The most common issue is that "
            "late samples arrive after the reagent window has closed, which makes the measurement unreliable.\n\n"
            "Record exclusions in `samples/run_17.csv` and include the technician initials. If more than 5% of samples are excluded, the run should "
            "be reviewed before the results are shared."
        ),
        "anchors": ["PCR-204", "samples/run_17.csv", "5%"],
    },
    {
        "name": "meeting recap",
        "text": (
            "The growth team agreed that the onboarding experiment should not launch until the help center article is ready. The draft experiment "
            "plan is strong, but it assumes users will understand the new import step without guidance.\n\n"
            "Post the revised copy in #growth-ops by Friday and ask support to review the article for common confusion points. The launch decision "
            "should happen after those comments are resolved."
        ),
        "anchors": ["#growth-ops", "Friday"],
    },
    {
        "name": "refund response",
        "text": (
            "The response to order ORD-90817 should be clear about what happened and what the customer can expect next. The duplicate charge was "
            "created when the payment page was refreshed after the bank authorization completed.\n\n"
            "Confirm that the $49.00 refund has been issued, explain that it may take 3 business days to appear, and send the receipt from "
            "refunds@shop.test."
        ),
        "anchors": ["ORD-90817", "$49.00", "3 business days", "refunds@shop.test"],
    },
    {
        "name": "patent summary",
        "text": (
            "Claim 7 is narrower than the abstract suggests because it depends on a specific ranking step after the sensor data is normalized. The "
            "summary should make that limitation visible so readers do not overstate the scope of the filing.\n\n"
            "The strongest evidence is in Figure 4, where the prototype compares the ranked signal against a baseline threshold. The text should "
            "describe that comparison without implying that the patent covers every sensor workflow."
        ),
        "anchors": ["Claim 7", "Figure 4"],
    },
    {
        "name": "sales followup",
        "text": (
            "The follow-up email should not say that the platform will transform the customer's entire workflow. The buyer asked a narrower question: "
            "whether the tool can reduce the time spent preparing board packets.\n\n"
            "A better reply should mention the 6-hour reduction from the pilot, offer to walk through the packet template, and confirm whether the "
            "CFO wants the export in PDF or PowerPoint."
        ),
        "anchors": ["6-hour", "CFO", "PDF", "PowerPoint"],
    },
    {
        "name": "open source release",
        "text": (
            "The release note for v0.12.0 should separate breaking changes from migration tips. Users need to know that `config.plugins` has been "
            "renamed to `extensions`, but they also need a quick example of the new shape.\n\n"
            "Link to https://docs.example.dev/migration/v0.12 and mention that the old key will keep working until September 2026. That gives teams "
            "time to update without treating the release as an emergency."
        ),
        "anchors": ["v0.12.0", "config.plugins", "extensions", "https://docs.example.dev/migration/v0.12", "September 2026"],
    },
    {
        "name": "museum label",
        "text": (
            "The museum label should explain why the repaired ceramic bowl matters without turning it into a generic story about resilience. The "
            "object was used in a household kitchen, repaired twice, and kept for another generation.\n\n"
            "Mention the 1897 repair mark and the donor note from L. Armitage. Those details help visitors see the bowl as an object with a traceable "
            "life rather than a symbol chosen after the fact."
        ),
        "anchors": ["1897", "L. Armitage"],
    },
    {
        "name": "incident customer note",
        "text": (
            "The customer note should acknowledge the outage without sounding evasive. Workspace exports failed between 09:10 and 09:44 UTC because "
            "the export worker could not read from the temporary file store.\n\n"
            "Tell customers that no files were lost, that queued exports were replayed, and that the team added an alert for `tmp_store_read_errors` "
            "before closing the incident."
        ),
        "anchors": ["09:10", "09:44 UTC", "tmp_store_read_errors"],
    },
    {
        "name": "academic methods paragraph",
        "text": (
            "The interview protocol was revised after the pilot because participants interpreted the word trust in different ways. Some discussed "
            "institutional trust, while others focused on whether they trusted the interface to show accurate information.\n\n"
            "The final protocol therefore separates trust in the institution from trust in the tool. This distinction follows Morgan (2022), but "
            "the coding scheme was adapted for a workplace setting."
        ),
        "anchors": ["Morgan (2022)"],
    },
    {
        "name": "policy rollback",
        "text": (
            "The rollback plan should state when the new moderation policy will be paused and who can make that decision. A vague statement about "
            "monitoring feedback is not enough because the policy affects creator payouts.\n\n"
            "If appeals increase by more than 22% for two consecutive weeks, Trust & Safety should pause the rollout and publish a short update "
            "explaining what will be reviewed."
        ),
        "anchors": ["22%", "Trust & Safety"],
    },
    {
        "name": "real estate brief",
        "text": (
            "The property brief should not oversell the site as turnkey. The building has strong transport access and good ceiling height, but the "
            "loading bay needs repair and the current lease restricts evening deliveries.\n\n"
            "The key numbers are 18,200 square feet, 11 parking spaces, and an asking rent of £42 per square foot. Those details should appear before "
            "any broader claims about growth potential."
        ),
        "anchors": ["18,200 square feet", "11 parking spaces", "£42"],
    },
    {
        "name": "medical admin notice",
        "text": (
            "The clinic notice should explain the scheduling change without sounding like a marketing announcement. From August 2026, routine blood "
            "tests will be booked through the patient portal rather than by phone.\n\n"
            "Patients who cannot use the portal can still call reception. The notice should make that exception clear so older patients do not think "
            "they have lost access to appointments."
        ),
        "anchors": ["August 2026"],
    },
    {
        "name": "nonprofit board note",
        "text": (
            "The board note should distinguish between volunteer retention and volunteer recruitment. Recruitment improved after the spring campaign, "
            "but retention fell because weekend shifts were harder to fill.\n\n"
            "The program needs 14 additional Saturday volunteers by November 2026. If that target is missed, the team should reduce Saturday delivery "
            "routes rather than stretching the same volunteers further."
        ),
        "anchors": ["14 additional Saturday volunteers", "November 2026"],
    },
    {
        "name": "legal clause explanation",
        "text": (
            "Clause 8.3 does not prevent the customer from exporting their own data. It only limits bulk extraction of enriched benchmark data created "
            "by the service provider.\n\n"
            "The explanation should state that distinction plainly and avoid implying that the customer needs permission to download ordinary account "
            "records. That point should be checked against Article 12(b) before the contract is sent."
        ),
        "anchors": ["Clause 8.3", "Article 12(b)"],
    },
    {
        "name": "warehouse process",
        "text": (
            "The warehouse process currently asks pickers to scan an item, place it in a tote, and then confirm the tote at the packing station. That "
            "sequence works, but it creates confusion when a tote is reassigned during a rush period.\n\n"
            "The revised process should add a second scan at Zone C and require supervisors to clear exception code WH-77 before the order can be "
            "closed."
        ),
        "anchors": ["Zone C", "WH-77"],
    },
    {
        "name": "translation style note",
        "text": (
            "The translation note should preserve the difference between formal and friendly tone. The source copy uses direct language, but it does "
            "not sound casual enough for a chat notification.\n\n"
            "For the French version, keep the product name AtlasFlow unchanged and avoid translating the command `Run sync now`. The final message "
            "should feel helpful without adding new promises."
        ),
        "anchors": ["AtlasFlow", "Run sync now"],
    },
    {
        "name": "developer changelog",
        "text": (
            "The changelog should explain why the SDK now retries 429 responses by default. The old behavior pushed retry logic into every customer "
            "integration, which made rate-limit handling inconsistent.\n\n"
            "In version v3.4.0, retries use exponential backoff with a maximum delay of 8 seconds. Developers can disable the behavior with "
            "`retry: false` if they already manage retries upstream."
        ),
        "anchors": ["429", "v3.4.0", "8 seconds", "retry: false"],
    },
    {
        "name": "training evaluation",
        "text": (
            "The training evaluation should not claim that the workshop improved manager confidence unless the evidence supports that claim. The "
            "survey response rate was 46%, and the comments mostly describe clearer expectations rather than confidence.\n\n"
            "A more accurate summary is that the workshop helped managers understand the new review rubric. The next evaluation should ask whether "
            "they used the rubric during an actual review cycle."
        ),
        "anchors": ["46%"],
    },
    {
        "name": "quality assurance note",
        "text": (
            "The QA note should explain the root cause of the escaped defect, not only list the steps used to reproduce it. The bug occurred because "
            "the test account had both beta billing and legacy discounts enabled.\n\n"
            "Add a regression test for account `qa_legacy_018`, then update `tests/billing/discounts.spec.ts` so the same combination is covered in "
            "CI before the next release."
        ),
        "anchors": ["qa_legacy_018", "tests/billing/discounts.spec.ts", "CI"],
    },
]


CASE_BANK = base.CASE_BANK + extra.EXTRA_CASES + MORE_CASES


def build_matrix(adapters: list[dict[str, Any]], target: int = LIVE_TARGET) -> list[tuple[int, dict[str, Any], dict[str, Any]]]:
    matrix: list[tuple[int, dict[str, Any], dict[str, Any]]] = []
    index = 1
    round_no = 0
    while len(matrix) < target:
        for adapter_index, adapter in enumerate(adapters):
            case = CASE_BANK[(adapter_index + round_no * len(adapters)) % len(CASE_BANK)]
            matrix.append((index, adapter, case))
            index += 1
            if len(matrix) >= target:
                break
        round_no += 1
    return matrix


def load_existing_ok() -> dict[int, dict[str, Any]]:
    if not REPORT_PATH.exists():
        return {}
    try:
        data = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {int(item["index"]): item for item in data.get("results", []) if item.get("ok")}


def write_report(results: list[dict[str, Any]], failures: list[dict[str, Any]], started_all: float) -> None:
    summary = {
        "total": LIVE_TARGET,
        "case_count": len(CASE_BANK),
        "adapter_count": len(server.load_adapters()),
        "completed": len(results),
        "failures": len(failures),
        "duration_ms": int((time.time() - started_all) * 1000),
        "results": sorted(results, key=lambda item: item["index"]),
    }
    REPORT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if failures:
        FAILURE_PATH.write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")
    elif FAILURE_PATH.exists():
        FAILURE_PATH.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run 500 sequential De-AI live QA tests")
    parser.add_argument("--resume", action="store_true", help="Reuse passed records in the existing 500-test report")
    parser.add_argument("--stop-on-fail", action="store_true", help="Stop immediately when a test fails")
    parser.add_argument("--limit", type=int, default=LIVE_TARGET, help="Maximum number of matrix rows to execute")
    args = parser.parse_args()

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

    matrix = build_matrix(adapters, target=LIVE_TARGET)
    existing_ok = load_existing_ok() if args.resume else {}
    results_by_index: dict[int, dict[str, Any]] = dict(existing_ok)
    failures: list[dict[str, Any]] = []
    executed = 0
    started_all = time.time()

    print(f"De-AI 500 live matrix: {LIVE_TARGET} tests, {len(adapters)} adapters, {len(CASE_BANK)} cases", flush=True)
    print(f"Model: {config.get('nvidia_model')} | Endpoint: {config.get('nvidia_url')}", flush=True)
    if existing_ok:
        print(f"Resume mode: {len(existing_ok)} passed tests already recorded", flush=True)

    for index, adapter, case in matrix:
        if executed >= args.limit:
            break
        if index in existing_ok:
            continue
        started = time.time()
        step = server.run_adapter(
            adapter,
            case["text"],
            user_note=(
                "500-case live QA: rewrite naturally and preserve exact anchors, paragraph count, facts, legal references, "
                "technical identifiers, money amounts, dates, percentages, URLs, emails, paths, and code spans. "
                "Return prose only with no headings, bullets, tables, scores, explanations, or before/after text."
            ),
        )
        elapsed = int((time.time() - started) * 1000)
        issues = base.check_output(step, case)
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
        label = f"{index:03d}/{LIVE_TARGET} {adapter['id']} :: {case['name']}"
        if issues:
            failure = {
                **record,
                "note": step.note,
                "stderr": step.stderr,
                "output": step.output,
                "source": case["text"],
                "anchors": case.get("anchors", []),
            }
            failures.append(failure)
            results_by_index[index] = record
            write_report(list(results_by_index.values()), failures, started_all)
            print(f"FAIL {label} {elapsed}ms", flush=True)
            for issue in issues:
                print(f"  - {issue}", flush=True)
            if args.stop_on_fail:
                print(f"Stopped on first failure. Report: {REPORT_PATH}", flush=True)
                return 1
        else:
            results_by_index[index] = record
            warn = f" warnings={len(step.warnings)}" if step.warnings else ""
            print(f"PASS {label} {elapsed}ms {len(step.output)} chars{warn}", flush=True)
            if index % 10 == 0:
                write_report(list(results_by_index.values()), failures, started_all)
        executed += 1

    write_report(list(results_by_index.values()), failures, started_all)
    completed = len([item for item in results_by_index.values() if item.get("ok")])
    print(f"\nCompleted {completed}/{LIVE_TARGET} tests, failures: {len(failures)}", flush=True)
    print(f"Report written to {REPORT_PATH}", flush=True)
    if failures:
        print(f"Failure details written to {FAILURE_PATH}", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
