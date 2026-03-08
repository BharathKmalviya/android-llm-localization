# Android LLM Localization

[![PyPI version](https://img.shields.io/pypi/v/android-localisation.svg)](https://pypi.org/project/android-localisation/)
[![Python 3.8+](https://img.shields.io/pypi/pyversions/android-localisation.svg)](https://pypi.org/project/android-localisation/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/BharathKmalviya/android-llm-localization/blob/master/LICENSE)

A zero-dependency Python tool to translate, fix, and verify Android `strings.xml` resources using Large Language Models (LLMs) — Gemini, OpenAI, Anthropic (Claude), or any local model via Ollama.

## Why this exists?

Localizing Android apps usually involves paying for services, exporting CSVs, or manually using Google Translate. This tool translates `strings.xml` directly in your project using modern LLMs, giving significantly better context-aware translations.

**Zero dependencies** — no `pip install` of extra libraries required. Uses only Python's built-in networking.

---

## Installation

```bash
pip install android-localisation
```

To update to the latest version:

```bash
pip install --upgrade android-localisation
```

---

## Quick Start

```bash
# 1. Translate (Gemini free tier recommended)
android-localise translate --api-key YOUR_GEMINI_API_KEY

# 2. Fix any XML escaping issues introduced by the LLM
android-localise fix

# 3. Verify no format specifiers were corrupted (requires Java JDK)
android-localise verify
```

---

## The Three Commands

### 1. `translate` — Translate strings into all locale directories

Reads `app/src/main/res/values/strings.xml` (English) and writes translated `strings.xml` into every `values-*` directory it finds.

**Prerequisites:**
- Create empty `values-<lang>/` folders for each language you want (e.g. `values-hi/`, `values-es/`)
- Get an API key — **[Google Gemini AI Studio](https://aistudio.google.com/) has a generous free tier**

```bash
# Basic — Gemini (default)
android-localise translate --api-key YOUR_GEMINI_API_KEY

# With app context for better translations
android-localise translate --api-key YOUR_KEY --app-context "a fitness tracking app"

# OpenAI
android-localise translate --api-key YOUR_KEY --provider openai --model gpt-4o

# Anthropic (Claude)
android-localise translate --api-key YOUR_KEY --provider anthropic

# Local model via Ollama
android-localise translate --provider custom --base-url http://localhost:11434/v1/chat/completions --model llama3
```

**Full arguments:**

| Argument | Description | Default |
|---|---|---|
| `--api-key` | API key (or set `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` env vars) | *None* |
| `--provider` | AI provider: `gemini`, `openai`, `anthropic`, `custom` | `gemini` |
| `--model` | Model name (e.g. `gemini-2.5-flash`, `gpt-4o`, `claude-3-5-sonnet-latest`) | provider default |
| `--app-context` | Short description of your app to improve translation quality | *None* |
| `--res-dir` | Path to the Android `res/` directory | `app/src/main/res` |
| `--base-url` | Base URL for custom OpenAI-compatible endpoints | *None* |
| `--sleep` | Seconds between requests to avoid rate limits | `5.0` |

---

### 2. `fix` — Fix XML escaping issues

LLMs occasionally introduce malformed characters — curly apostrophes (`'`), unescaped quotes, or broken `%` symbols. This command cleans them all up.

```bash
android-localise fix
# or with a custom res dir:
android-localise fix --res-dir path/to/res
```

---

### 3. `verify` — Catch format specifier crashes before they happen

LLMs can corrupt Android format specifiers like `%1$s` or `%d`, which causes `UnknownFormatConversionException` crashes at runtime. This command compiles a Java verifier and dry-runs `String.format()` against every translated string.

```bash
android-localise verify
```

*Requires `javac` in your system PATH. Run from Android Studio's terminal if needed.*

---

## Recommended Workflow

1. Update your English `strings.xml`
2. Create empty `values-<lang>/` folders for the languages you want
3. `android-localise translate --api-key YOUR_KEY`
4. `android-localise fix`
5. `android-localise verify`
6. Build and test your app

---

## Supported Providers

| Provider | Default Model | API Key Env Var |
|---|---|---|
| `gemini` (default) | `gemini-2.5-flash` | `GEMINI_API_KEY` |
| `openai` | `gpt-4o-mini` | `OPENAI_API_KEY` |
| `anthropic` | `claude-3-5-sonnet-latest` | `ANTHROPIC_API_KEY` |
| `custom` | *(must specify)* | `OPENAI_API_KEY` or none |

---

---

## Contributing

Issues and PRs welcome at [github.com/BharathKmalviya/android-llm-localization](https://github.com/BharathKmalviya/android-llm-localization).

---

*Created to make Android localization accessible, free, and completely automated.*
