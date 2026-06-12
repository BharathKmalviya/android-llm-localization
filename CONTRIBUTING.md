# Contributing to android-localisation

Thank you for considering a contribution. This project is intentionally small — zero third-party dependencies, a flat Python package, and a single CLI entry point — so changes stay easy to review.

---

## Getting started

```bash
git clone https://github.com/BharathKmalviya/android-llm-localization
cd android-llm-localization
git checkout dev
pip install -e .
```

Verify the CLI is wired up:

```bash
android-localise --version
android-localise --help
```

Use the local `test/` fixture (gitignored) for manual runs — see [AGENTS.md](AGENTS.md) for examples. Never commit the `test/` folder.

---

## Branch workflow

| Branch | Purpose |
|---|---|
| `dev` | All day-to-day changes — features, fixes, docs |
| `master` | Production only — merged via PR when releasing |

**Always open PRs against `dev`**, not `master`, unless you are performing a release merge.

```bash
git checkout dev
# make your changes
git add .
git commit -m "Add feature X — short reason"
git push origin dev
```

---

## What to change where

| Change type | Files |
|---|---|
| New CLI flag | `android_localisation/cli.py` + relevant module `_parse_args()` |
| Translation / LLM logic | `android_localisation/translate.py` |
| XML escaping fixes | `android_localisation/fix.py` |
| Format verifier | `android_localisation/verify.py`, `android_localisation/java/VerifyStrings.java` |
| User docs | `README.md` |
| Agent / maintainer docs | `AGENTS.md` |
| Release notes | `CHANGELOG.md` |

---

## Code rules

- **Stdlib only** — never add third-party `pip` dependencies
- **No root-level scripts** — all logic lives in `android_localisation/`
- **Version sync** — `pyproject.toml` and `android_localisation/__init__.py` must always match
- **Module `main()`** must accept both a pre-parsed `Namespace` and a raw argv list

---

## Documentation requirements

**Code changes** that affect user-facing behaviour:

1. Update `README.md`
2. Add an entry to `CHANGELOG.md`
3. Bump version in `pyproject.toml` and `android_localisation/__init__.py`

**Docs-only changes** (README, CONTRIBUTING, etc.): no version bump needed.

**New CLI flags**: add to the flags table in `README.md` and the translate flags table in `AGENTS.md`.

---

## Commit messages

Format: `<verb> <what> — <why if not obvious>`

Examples:

- `Add --languages flag — auto-create locale folders`
- `Fix % escaping in fix.py — was corrupting non-standard specifiers`
- `Release v1.0.5 — document formatted=false handling`

---

## Releases

Releases are automated — never publish to PyPI manually.

1. Bump version in `pyproject.toml` and `android_localisation/__init__.py`
2. Update `CHANGELOG.md` with the version and date
3. Update `README.md` if behaviour changed
4. Commit on `dev` and push
5. Open a PR from `dev` → `master`
6. After merge, GitHub Actions tags, builds, publishes to PyPI, and creates a GitHub Release

---

## Pull request checklist

- [ ] Changes are focused — one logical change per PR when possible
- [ ] `README.md` updated if user-facing behaviour changed
- [ ] `CHANGELOG.md` updated for code changes
- [ ] Version bumped in both `pyproject.toml` and `__init__.py` for code changes
- [ ] No API keys or secrets committed
- [ ] No third-party dependencies added
- [ ] Manually tested against `test/res` fixture (if code changed)

---

## Ideas for contributors

- Smarter `values-*` folder detection (skip `night`, `sw600dp`, `v21`, etc.)
- iOS `Localizable.strings` / `.xcstrings` support (see README roadmap)
- Unit tests for `fix.py` and format-specifier edge cases
- Better handling of `plurals.xml` and string arrays

Open an issue before starting large features so we can align on approach.
