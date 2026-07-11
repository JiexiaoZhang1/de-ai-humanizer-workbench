# Contributing

Contributions are welcome as focused issues or pull requests. Keep changes small enough to review and preserve the project's local-first, explicit-pipeline design.

## Development setup

```bash
git clone https://github.com/JiexiaoZhang1/de-ai-humanizer-workbench.git
cd de-ai-humanizer-workbench
python3 tools/qa_50_tests.py
python3 server.py --host 127.0.0.1 --port 8765
```

No Python dependency installation is required for the current backend. The browser needs access to `esm.sh` to load React.

## Before opening a pull request

Run:

```bash
python3 -m py_compile server.py tools/*.py
python3 tools/qa_50_tests.py
python3 tools/generate_sources_doc.py
python3 tools/check_publication.py
```

Confirm that generated source documentation has no unintended changes and that no local credentials, downloaded repositories, reports, logs, or browser artifacts are staged.

## Adding or changing an adapter

1. Use a stable lowercase `id` with underscores.
2. Keep `repo` in GitHub `owner/name` form.
3. Put local caches under `repos/english-humanizers/` only.
4. Choose the narrowest existing category and integration mode.
5. Write a factual description without detector guarantees or unsupported quality claims.
6. Keep `prompt_files` to a short allow-list of text files needed for editorial reference.
7. Do not add commands that execute an upstream repository.
8. Regenerate `docs/SOURCES.md`.
9. Add or update tests when the adapter introduces a new behavior or protected token format.

## Adding a built-in profile

Built-in profiles are project-owned text under `prompts/`. A profile should describe editing behavior, preserve source meaning, and avoid copying distinctive language from an upstream project.

To add one:

1. Create a concise Markdown file in `prompts/`.
2. Add its category mapping to `CATEGORY_PROFILES` in `server.py`.
3. Add at least one adapter in that category or explain the planned use.
4. Extend tests to confirm the profile is loadable in a clean clone.

## Code style

- Support Python 3.10 and newer.
- Prefer the standard library unless a dependency removes substantial complexity.
- Keep browser code build-free unless a broader frontend migration is intentionally proposed.
- Keep comments focused on non-obvious constraints.
- Preserve public API field names unless a compatibility change is documented.
- Never return credentials or full unexpected tracebacks to the browser by default.

## Test expectations

Changes to cleanup, protected terms, quality scoring, retry behavior, or API contracts should include focused regression tests. Tests must not require a real API key unless they are explicitly marked as live checks and excluded from the default CI path.

For frontend changes, verify at minimum:

- Desktop layout near `1440 x 1000`.
- Mobile layout near `390 x 844`.
- Node search, category filters, add/remove controls, move controls, and run button.
- No horizontal overflow or incoherent overlap.
- No credential values in screenshots or browser output.

## Third-party and licensing rules

- Do not commit anything under `repos/english-humanizers/`.
- Do not paste upstream prompt files into built-in profiles.
- Link and attribute upstream work in `data/adapters.json` and `docs/SOURCES.md`.
- Preserve upstream licenses in local caches; do not imply that this repository relicenses them.
- Do not add a project-level open-source license without the repository owner's explicit decision.

## Pull request checklist

- The change has one clear purpose.
- Offline QA passes.
- Publication guard passes.
- Documentation matches behavior.
- No real model credential is present.
- No third-party repository mirror is present.
- User-visible claims are factual and do not promise detector outcomes.
- Security and privacy impact has been considered.
