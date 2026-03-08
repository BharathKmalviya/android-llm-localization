# android-llm-localization

[![PyPI version](https://img.shields.io/pypi/v/android-localisation.svg)](https://pypi.org/project/android-localisation/)
[![Python 3.8+](https://img.shields.io/pypi/pyversions/android-localisation.svg)](https://pypi.org/project/android-localisation/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Translate your Android `strings.xml` into any language using LLMs — Gemini, OpenAI, Anthropic, or a local model. No paid localization service, no CSV exports, no manual copy-paste.

Works entirely from the command line, has zero external dependencies, and fits into any existing Android project without changes to your build setup.

---

## What it does

Most localization workflows are painful. You export strings, paste them into Google Translate or some dashboard, clean up the output, re-import, and repeat for every language. This tool skips all of that.

Point it at your `res/` directory, give it an API key, and it writes translated `strings.xml` files directly into your locale folders. It also ships two safety tools — one that fixes common LLM formatting mistakes, and one that verifies format specifiers like `%1$s` won't crash your app at runtime.

---

## Installation

```bash
pip install android-localisation
```

---

## Setup

Create locale folders for the languages you want. The tool looks for any `values-*` directory and treats it as a translation target.

```
app/src/main/res/
├── values/               ← your English source
│   └── strings.xml
├── values-hi/            ← Hindi (create empty)
├── values-es/            ← Spanish (create empty)
└── values-fr/            ← French (create empty)
```

Get an API key. [Google Gemini AI Studio](https://aistudio.google.com/) has a free tier that works well for most apps.

---

## Usage

### Translate

```bash
android-localise translate --api-key YOUR_KEY
```

Reads `values/strings.xml` and writes translated files into every `values-*` folder it finds.

Add `--app-context` to give the model a hint about what your app does — this noticeably improves translation quality for domain-specific terms:

```bash
android-localise translate --api-key YOUR_KEY --app-context "a personal finance and budgeting app"
```

**All options:**

| Flag | Description | Default |
|---|---|---|
| `--api-key` | API key. Can also be set via env var | — |
| `--provider` | `gemini`, `openai`, `anthropic`, or `custom` | `gemini` |
| `--model` | Any model name the provider supports | provider default |
| `--app-context` | One-line description of your app | — |
| `--res-dir` | Path to your `res/` directory | `app/src/main/res` |
| `--base-url` | Endpoint URL for custom/local providers | — |
| `--sleep` | Delay between requests in seconds | `5.0` |

### Fix

```bash
android-localise fix
```

LLMs occasionally produce curly apostrophes, unescaped quotes, or malformed `%` signs that cause AAPT2 build failures. This command scans all translated files and corrects them.

### Verify

```bash
android-localise verify
```

Compiles a Java verifier and dry-runs `String.format()` against every translated string. Catches corrupted format specifiers (`%1$s` → `%s`, etc.) that would throw `UnknownFormatConversionException` at runtime. Requires `javac` in your PATH — run from Android Studio's terminal if needed.

### List available models

```bash
android-localise models
```

---

## Providers

| Provider | Default model | Env var |
|---|---|---|
| `gemini` _(default)_ | `gemini-2.5-flash` | `GEMINI_API_KEY` |
| `openai` | `gpt-4o-mini` | `OPENAI_API_KEY` |
| `anthropic` | `claude-3-5-haiku-latest` | `ANTHROPIC_API_KEY` |
| `custom` | specify with `--model` | — |

Each provider has a fallback chain — if the default model is unavailable, the next one is tried automatically. Use `--model` to pin a specific model and skip fallbacks entirely.

**Using a local model (Ollama, LM Studio):**

```bash
android-localise translate \
  --provider custom \
  --base-url http://localhost:11434/v1/chat/completions \
  --model llama3
```

No API key required for local providers.

---

## Recommended workflow

```bash
# 1. Update your English strings.xml
# 2. Create empty values-<lang>/ folders for new languages

android-localise translate --api-key YOUR_KEY --app-context "your app description"
android-localise fix
android-localise verify

# 3. Build your app
```

Run `fix` before `verify` — the fixer corrects formatting issues that the verifier would otherwise flag.

---

## Environment variables

Instead of passing `--api-key` every time, export the key for your provider:

```bash
export GEMINI_API_KEY=your_key       # or set in your shell profile
android-localise translate
```

| Variable | Provider |
|---|---|
| `GEMINI_API_KEY` | Gemini |
| `OPENAI_API_KEY` | OpenAI / custom |
| `ANTHROPIC_API_KEY` | Anthropic |

---

## Contributing

Bug reports and pull requests are welcome. Open an issue first for anything beyond small fixes — it helps avoid duplicate work.

To run locally:

```bash
git clone https://github.com/BharathKmalviya/android-llm-localization
cd android-llm-localization
pip install -e .
```

Releases are automated. Bumping the version in `pyproject.toml` and `__init__.py`, updating `CHANGELOG.md`, and pushing to `master` triggers a build and publish to PyPI via GitHub Actions.

---

## License

[MIT](LICENSE)
