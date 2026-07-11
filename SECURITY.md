# Security Policy

## Scope

Security fixes are maintained on the latest `main` branch. This repository is a local demonstration application, not a hardened multi-user service.

## Reporting a vulnerability

Open a GitHub issue only when the report can be shared publicly without credentials, private text, personal data, or exploitable production details. For a sensitive report, contact the repository owner through a private channel listed on their GitHub profile before publishing details.

Do not include any of the following in an issue, discussion, screenshot, log, or pull request:

- API keys or authorization headers.
- Contents of `config.local.json` or `.env` files.
- Private documents submitted for rewriting.
- Full model request or response bodies containing confidential text.
- Tokens copied from a terminal, browser storage, or Git credential helper.

## Credential handling

Use `NVIDIA_API_KEY` when possible. `config.local.json` is supported for local convenience and is ignored by Git. `config.example.json` must always keep an empty key.

Before every public push, run:

```bash
python3 tools/check_publication.py
```

If a credential is ever committed, removing it from the latest file is not enough. Revoke or rotate the credential immediately, then clean Git history before sharing the repository again.

## Data flow and privacy

During a real rewrite, the source text, user note, node metadata, built-in profile, and any selected optional source material are sent to the configured NVIDIA endpoint. Review the provider's data-handling terms before processing confidential, regulated, or personal information. `--demo` mode performs its deterministic example rewrite locally and does not send text to the model endpoint.

The application does not maintain a server-side document database. Input and output remain in browser component state for the page session, but terminal logs and external infrastructure may still record metadata. Do not assume that local UI state means the entire processing path is offline.

## Third-party source material

`tools/fetch_sources.py` shallow-clones repositories but does not install dependencies or run their code. The server reads allow-listed text files as prompt reference material. Those files are untrusted input and can contain prompt-injection instructions.

The shared system prompt instructs the model to ignore repository text that requests tools, secrets, installation, browsing, or instruction overrides. This is a risk reduction, not a formal sandbox. Cache only reviewed sources, keep file allow-lists narrow, and remove a cache if its contents are questionable.

## Deployment warning

The default server has no user authentication, authorization, quota enforcement, CSRF protection, or production-grade rate limiting. Keep it bound to `127.0.0.1` for local use.

Before any shared deployment, add at minimum:

- A production HTTP server and reverse proxy.
- TLS, authentication, and per-user authorization.
- Request-size, pipeline-length, timeout, and rate limits.
- Managed secret storage.
- Redacted structured logging and an explicit retention policy.
- Origin and CSRF controls appropriate to the client architecture.
- Dependency pinning or self-hosted frontend assets.
- Cost monitoring and abuse controls for model calls.
- A review of all enabled source material and licenses.

## Response headers

The local server sets `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, and `X-Frame-Options: DENY`. These headers are useful defaults but do not turn the development server into a secure public service.
