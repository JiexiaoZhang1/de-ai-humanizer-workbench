# API Reference

Base URL for the default local server: `http://127.0.0.1:8765`

All API responses use UTF-8 JSON. The development server does not implement authentication, so it should remain bound to a trusted local interface.

## Common headers

Responses include:

```http
Content-Type: application/json; charset=utf-8
X-Content-Type-Options: nosniff
Referrer-Policy: no-referrer
X-Frame-Options: DENY
```

Requests with a JSON body should include:

```http
Content-Type: application/json
```

## `GET /api/health`

Reports whether the server is running and whether a credential is configured. It never returns the credential itself.

Example:

```bash
curl -sS http://127.0.0.1:8765/api/health
```

Example response:

```json
{
  "ok": true,
  "adapters": 88,
  "sourceCached": 0,
  "hasKey": true,
  "demoMode": false
}
```

| Field | Type | Meaning |
| --- | --- | --- |
| `ok` | boolean | HTTP server and handler are available |
| `adapters` | integer | Number of loaded node definitions |
| `sourceCached` | integer | Number of adapters whose optional upstream directory exists locally |
| `hasKey` | boolean | A non-empty server-side NVIDIA key is configured |
| `demoMode` | boolean | Requests use the deterministic local demo rewrite instead of a model endpoint |

`ok: true` does not test a real model request. Use a small `/api/run` request or `--self-test-llm` when model connectivity must be verified. Demo mode is started with `python3 server.py --demo`; its output is intentionally marked as local demonstration behavior.

## `GET /api/adapters`

Returns the node library used by the interface.

Example:

```bash
curl -sS http://127.0.0.1:8765/api/adapters
```

Response shape:

```json
{
  "adapters": [
    {
      "id": "blader_humanizer",
      "name": "Humanizer",
      "repo": "blader/humanizer",
      "path": "repos/english-humanizers/blader_humanizer",
      "kind": "llm_prompt",
      "category": "Skill / Prompt",
      "description": "...",
      "integration_mode": "native_skill",
      "prompt_files": ["SKILL.md", "README.md"],
      "timeout": 90,
      "prompt_profile": "skill-prompt.md",
      "source_cached": false,
      "available": true
    }
  ]
}
```

The `path` and `prompt_files` fields identify optional local reference material. They are not browser-accessible file endpoints.

## `POST /api/run`

Executes node IDs from top to bottom. Each accepted node receives the previous node's cleaned output.

### Request body

```json
{
  "text": "Source English prose.",
  "pipeline": ["blader_humanizer", "stephenturner_skill_deslop"],
  "note": "Keep the tone direct and preserve technical terms."
}
```

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `text` | string | yes | Must contain non-whitespace text |
| `pipeline` | array of strings | yes | Must contain at least one known adapter ID |
| `note` | string | no | Additional instruction applied to every node |

The complete request body is limited to 2,000,000 bytes by the application. A reverse proxy should enforce a smaller deployment-specific limit.

### Example request

```bash
curl -sS http://127.0.0.1:8765/api/run \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "The release remains scheduled for July 2026. API v2.3.1 must keep DB_SCHEMA_VERSION=20260412 unchanged.",
    "pipeline": ["blader_humanizer"],
    "note": "Use direct professional English."
  }'
```

### Successful response

```json
{
  "input": "The release remains scheduled for July 2026...",
  "output": "The final cleaned rewrite...",
  "steps": [
    {
      "id": "blader_humanizer",
      "name": "Humanizer",
      "repo": "blader/humanizer",
      "kind": "llm_prompt",
      "input": "The release remains scheduled for July 2026...",
      "output": "The cleaned node output...",
      "elapsed_ms": 1834,
      "ok": true,
      "note": "NVIDIA LLM rewrite",
      "stderr": "",
      "warnings": []
    }
  ]
}
```

| Step field | Type | Meaning |
| --- | --- | --- |
| `id` | string | Adapter ID used in the request |
| `name` | string | Display name |
| `repo` | string | Referenced upstream project |
| `kind` | string | Execution strategy |
| `input` | string | Text entering this node |
| `output` | string | Cleaned text leaving this node |
| `elapsed_ms` | integer | End-to-end node time, including recovery calls |
| `ok` | boolean | Whether the node completed without an exception |
| `note` | string | Short execution note or expected error message |
| `stderr` | string | Local command diagnostics for command-style nodes; normally empty for prompt nodes |
| `warnings` | array of strings | Cleanup, retry, repair, fallback, and residual quality notes |

A failed node catches its exception, marks `ok: false`, and returns its input as its output. The pipeline then continues. This behavior preserves text but means callers should inspect every step, not only the final HTTP status.

## Error responses

### `400 Bad Request`

Empty input:

```json
{"error": "Input text cannot be empty."}
```

Empty pipeline:

```json
{"error": "Select at least one node."}
```

Malformed JSON can result in a generic internal error in the current demo implementation. A production API should return a dedicated `400` error for JSON decoding failures.

### `404 Not Found`

Unknown node:

```json
{"error": "Unknown node: missing_id"}
```

Unknown API path:

```json
{"error": "Unknown API: /api/unknown"}
```

### `413 Request Entity Too Large`

```json
{"error": "Request body is too large."}
```

### `500 Internal Server Error`

Missing model credential is currently reported as a node-level failure inside a successful pipeline response because `run_adapter()` catches the exception. Unexpected handler failures return:

```json
{"error": "Internal server error."}
```

When local `debug` is enabled, an unexpected handler response may also contain a traceback. Never enable debug on an exposed service.

### `502 Bad Gateway`

The model client raises `502`-class `AppError` values for NVIDIA HTTP errors, connection failures, or an unexpected response shape. Within a normal pipeline, those are caught into the affected step as described above.

## Non-API routes

| Route | Content |
| --- | --- |
| `/` | Workbench HTML |
| `/app.js` | React application source |
| `/styles.css` | Application styles |
| `/robots.txt` | Crawler rules; `/api/` is disallowed |
| `/sitemap.xml` | Single-page sitemap generated from the request host |
| `/llms.txt` | Plain-language project summary |

## Client integration notes

- Preserve node order exactly as sent.
- Treat `steps[].ok` and `steps[].warnings` as part of the contract.
- Do not infer a successful model call from HTTP `200` alone.
- Avoid logging full requests and responses when text may contain confidential information.
- Never put the NVIDIA key in browser JavaScript or request payloads.
- Apply client and proxy timeouts that allow for retries; one node can make several sequential model calls.
- Keep pipelines short for interactive use. More nodes increase latency, cost, and semantic drift.
