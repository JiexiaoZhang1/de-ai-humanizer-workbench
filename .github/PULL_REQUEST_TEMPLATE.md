## Summary

Describe what changed and why.

## User impact

Explain the visible or behavioral effect.

## Validation

- [ ] `python3 -m py_compile server.py tools/*.py`
- [ ] `python3 tools/qa_50_tests.py`
- [ ] `python3 tools/generate_sources_doc.py` leaves no diff
- [ ] `python3 tools/check_publication.py`
- [ ] Desktop and mobile UI checked when applicable

## Publication safety

- [ ] No API key, credential, private input text, or authorization header is included
- [ ] No file from `repos/english-humanizers/` is included
- [ ] Third-party references are linked and attributed
- [ ] Documentation and screenshots match current behavior
