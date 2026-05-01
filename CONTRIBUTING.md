# Contributing

This project is in MVP prototype mode. Contributions should preserve provenance, reproducibility, and research-only framing.

Before opening a change:

```bash
ruff check .
pytest
```

Schema changes should add or update tests in `tests/`. Data-source additions must include source, license, provenance, and redistribution notes.
