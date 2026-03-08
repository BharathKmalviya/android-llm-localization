# android-llm-localization

[![PyPI version](https://img.shields.io/pypi/v/android-localisation.svg)](https://pypi.org/project/android-localisation/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://pypi.org/project/android-localisation/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Translate your Android `strings.xml` into multiple languages using AI — Gemini, OpenAI, Anthropic, or a local model via Ollama. No paid service, no CSV exports, no copy-paste.

---

## The problem

Localizing an Android app the usual way means exporting strings, running them through Google Translate or some dashboard, cleaning up the output, and re-importing — for every language, every update. It's slow, error-prone, and the translations often feel robotic.

This tool does it differently. It reads your `strings.xml`, sends it to an LLM with context about your app, and writes the translated files directly into your project. The model understands UI language, keeps format specifiers intact, and produces natural-sounding output rather than word-for-word translations.

---

## Installation

```bash
pip install android-localisation
```

Requires Python 3.8+. No other dependencies.

---

## Quick start

```bash
# Step 1 — translate
android-localise translate --api-key YOUR_GEMINI_KEY

# Step 2 — fix any formatting issues the LLM may have introduced
android-localise fix

# Step 3 — verify nothing will crash at runtime
android-localise verify
```

That's the full workflow. Run these three commands after every time you update your English strings.

---

## What happens when you run translate

When you run `android-localise translate --api-key YOUR_KEY`, here's exactly what it does:

1. Looks for `app/src/main/res/values/strings.xml` — this is your English source
2. Scans the `res/` directory for any `values-*` folders (e.g. `values-hi`, `values-es`)
3. For each locale folder, sends your full `strings.xml` to the LLM with a prompt that instructs it to translate naturally, preserve all XML structure, and never touch format specifiers like `%1$s` or `%d`
4. Writes the translated `strings.xml` directly into each locale folder
5. Waits 5 seconds between each language request to avoid hitting API rate limits

**Defaults used when you don't specify anything:**

| What | Default |
|---|---|
| Provider | Gemini |
| Model | `gemini-2.5-flash` |
| Source directory | `app/src/main/res` |
| Delay between requests | 5 seconds |
| App context | none (generic prompt) |

Nothing is modified unless the translation comes back with valid XML. If a request fails, that language is skipped and logged — other languages continue.

---

## Setup

Before running translate, create empty folders for each language you want inside your `res/` directory:

```
app/src/main/res/
├── values/               ← your English source (must exist)
│   └── strings.xml
├── values-hi/            ← Hindi
├── values-es/            ← Spanish
├── values-fr/            ← French
├── values-de/            ← German
└── values-zh-rCN/        ← Chinese (Simplified)
```

The tool only translates into folders that already exist. Create the folder, run translate, done.

**Get a free API key:** [Google Gemini AI Studio](https://aistudio.google.com/) → Get API Key. The free tier handles most apps without hitting limits.

---

## Commands

### `translate`

```bash
android-localise translate --api-key YOUR_KEY
```

Add `--app-context` with a one-line description of your app. This meaningfully improves translation quality — the model knows whether "record" means a music track, a health log, or a database entry:

```bash
android-localise translate \
  --api-key YOUR_KEY \
  --app-context "a workout tracking app for gym beginners"
```

**All flags:**

| Flag | What it does | Default |
|---|---|---|
| `--api-key` | Your API key | reads from env var |
| `--provider` | Which AI to use: `gemini` `openai` `anthropic` `custom` | `gemini` |
| `--model` | Specific model to use | see [Providers](#providers) |
| `--app-context` | One-line description of your app | — |
| `--res-dir` | Path to your `res/` folder | `app/src/main/res` |
| `--base-url` | API endpoint for local/custom providers | — |
| `--sleep` | Seconds to wait between language requests | `5.0` |

---

### `fix`

```bash
android-localise fix
```

LLMs occasionally produce output that looks correct but breaks the Android build — curly apostrophes (`'`) instead of escaped ones (`\'`), unescaped double quotes, or mangled `%` signs. This command scans every translated `strings.xml` and corrects these silently.

Always run this before `verify` and before building.

---

### `verify`

```bash
android-localise verify
```

Takes every translated string that contains a format specifier (`%1$s`, `%d`, `%1$f`, etc.) and calls `String.format()` on it using Java's actual runtime. If a translated string would throw `UnknownFormatConversionException` or `MissingFormatArgumentException` in your app, this catches it before your users do.

Requires `javac` in your PATH. If you don't have it system-wide, run this from the Terminal tab inside Android Studio — it ships with a JDK.

---

### `models`

```bash
android-localise models                  # all providers
android-localise models --provider openai  # one provider
```

Lists every available model and fallback for each provider.

---

## Providers

By default the tool uses Gemini with `gemini-2.5-flash`. You can switch providers with `--provider` and optionally pin a specific model with `--model`.

| Provider | Default model | Fallbacks | API key env var |
|---|---|---|---|
| `gemini` _(default)_ | `gemini-2.5-flash` | `gemini-2.0-flash` → `gemini-1.5-flash` → `gemini-1.5-pro` | `GEMINI_API_KEY` |
| `openai` | `gpt-4o-mini` | `gpt-4o` → `gpt-3.5-turbo` | `OPENAI_API_KEY` |
| `anthropic` | `claude-3-5-haiku-latest` | `claude-3-5-sonnet-latest` → `claude-3-opus-latest` | `ANTHROPIC_API_KEY` |
| `custom` | set with `--model` | none | — |

If the default model returns a "model not found" error (e.g. it was deprecated), the tool automatically retries with the next fallback. If you pin a model with `--model`, no fallback is used.

**Using OpenAI:**
```bash
android-localise translate --provider openai --api-key YOUR_KEY
android-localise translate --provider openai --model gpt-4o --api-key YOUR_KEY
```

**Using Anthropic:**
```bash
android-localise translate --provider anthropic --api-key YOUR_KEY
```

**Using a local model (no API key needed):**
```bash
# Ollama
android-localise translate \
  --provider custom \
  --base-url http://localhost:11434/v1/chat/completions \
  --model llama3

# LM Studio
android-localise translate \
  --provider custom \
  --base-url http://localhost:1234/v1/chat/completions \
  --model mistral
```

---

## Environment variables

Set your API key as an env variable so you don't have to pass it every time:

```bash
# macOS / Linux
export GEMINI_API_KEY=your_key

# Windows PowerShell
$env:GEMINI_API_KEY = "your_key"
```

Then just run:
```bash
android-localise translate
```

| Variable | Used by |
|---|---|
| `GEMINI_API_KEY` | `--provider gemini` |
| `OPENAI_API_KEY` | `--provider openai` and `--provider custom` |
| `ANTHROPIC_API_KEY` | `--provider anthropic` |

---

## Full workflow example

```bash
# First time setup — create locale folders
mkdir -p app/src/main/res/values-hi
mkdir -p app/src/main/res/values-es
mkdir -p app/src/main/res/values-de

# Set your key once
export GEMINI_API_KEY=your_key

# Translate, fix, verify
android-localise translate --app-context "a habit tracking app"
android-localise fix
android-localise verify

# Build your app as usual
./gradlew assembleDebug
```

After this, whenever you add or change strings in your English `strings.xml`, run the same three commands again. Existing translated strings will be overwritten with fresh translations.

---

## Contributing

Bug reports and pull requests are welcome. For larger changes, open an issue first.

```bash
git clone https://github.com/BharathKmalviya/android-llm-localization
cd android-llm-localization
pip install -e .
```

Releases are automated via GitHub Actions — bump the version in `pyproject.toml` and `__init__.py`, update `CHANGELOG.md`, and push to `master`.

---

## License

[MIT](LICENSE)
