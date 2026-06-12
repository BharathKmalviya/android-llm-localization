# AGENTS.md — AI Agent Guide for android-llm-localization

This file is the single source of truth for any AI agent (Claude, Cursor, Copilot, etc.) working on this repo. Read it fully before making any changes.

---

## Project overview

`android-localisation` is a zero-dependency Python CLI tool that translates Android `strings.xml` files using LLMs (Gemini, OpenAI, Anthropic, Ollama).

- **PyPI:** `pip install android-localisation`
- **Repo:** https://github.com/BharathKmalviya/android-llm-localization
- **CLI entry point:** `android-localise`
- **Language:** Python 3.8+, stdlib only — no third-party dependencies ever

---

## Project structure

```
android-localisation-scripts/
├── android_localisation/          # The installable Python package
│   ├── __init__.py                # Package version — must match pyproject.toml
│   ├── cli.py                     # Unified CLI entry point, defines all subcommands
│   ├── translate.py               # LLM API clients, translation logic, PROVIDER_MODELS
│   ├── fix.py                     # XML escaping fixer
│   ├── verify.py                  # Java format specifier verifier (spawns javac)
│   └── java/
│       └── VerifyStrings.java     # Bundled Java verifier (package data)
├── .github/
│   └── workflows/
│       └── publish.yml            # Auto-publishes to PyPI when version changes on master
├── test/                          # Local test fixture — gitignored, never committed
│   └── res/
│       ├── values/strings.xml     # English source for local testing
│       └── values-*/              # Empty locale folders for testing
├── pyproject.toml                 # Package metadata, keywords, build config
├── CHANGELOG.md                   # Version history — updated on every release
├── CONTRIBUTING.md                # Contributor guide (branch workflow, PR checklist)
├── SECURITY.md                    # Vulnerability reporting policy
├── MANIFEST.in                    # Ensures java/ ships in source distributions
├── LICENSE                        # MIT
└── README.md                      # User-facing documentation — always kept in sync
```

---

## Dev environment

```bash
# Install in editable mode (changes reflect immediately, no reinstall needed)
pip install -e .

# Verify the CLI is wired up
android-localise --version
android-localise --help

# Run against the local test fixture
android-localise translate --api-key YOUR_KEY --res-dir test/res --app-context "a test app"
android-localise fix --res-dir test/res
android-localise verify --res-dir test/res
```

The `test/` folder is gitignored — use it freely for local runs. Never commit it.

To jump straight to a specific module, files are flat inside `android_localisation/` — no nested packages to navigate.

---

## CLI commands reference

```bash
android-localise translate --api-key KEY              # translate strings.xml into all locale dirs
android-localise translate --languages hi,es,fr --api-key KEY  # auto-create folders and translate
android-localise fix                                  # fix XML escaping issues in translated files
android-localise verify                               # verify format specifiers won't crash app
android-localise models                               # list all models and fallbacks per provider
android-localise models --provider openai             # filter by provider
android-localise --version                            # show installed version
```

**All `translate` flags:**

| Flag | Description | Default |
|---|---|---|
| `--api-key` | API key (or set via env var) | — |
| `--provider` | `gemini` `openai` `anthropic` `custom` | `gemini` |
| `--model` | Any model name — pins it, disables fallbacks | provider default |
| `--languages` | Comma-separated codes, e.g. `hi,es,fr` — auto-creates folders | — |
| `--app-context` | One-line app description for better translations | — |
| `--res-dir` | Path to `res/` directory | `app/src/main/res` |
| `--base-url` | Endpoint URL for custom/local providers | — |
| `--sleep` | Seconds between API requests | `5.0` |

**Other subcommand flags:**

| Command | Flag | Default |
|---|---|---|
| `fix` | `--res-dir` | `app/src/main/res` |
| `verify` | `--res-dir` | `app/src/main/res` |
| `models` | `--provider` | all providers |

---

## Providers and models

`PROVIDER_MODELS` in `translate.py` is the single source of truth. First entry = default, rest = automatic fallbacks (only used when `--model` is not set).

| Provider | Default | Fallbacks | Env var |
|---|---|---|---|
| `gemini` | `gemini-2.5-flash` | `gemini-2.0-flash` → `gemini-1.5-flash` → `gemini-1.5-pro` | `GEMINI_API_KEY` |
| `openai` | `gpt-4o-mini` | `gpt-4o` → `gpt-3.5-turbo` | `OPENAI_API_KEY` |
| `anthropic` | `claude-3-5-haiku-latest` | `claude-3-5-sonnet-latest` → `claude-3-opus-latest` | `ANTHROPIC_API_KEY` |
| `custom` | must set `--model` | none | `OPENAI_API_KEY` or none |
| any | — | — | `API_KEY` (fallback if provider-specific var unset) |

To add a provider: add it to `PROVIDER_MODELS`, add it to `choices` in `_parse_args()` in `translate.py`, and add it to the subparser in `cli.py`.

---

## Agent behaviour — non-negotiable defaults

These apply automatically on every task. The user should never have to ask for any of these.

**After any code change:**
- Update `README.md` to reflect the change — new flags, changed defaults, new behaviour, removed features
- Update `CHANGELOG.md` with a new version entry describing what changed and why
- Bump version in both `pyproject.toml` and `android_localisation/__init__.py`
- Commit and push — the pipeline publishes to PyPI automatically

**After any README or docs change only (no code changed):**
- Commit and push — no version bump needed

**After adding a new CLI flag:**
- Add it to the flags table in `README.md`
- Add it to the "All `translate` flags" table in `AGENTS.md` if it's a translate flag
- Document any new default behaviour in the "What happens when you run translate" section in README

**After any release:**
- Verify GitHub Actions ran successfully at https://github.com/BharathKmalviya/android-llm-localization/actions
- Confirm the new version appears on PyPI

**General:**
- Always work on the `dev` branch — never commit directly to `master`
- Never push unless the user explicitly says to push
- Never leave the repo in a state where README, CHANGELOG, and code are out of sync
- Always commit changes locally after completing a task — push only when asked
- If something breaks, fix it in the same session before stopping

---

## Code rules — read before touching anything

- **Zero external dependencies.** Only Python stdlib. Never add a `pip install` import.
- **No root-level scripts.** All logic lives in `android_localisation/`. There are no standalone `.py` files at the repo root.
- **Module `main()` accepts both a pre-parsed Namespace and a raw argv list.** Always handle both:
  ```python
  def main(args=None):
      if args is None or isinstance(args, list):
          args = _parse_args(args)
  ```
- **New CLI flags go in two places:** the subparser in `cli.py` AND `_parse_args()` in the module file.
- **Version must be in sync** in `pyproject.toml` and `android_localisation/__init__.py`. Changing one without the other will break the build.

---

## Adding a new feature — checklist

1. Add logic to the relevant module (`translate.py`, `fix.py`, `verify.py`)
2. If it adds a CLI flag — update both `cli.py` and `_parse_args()` in the module
3. Update `README.md` — document the new behaviour, flag, or default for users
4. Update `CHANGELOG.md` with a new version entry
5. Bump version in `pyproject.toml` and `__init__.py`
6. Commit and push — GitHub Actions publishes to PyPI automatically

Do not skip any of these steps. README and CHANGELOG are not optional.

---

## Testing instructions

There is no automated test suite yet. Test manually using the local fixture:

```bash
# Quick smoke test — checks CLI is installed and flags work
android-localise --version
android-localise translate --help

# Full translation test against the local fixture
android-localise translate \
  --api-key YOUR_KEY \
  --res-dir test/res \
  --app-context "a general mobile app" \
  --sleep 3

# Fix and verify
android-localise fix --res-dir test/res
android-localise verify --res-dir test/res

# Test --languages flag (auto folder creation)
android-localise translate --api-key YOUR_KEY --res-dir test/res --languages ja,ko
```

Check that:
- Each language folder gets a `strings.xml`
- Format specifiers like `%1$s` and `%1$d` are preserved
- `verify` exits with no errors
- Translations are natural-sounding, not word-for-word

---

## Release instructions

Every script change must be published. The pipeline is fully automated — just push.

1. Make and test your changes
2. Bump version in **both files**:
   - `pyproject.toml` → `version = "x.x.x"`
   - `android_localisation/__init__.py` → `__version__ = "x.x.x"`
3. Add a new entry to `CHANGELOG.md` with the version and date
4. Update `README.md` if any user-facing behaviour changed
5. Commit and push:
   ```bash
   git add .
   git commit -m "Release vX.X.X — short description"
   git push
   ```

GitHub Actions will detect the version bump, auto-tag the commit, build the package, publish to PyPI, and create a GitHub Release with the changelog as release notes. If the version didn't change, it skips silently.

**Never** publish manually with `twine`. **Never** create tags manually. The workflow handles both.

---

## Branching workflow

This repo uses a `dev` → `master` workflow. **Never push directly to `master`.**

| Branch | Purpose |
|---|---|
| `dev` | All day-to-day changes — features, fixes, docs, refactors |
| `master` | Production only — merged into via PR when ready to release |

**Day-to-day (all changes go to `dev`):**
```bash
git checkout dev
# make changes
git add .
git commit -m "your message"
# DO NOT push unless the user says to
```

**When the user says to push:**
```bash
git push origin dev
```

**When the user says to release:**
1. Bump version in `pyproject.toml` and `__init__.py`
2. Update `CHANGELOG.md`
3. Commit on `dev` and push
4. Create a PR from `dev` → `master`:
   ```bash
   gh pr create --base master --head dev --title "Release vX.X.X" --body "See CHANGELOG.md"
   ```
5. Tell the user the PR URL — they review and merge
6. After merge, GitHub Actions auto-publishes to PyPI

**After a release merge, sync `dev` with `master`:**
```bash
git checkout dev
git merge master
git push origin dev
```

---

## PR / commit instructions

- Commit message format: `<verb> <what> — <why if not obvious>`
  - Examples: `Add --languages flag — auto-create locale folders`
  - Examples: `Fix % escaping in fix.py — was corrupting non-standard specifiers`
- For releases: `Release vX.X.X — one-line summary of what changed`
- Always run a local test before pushing a release commit
- Keep commits focused — one logical change per commit
- **Do not push after every small change** — batch related changes and push when the user asks

---

## What NOT to do

- Do not add third-party imports — stdlib only
- Do not create standalone scripts at the repo root
- Do not bump version in only one file — always both
- Do not publish to PyPI manually with `twine` — use the automated pipeline
- Do not commit the `test/` folder — it is gitignored and local only
- Do not store API keys anywhere in the codebase
- Do not skip README or CHANGELOG updates when shipping a change
