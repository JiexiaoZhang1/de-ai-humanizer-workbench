#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import io
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from contextlib import redirect_stderr
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]


def load_server():
    spec = importlib.util.spec_from_file_location("humanizer_server", ROOT / "server.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load server.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


server = load_server()


def fake_nvidia_chat(messages: list[dict[str, str]], max_tokens: int | None = None) -> str:
    user = messages[-1]["content"]
    marker = "Text to rewrite:\n"
    if marker in user:
        body = user.split(marker, 1)[1]
        body = body.split("\n\nRewrite using this node", 1)[0]
        return body.strip()
    marker = "Source text:\n"
    if marker in user:
        body = user.split(marker, 1)[1]
        return body.split("\n\nPrevious failed output:", 1)[0].strip()
    return "This is a concise rewritten English paragraph."


server.nvidia_chat = fake_nvidia_chat


class Runner:
    def __init__(self) -> None:
        self.total = 0
        self.failed: list[tuple[int, str, str]] = []

    def test(self, name: str, fn: Callable[[], Any]) -> None:
        self.total += 1
        number = self.total
        try:
            fn()
            print(f"{number:02d}. PASS {name}")
        except Exception as exc:  # noqa: BLE001 - QA runner must keep going.
            self.failed.append((number, name, str(exc)))
            print(f"{number:02d}. FAIL {name} :: {exc}")

    def done(self) -> int:
        print(f"\nRan {self.total} tests, failures: {len(self.failed)}")
        if self.failed:
            print("\nFailures:")
            for number, name, message in self.failed:
                print(f"- {number:02d}. {name}: {message}")
        return 1 if self.failed else 0


def assert_true(value: Any, message: str = "expected truthy value") -> None:
    if not value:
        raise AssertionError(message)


def assert_equal(actual: Any, expected: Any, message: str = "") -> None:
    if actual != expected:
        raise AssertionError(message or f"expected {expected!r}, got {actual!r}")


def assert_in(needle: Any, haystack: Any, message: str = "") -> None:
    if needle not in haystack:
        raise AssertionError(message or f"{needle!r} not found")


def assert_not_in(needle: Any, haystack: Any, message: str = "") -> None:
    if needle in haystack:
        raise AssertionError(message or f"{needle!r} unexpectedly found")


def assert_raises(fn: Callable[[], Any], exc_type: type[BaseException], status: int | None = None) -> None:
    try:
        fn()
    except exc_type as exc:
        if status is not None:
            assert_equal(getattr(exc, "status", None), status)
        return
    raise AssertionError(f"expected {exc_type.__name__}")


def start_test_server() -> tuple[str, ThreadingHTTPServer]:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{httpd.server_port}"
    for _ in range(50):
        try:
            get_json(base + "/api/health")
            break
        except Exception:
            time.sleep(0.02)
    return base, httpd


def request(url: str, method: str = "GET", payload: dict[str, Any] | None = None) -> tuple[int, bytes, str]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read(), resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), exc.headers.get("Content-Type", "")


def get_text(url: str) -> str:
    status, body, _ = request(url)
    assert_equal(status, 200)
    return body.decode("utf-8")


def get_json(url: str) -> dict[str, Any]:
    status, body, content_type = request(url)
    assert_equal(status, 200)
    assert_in("application/json", content_type)
    return json.loads(body.decode("utf-8"))


def post_json(url: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    status, body, content_type = request(url, method="POST", payload=payload)
    assert_in("application/json", content_type)
    return status, json.loads(body.decode("utf-8"))


def main() -> int:
    r = Runner()
    adapters = server.load_adapters()
    config = server.load_config()
    app_js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    styles = (ROOT / "static" / "styles.css").read_text(encoding="utf-8")
    index = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    config_example = json.loads((ROOT / "config.example.json").read_text(encoding="utf-8"))
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    sample = (
        "As AI tools become woven into everyday research work, teams often produce drafts that sound polished but generic. "
        "This section explains why editorial review still matters for accuracy, voice, and accountability.\n\n"
        "If the release note mentions `DB_SCHEMA_VERSION=20260412` or API v2.3.1, those details must remain intact. "
        "The rewrite should feel natural without changing the operational meaning."
    )

    r.test("config includes NVIDIA URL", lambda: assert_true(config.get("nvidia_url", "").startswith("https://")))
    r.test("config includes model name", lambda: assert_in("/", config.get("nvidia_model", "")))
    r.test("default max_tokens is positive", lambda: assert_true(int(config.get("default_max_tokens", 0)) > 0))
    r.test("temperature is in range", lambda: assert_true(0 <= float(config.get("temperature", 0)) <= 2))
    r.test("adapter count is high", lambda: assert_true(len(adapters) >= 85, len(adapters)))
    r.test("adapter IDs are unique", lambda: assert_equal(len({a["id"] for a in adapters}), len(adapters)))
    r.test("adapter names are non-empty", lambda: assert_true(all(a.get("name") for a in adapters)))
    r.test("adapter repos include owner/name", lambda: assert_true(all("/" in a.get("repo", "") for a in adapters)))
    r.test("adapter profiles exist", lambda: assert_true(all((ROOT / "prompts" / a["prompt_profile"]).is_file() for a in adapters)))
    r.test("all adapters are LLM prompt wrappers", lambda: assert_true(all(a.get("kind") == "llm_prompt" for a in adapters)))
    r.test("adapter categories are non-empty", lambda: assert_true(all(a.get("category") for a in adapters)))
    r.test("adapter prompt file lists are non-empty", lambda: assert_true(all(a.get("prompt_files") for a in adapters)))
    r.test("native skill adapters exist", lambda: assert_true(any(a.get("integration_mode") == "native_skill" for a in adapters)))
    r.test("decomposed Node/Web adapters exist", lambda: assert_true(any(a.get("integration_mode") == "decomposed_node_web" for a in adapters)))
    r.test("decomposed Python adapters exist", lambda: assert_true(any(a.get("integration_mode") == "decomposed_python" for a in adapters)))
    r.test("all adapters remain available without source caches", lambda: assert_true(all(a["available"] for a in adapters)))
    r.test("source cache state is explicit", lambda: assert_true(all(isinstance(a["source_cached"], bool) for a in adapters)))
    r.test("adapter_by_id finds default node", lambda: assert_equal(server.adapter_by_id("blader_humanizer")["repo"], "blader/humanizer"))
    r.test("adapter_by_id unknown returns 404", lambda: assert_raises(lambda: server.adapter_by_id("__missing__"), server.AppError, 404))
    r.test("read_prompt_material includes built-in profile", lambda: assert_in("BUILT-IN PROFILE", server.read_prompt_material(server.adapter_by_id("blader_humanizer"))))
    r.test("config example leaves API key empty", lambda: assert_equal(config_example["nvidia_api_key"], ""))
    r.test("gitignore excludes local config", lambda: assert_in("config.local.json", gitignore))
    r.test("safe path rejects traversal", lambda: assert_raises(lambda: server._safe_relative("../secret"), server.AppError, 500))

    r.test("normalize_text unifies CRLF", lambda: assert_equal(server.normalize_text(" A \r\nB \r C "), "A\nB\nC"))
    r.test("normalize_text collapses triple breaks", lambda: assert_equal(server.normalize_text("One\n\n\nTwo"), "One\n\nTwo"))
    r.test("split_paragraphs detects paragraphs", lambda: assert_equal(len(server.split_paragraphs(sample)), 2))
    r.test("paragraph_count returns 2", lambda: assert_equal(server.paragraph_count(sample), 2))
    r.test("demo rewrite preserves paragraphs", lambda: assert_equal(server.paragraph_count(server.demo_chat([{"role": "user", "content": f"Text to rewrite:\n{sample}\n\nRewrite using this node"}])), 2))
    r.test("demo rewrite changes matching prose", lambda: assert_not_in("become woven into", server.demo_chat([{"role": "user", "content": "Text to rewrite:\nAI tools become woven into daily work.\n\nRewrite using this node"}])))
    r.test("sanitize_output removes code fences", lambda: assert_equal(server.sanitize_output("```\nPlain text\n```")[0], "Plain text"))
    r.test("sanitize_output removes detection line", lambda: assert_not_in("Detection result", server.sanitize_output("Detection result: 90\nPlain text", sample)[0]))
    r.test("sanitize_output keeps inline final text", lambda: assert_equal(server.sanitize_output("Final text: This is prose.")[0], "This is prose."))
    r.test("sanitize_output truncates notes section", lambda: assert_equal(server.sanitize_output("Prose here.\n\nNotes\nDo not show", sample)[0], "Prose here."))
    r.test("sanitize_output removes orphan transition", lambda: assert_equal(server.sanitize_output("In conclusion\n\nActual prose")[0], "Actual prose"))
    r.test("sanitize_output restores paragraph breaks", lambda: assert_equal(server.paragraph_count(server.sanitize_output("One\nTwo", "Source one\n\nSource two")[0]), 2))
    r.test("sanitize_output restores AI acronym", lambda: assert_in("AI", server.sanitize_output("artificial intelligence tools matter.", "AI tools matter.")[0]))
    r.test("sanitize_output restores config equals value", lambda: assert_in("DB_SCHEMA_VERSION=20260412", server.sanitize_output("The `DB_SCHEMA_VERSION` value is 20260412.", "`DB_SCHEMA_VERSION=20260412`")[0]))
    r.test("sanitize_output restores number unit phrase", lambda: assert_in("14 days", server.sanitize_output("Submit within a 14-day timeframe.", "Submit within 14 days.")[0]))
    r.test("sanitize_output restores quantified noun phrase", lambda: assert_in("14 additional Saturday volunteers", server.sanitize_output("The program requires 14 more Saturday volunteers.", "The program needs 14 additional Saturday volunteers.")[0]))
    r.test("sanitize_output restores word quantified noun phrase", lambda: assert_in("one worked example", server.sanitize_output("Add a detailed worked example.", "Add one worked example.")[0]))
    r.test("extract_protected_terms includes numeric anchors", lambda: assert_true(all(term in server.extract_protected_terms("At 14:32 UTC, 18,420 messages hit 12.8% after 14 days.") for term in ["14:32 UTC", "18,420", "12.8%", "14 days"])))
    r.test("extract_protected_terms includes quantified nouns", lambda: assert_true(all(term in server.extract_protected_terms("The program needs 14 additional Saturday volunteers, two short peer-review prompts, and 11 consecutive quarters.") for term in ["14 additional Saturday volunteers", "two short peer-review prompts", "11 consecutive quarters"])))
    r.test("extract_protected_terms ignores route connector spillover", lambda: assert_not_in("6 because that delivery route", server.extract_protected_terms("Use Route 6 because that delivery route changed.")))
    r.test("extract_protected_terms ignores hyphen-number spillover", lambda: assert_not_in("204 should say why samples", server.extract_protected_terms("PCR-204 should say why samples are excluded.")))
    r.test("extract_protected_terms includes entity refs", lambda: assert_true(all(term in server.extract_protected_terms("Route 6, Module 3, Figure 4, Claim 7, Zone C, and E-2048 remain exact.") for term in ["Route 6", "Module 3", "Figure 4", "Claim 7", "Zone C", "E-2048"])))
    r.test("extract_protected_terms includes URL email issue path", lambda: assert_true(all(term in server.extract_protected_terms("See https://status.example.com/incidents/INC-4421, email ops@example.com, and docs/q3-plan.md.") for term in ["https://status.example.com/incidents/INC-4421", "INC-4421", "ops@example.com", "docs/q3-plan.md"])))
    r.test("extract_protected_terms includes money legal metrics", lambda: assert_true(all(term in server.extract_protected_terms("Section 4.2 requires SOC 2 Type II evidence, RFC-109, p95 latency, July 2026, and $184,500.") for term in ["Section 4.2", "SOC 2 Type II", "RFC-109", "p95", "July 2026", "$184,500"])))
    r.test("extract_protected_terms ignores plain policy phrase", lambda: assert_not_in("policy is", server.extract_protected_terms("The new expense policy is designed to be clear.")))
    r.test("extract_protected_terms includes DOI CVE URI channel", lambda: assert_true(all(term in server.extract_protected_terms("Track CVE-2026-12345, doi 10.1145/3613904.3642200, s3://bucket/key, and #growth-ops.") for term in ["CVE-2026-12345", "10.1145/3613904.3642200", "s3://bucket/key", "#growth-ops"])))
    r.test("quality_issues finds empty output", lambda: assert_in("empty output", server.quality_issues("", sample)))
    r.test("quality_issues finds metadata", lambda: assert_true(any("metadata" in x for x in server.quality_issues("Detection result: pass\nProse", sample))))
    r.test("quality_issues finds paragraph compression", lambda: assert_true(any("paragraph count" in x for x in server.quality_issues("Merged sentence.", sample))))
    r.test("quality_issues finds paragraph split", lambda: assert_true(any("split into" in x for x in server.quality_issues("One\n\nTwo\n\nThree", sample))))
    r.test("quality_issues finds missing protected term", lambda: assert_true(any("protected content" in x for x in server.quality_issues("The version changed.", "API v2.3.1 changed."))))
    r.test("quality_issues finds unchanged output", lambda: assert_true(any("unchanged" in x for x in server.quality_issues(sample * 4, sample * 4))))
    r.test("quality_issues finds too short", lambda: assert_true(any("too short" in x for x in server.quality_issues("Short.", sample * 20))))
    r.test("quality_issues finds too long", lambda: assert_true(any("too long" in x for x in server.quality_issues(sample * 20, sample * 4))))
    r.test("quality_issues finds list format", lambda: assert_true(any("list" in x for x in server.quality_issues("1. Rule\n2. Rule", sample))))
    r.test("quality_issues finds table format", lambda: assert_true(any("table" in x for x in server.quality_issues("|A|B|\n|C|D|", sample))))
    r.test("issue_score scores issues", lambda: assert_true(server.issue_score(["empty output"], "", sample) > 0))

    messages = server.build_llm_messages(server.adapter_by_id("blader_humanizer"), sample, user_note="More natural")
    r.test("build_llm_messages returns system/user", lambda: assert_equal([m["role"] for m in messages], ["system", "user"]))
    r.test("build_llm_messages system is De-AI", lambda: assert_in("De-AI", messages[0]["content"]))
    r.test("build_llm_messages treats repo material as reference", lambda: assert_in("only reference material", messages[0]["content"]))
    r.test("build_llm_messages includes user note", lambda: assert_in("More natural", messages[1]["content"]))
    r.test("build_repair_messages includes issue", lambda: assert_in("paragraph count", server.build_repair_messages(server.adapter_by_id("blader_humanizer"), sample, "bad", ["paragraph count"], "None")[1]["content"]))
    r.test("retry_note merges original request", lambda: assert_in("Original request", server.retry_note("Original request", sample, ["too short"])))

    r.test("run_pipeline empty input errors", lambda: assert_raises(lambda: server.run_pipeline("", ["blader_humanizer"]), server.AppError, 400))
    r.test("run_pipeline empty pipeline errors", lambda: assert_raises(lambda: server.run_pipeline(sample, []), server.AppError, 400))
    r.test("run_pipeline unknown node errors", lambda: assert_raises(lambda: server.run_pipeline(sample, ["__missing__"]), server.AppError, 404))
    r.test("single-node LLM wrapper returns one step", lambda: assert_equal(len(server.run_pipeline(sample, ["blader_humanizer"])["steps"]), 1))
    r.test("default pipeline IDs exist", lambda: assert_true(all(server.adapter_by_id(x) for x in ["blader_humanizer", "stephenturner_skill_deslop"])))

    original_chat = server.nvidia_chat
    try:
        server.nvidia_chat = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("synthetic model failure"))
        with redirect_stderr(io.StringIO()):
            failed_step = server.run_pipeline(sample, ["blader_humanizer"])["steps"][0]
    finally:
        server.nvidia_chat = original_chat
    r.test("failed model step is marked unsuccessful", lambda: assert_true(not failed_step["ok"]))
    r.test("failed model step hides traceback by default", lambda: assert_equal(failed_step["stderr"], ""))

    base, httpd = start_test_server()
    try:
        r.test("HTTP /api/health 200", lambda: assert_equal(request(base + "/api/health")[0], 200))
        r.test("HTTP /api/health ok true", lambda: assert_true(get_json(base + "/api/health")["ok"]))
        r.test("HTTP /api/health reports source cache count", lambda: assert_true(isinstance(get_json(base + "/api/health")["sourceCached"], int)))
        r.test("HTTP /api/adapters 200", lambda: assert_equal(request(base + "/api/adapters")[0], 200))
        r.test("HTTP /api/adapters count matches", lambda: assert_equal(len(get_json(base + "/api/adapters")["adapters"]), len(adapters)))
        r.test("HTTP / returns index", lambda: assert_in('<div id="root"></div>', get_text(base + "/")))
        r.test("HTTP /app.js returns React source", lambda: assert_in("import React", get_text(base + "/app.js")))
        r.test("HTTP /styles.css returns progress styles", lambda: assert_in(".progress-percent", get_text(base + "/styles.css")))
        r.test("HTTP /robots.txt allows home", lambda: assert_in("Allow: /", get_text(base + "/robots.txt")))
        r.test("HTTP /robots.txt disallows API", lambda: assert_in("Disallow: /api/", get_text(base + "/robots.txt")))
        r.test("HTTP /robots.txt advertises llms", lambda: assert_in("LLMs.txt:", get_text(base + "/robots.txt")))
        r.test("HTTP /sitemap.xml returns home", lambda: assert_in("<loc>http://127.0.0.1:", get_text(base + "/sitemap.xml")))
        r.test("HTTP /llms.txt describes local pipeline", lambda: assert_in("local pipeline workbench", get_text(base + "/llms.txt").lower()))
        r.test("HTTP unknown POST returns 404", lambda: assert_equal(post_json(base + "/api/nope", {})[0], 404))
        r.test("HTTP /api/run empty input 400", lambda: assert_equal(post_json(base + "/api/run", {"text": "", "pipeline": ["blader_humanizer"]})[0], 400))
        r.test("HTTP /api/run empty pipeline 400", lambda: assert_equal(post_json(base + "/api/run", {"text": sample, "pipeline": []})[0], 400))
        r.test("HTTP /api/run unknown node 404", lambda: assert_equal(post_json(base + "/api/run", {"text": sample, "pipeline": ["__missing__"]})[0], 404))
        r.test("HTTP /api/run LLM wrapper success", lambda: assert_true(post_json(base + "/api/run", {"text": sample, "pipeline": ["blader_humanizer"], "note": "Preserve paragraphs"})[1]["output"].strip()))
    finally:
        httpd.shutdown()

    r.test("index uses grounded De-AI title", lambda: assert_in("De-AI | Local English Rewrite Pipeline", index))
    r.test("index describes fact preservation", lambda: assert_in("preserving facts, citations", index))
    r.test("index avoids unsupported strongest claim", lambda: assert_not_in("Strongest", index))
    r.test("index identifies local workbench", lambda: assert_in("local workbench", index))
    r.test("index contains structured data", lambda: assert_in('"@type": "SoftwareApplication"', index))
    r.test("index contains OpenGraph title", lambda: assert_in('property="og:title"', index))
    r.test("index contains noscript fallback", lambda: assert_in("<noscript>", index))
    r.test("frontend uses React 18", lambda: assert_in("react@18.3.1", app_js))
    r.test("frontend uses createRoot", lambda: assert_in("createRoot(document.getElementById", app_js))
    r.test("default pipeline includes core node", lambda: assert_in('"blader_humanizer"', app_js))
    r.test("default pipeline keeps only first two nodes", lambda: assert_in('const DEFAULT_PIPELINE = [\n  "blader_humanizer",\n  "stephenturner_skill_deslop",\n];', app_js))
    r.test("workbench grid class exists", lambda: assert_in("workbench-grid", app_js))
    r.test("progress ring uses conic-gradient", lambda: assert_in("conic-gradient", styles))
    r.test("progress number is dark enough", lambda: assert_in("color: #060607", styles))
    r.test("mobile media query exists", lambda: assert_in("@media (max-width: 780px)", styles))
    r.test("button glyph class exists", lambda: assert_in("button-glyph", app_js))
    r.test("node library uses adaptive grid", lambda: assert_in("repeat(auto-fit, minmax(360px, 1fr))", styles))
    r.test("static frontend does not expose NVIDIA key", lambda: assert_not_in("nvapi-", app_js + styles + index))
    r.test("frontend no Chinese brand copy", lambda: assert_not_in("中文去 AI", app_js + index))

    return r.done()


if __name__ == "__main__":
    raise SystemExit(main())
