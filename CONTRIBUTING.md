# Contributing

Thanks for improving `ci-fix-brief`.

## Local Setup

```bash
python -m pip install .
python -m unittest discover -s tests
```

## Good Contributions

- Add small log fixtures for real CI failure formats.
- Improve detection rules with deterministic tests.
- Tighten docs when a command or limitation is unclear.
- Keep runtime dependencies at zero unless the benefit is obvious.

## Pull Request Checklist

- Tests pass with `python -m unittest discover -s tests`.
- New heuristics include fixture coverage.
- Output stays deterministic.
- Examples do not contain real secrets or private project data.

## Project Direction

This project should stay small: local log in, compact repair brief out. Features that require hosted services, accounts, or background state are likely out of scope.
