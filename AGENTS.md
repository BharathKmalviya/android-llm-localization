# AGENTS.md — AI Agent Guide for android-llm-localization

This file tells AI agents (Claude, Cursor, Copilot, etc.) how this project is structured and what steps to follow for common tasks.

---

## Project Overview

`android-localisation` is a zero-dependency Python CLI tool that translates Android `strings.xml` files using LLMs.

**PyPI:** `pip install android-localisation`
**Repo:** https://github.com/BharathKmalviya/android-llm-localization
**CLI entry point:** `android-localise`

---

## Project Structure

```
android-localisation-scripts/
├── android_localisation/          # The Python package
│   ├── __init__.py                # Package version (keep in sync with pyproject.toml)
│   ├── cli.py                     # Unified CLI entry point with subcommands
│   ├── translate.py               # LLM API clients + translation logic
│   ├── fix.py                     # XML escaping fixer
│   ├── verify.py                  # Java format specifier verifier (runs javac)
│   └── java/
│       └── VerifyStrings.java     # Java verifier (bundled as package data)
├── .github/
│   └── workflows/
│       └── publish.yml            # Auto-publishes to PyPI on version tag push
├── pyproject.toml                 # Package metadata and build config
├── CHANGELOG.md                   # Version history (update on every release)
├── MANIFEST.in                    # Ensures java/ is included in source distributions
├── LICENSE                        # MIT
└── README.md                      # User-facing documentation
```

---

## Key Rules

- **Zero external dependencies.** Only Python stdlib (`urllib`, `json`, `re`, `subprocess`, `argparse`, etc.). Never add third-party imports.
- **Version must be in sync** in two places: `pyproject.toml` and `android_localisation/__init__.py`.
- **Never duplicate logic.** All script logic lives in `android_localisation/`. There are no root-level standalone scripts.
- **CLI subcommands** (`translate`, `fix`, `verify`, `models`) are defined in `cli.py` and delegate to their respective modules.
- **Module functions accept a pre-parsed `args` Namespace** (from `cli.py`) or a raw `argv` list (for direct invocation). Always handle both:
  ```python
  def main(args=None):
      if args is None or isinstance(args, list):
          args = _parse_args(args)
  ```
- **PROVIDER_MODELS** in `translate.py` is the single source of truth for available models and fallback order.

---

## CLI Commands

```bash
android-localise translate --api-key KEY          # Translate strings.xml
android-localise fix                              # Fix XML escaping issues
android-localise verify                           # Verify format specifiers (needs javac)
android-localise models                           # List available models per provider
android-localise --version                        # Show version
```

---

## Supported Providers

| Provider | Default Model | Fallbacks | API Key Env Var |
|---|---|---|---|
| `gemini` | `gemini-2.5-flash` | `gemini-2.0-flash`, `gemini-1.5-flash`, `gemini-1.5-pro` | `GEMINI_API_KEY` |
| `openai` | `gpt-4o-mini` | `gpt-4o`, `gpt-3.5-turbo` | `OPENAI_API_KEY` |
| `anthropic` | `claude-3-5-haiku-latest` | `claude-3-5-sonnet-latest`, `claude-3-opus-latest` | `ANTHROPIC_API_KEY` |
| `custom` | *(must specify --model)* | none | `OPENAI_API_KEY` or none |

To add a new provider or update model lists, edit `PROVIDER_MODELS` in `translate.py` and add the provider choice to `cli.py` and `_parse_args()` in `translate.py`.

---

## How to Add a New Feature

1. Add logic to the relevant module (`translate.py`, `fix.py`, `verify.py`)
2. If it needs a new CLI argument, add it in both `cli.py` (subparser) and `_parse_args()` in the module
3. Update `README.md` if it's user-facing
4. Update `CHANGELOG.md` under an `[Unreleased]` section

---

## How to Release a New Version

1. Make and commit all changes
2. Bump version in **both**:
   - `pyproject.toml` → `version = "x.x.x"`
   - `android_localisation/__init__.py` → `__version__ = "x.x.x"`
3. Update `CHANGELOG.md` — move items from `[Unreleased]` to a new `[x.x.x] - YYYY-MM-DD` section
4. Commit:
   ```bash
   git add .
   git commit -m "Release vX.X.X"
   ```
5. Tag and push:
   ```bash
   git tag vX.X.X
   git push && git push --tags
   ```
6. GitHub Actions (`publish.yml`) automatically builds and publishes to PyPI.

---

## Testing Locally

```bash
pip install -e .                          # install in editable mode
android-localise --version               # verify CLI works

# Test against a dummy res/ folder
mkdir -p test_res/values test_res/values-hi test_res/values-es
# add a strings.xml to test_res/values/
android-localise translate --api-key KEY --res-dir test_res
android-localise fix --res-dir test_res
android-localise verify --res-dir test_res
```

---

## What NOT to Do

- Do not add `pip install` dependencies — stdlib only
- Do not create root-level standalone scripts (everything goes in `android_localisation/`)
- Do not change the version in only one place — always update both `pyproject.toml` and `__init__.py`
- Do not push directly to PyPI with `twine` manually after the GitHub Actions workflow is set up — use tags instead
- Do not store API keys in code or config files
