# android-localisation

[![PyPI version](https://img.shields.io/pypi/v/android-localisation.svg)](https://pypi.org/project/android-localisation/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://pypi.org/project/android-localisation/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**PyPI:** [`android-localisation`](https://pypi.org/project/android-localisation/) · **CLI:** `android-localise` · **Repo:** [android-llm-localization](https://github.com/BharathKmalviya/android-llm-localization)

Translate your Android `strings.xml` into multiple languages using AI — Gemini, OpenAI, Anthropic, or a local model via Ollama. No paid translation service, no CSV exports, no copy-paste.

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
2. If `--languages` is provided, creates any missing `values-<lang>/` folders automatically. Otherwise scans the `res/` directory for existing `values-*` folders
3. For each locale, if `strings.xml` doesn't exist it creates the file first, then sends your full English XML to the LLM with a prompt that instructs it to translate naturally, preserve all XML structure, and never touch format specifiers like `%1$s` or `%d`
4. Writes the translated `strings.xml` directly into each locale folder
5. Waits 5 seconds between each language request to avoid hitting API rate limits

**Defaults used when you don't specify anything:**

| What | Default |
|---|---|
| Provider | Gemini |
| Model | `gemini-3.5-flash` |
| Source directory | `app/src/main/res` |
| Delay between requests | 5 seconds |
| App context | none (generic prompt) |

Nothing is modified unless the translation comes back with valid XML. If a request fails, that language is skipped and logged — other languages continue.

---

## Setup

The only requirement is that `app/src/main/res/values/strings.xml` exists — your English source file.

For target languages, you have two options:

**Option A — let the tool create everything:**
```bash
android-localise translate --api-key YOUR_KEY --languages hi,es,fr,de
```
This creates `values-hi/`, `values-es/`, `values-fr/`, `values-de/` folders and their `strings.xml` files automatically, then translates into each one.

**Option B — pre-create folders yourself:**
```
app/src/main/res/
├── values/               ← your English source (must exist)
│   └── strings.xml
├── values-hi/            ← empty folder is fine
├── values-es/
└── values-fr/
```
Run `android-localise translate --api-key YOUR_KEY` and it picks up any `values-*` folder it finds, creating `strings.xml` inside each one if it doesn't exist yet.

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
| `--languages` | Comma-separated language codes — creates folders and files automatically | — |
| `--app-context` | One-line description of your app | — |
| `--res-dir` | Path to your `res/` folder | `app/src/main/res` |
| `--base-url` | API endpoint for local/custom providers | — |
| `--sleep` | Seconds to wait between language requests | `5.0` |
| `--timeout` | Seconds to wait for each API response (up to 3 attempts on timeout) | `180` |

---

### `fix`

```bash
android-localise fix
android-localise fix --res-dir path/to/res
```

LLMs occasionally produce output that looks correct but breaks the Android build — curly apostrophes (`'`) instead of escaped ones (`\'`), unescaped double quotes, or mangled `%` signs. This command scans every translated `strings.xml` and corrects these silently.

Strings marked `formatted="false"` are skipped — their `%` signs are literal, not format specifiers.

Always run this before `verify` and before building.

---

### `verify`

```bash
android-localise verify
android-localise verify --res-dir path/to/res
```

Takes every translated string that contains a format specifier (`%1$s`, `%d`, `%1$f`, etc.) and calls `String.format()` on it using Java's actual runtime. If a translated string would throw `UnknownFormatConversionException` or `MissingFormatArgumentException` in your app, this catches it before your users do.

Strings marked `formatted="false"` are skipped. Requires `javac` in your PATH. If you don't have it system-wide, run this from the Terminal tab inside Android Studio — it ships with a JDK.

---

### `models`

```bash
android-localise models                  # all providers
android-localise models --provider openai  # one provider
```

Lists every available model and fallback for each provider.

---

## Providers

By default the tool uses Gemini with `gemini-3.5-flash`. You can switch providers with `--provider` and optionally pin a specific model with `--model`.

| Provider | Default model | Fallbacks | API key env var |
|---|---|---|---|
| `gemini` _(default)_ | `gemini-3.5-flash` | `gemini-3.1-flash-lite` → `gemini-2.5-flash` → `gemini-2.5-flash-lite` | `GEMINI_API_KEY` |
| `openai` | `gpt-5.4-mini` | `gpt-5-mini` → `gpt-4o-mini` | `OPENAI_API_KEY` |
| `anthropic` | `claude-haiku-4-5` | `claude-sonnet-4-6` → `claude-opus-4-8` | `ANTHROPIC_API_KEY` |
| `custom` | set with `--model` | none | `OPENAI_API_KEY` (optional) |

If the default model returns a "model not found" error (e.g. it was deprecated), the tool automatically retries with the next fallback. If you pin a model with `--model`, no fallback is used.

**Using OpenAI:**
```bash
android-localise translate --provider openai --api-key YOUR_KEY
android-localise translate --provider openai --model gpt-5.4-mini --api-key YOUR_KEY
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

# Windows CMD
set GEMINI_API_KEY=your_key
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
| `API_KEY` | fallback for any provider if the provider-specific var is not set |

---

## Full workflow example

```bash
# First time setup — create locale folders (macOS / Linux)
mkdir -p app/src/main/res/values-hi
mkdir -p app/src/main/res/values-es
mkdir -p app/src/main/res/values-de

# Windows PowerShell
New-Item -ItemType Directory -Force app/src/main/res/values-hi
New-Item -ItemType Directory -Force app/src/main/res/values-es
New-Item -ItemType Directory -Force app/src/main/res/values-de

# Set your key once
export GEMINI_API_KEY=your_key   # or $env:GEMINI_API_KEY on Windows

# Translate, fix, verify
android-localise translate --app-context "a habit tracking app"
android-localise fix
android-localise verify

# Build your app as usual
./gradlew assembleDebug
```

After this, whenever you add or change strings in your English `strings.xml`, run the same three commands again. Existing translated strings will be overwritten with fresh translations.

---

## Platform support

This project is developed and **manually tested on Windows only** at the moment. It is written in pure Python (stdlib only) and should run on macOS and Linux, but those platforms have **not been verified** by the maintainer yet.

We especially need help testing on:

- **macOS** — `translate`, `fix`, `verify` (including `javac` / Android Studio terminal)
- **Linux** — same workflow, plus common CI environments

If you use another OS, please try the [quick start](#quick-start) workflow and report what you find:

- **Works?** — open a [GitHub issue](https://github.com/BharathKmalviya/android-llm-localization/issues) titled e.g. `Confirmed working on macOS 14` with your OS, Python version, and provider used
- **Broken?** — open a [bug report](https://github.com/BharathKmalviya/android-llm-localization/issues/new?template=bug_report.md) with the full error output
- **Want to help more?** — see [Contributing](#contributing) and [CONTRIBUTING.md](CONTRIBUTING.md)

Cross-platform fixes and test notes in pull requests are very welcome.

---

## Limitations

| Topic | Detail |
|---|---|
| **Platform testing** | Maintainer-tested on **Windows only** — macOS and Linux need community verification (see [Platform support](#platform-support)) |
| **Scope** | Translates `values/strings.xml` only — not `plurals.xml`, `arrays.xml`, or other resource files |
| **Overwrite** | Each run replaces the entire `strings.xml` in each locale folder with a fresh LLM translation |
| **Folder scan** | Without `--languages`, every `values-*` folder is treated as a locale. Qualifier-only folders like `values-night` or `values-sw600dp` may be picked up incorrectly — prefer `--languages` or keep only locale folders in `res/` |
| **Network** | `translate` requires internet access to reach the LLM API (except local `custom` providers) |
| **JDK** | `verify` requires `javac` on your PATH |

---

## Troubleshooting

| Problem | What to try |
|---|---|
| `Could not find English strings.xml` | Check `--res-dir` points to your `res/` folder and `values/strings.xml` exists |
| `No locale directories found` | Add `--languages hi,es,fr` or create `values-<lang>/` folders manually |
| API auth errors | Confirm your key env var or `--api-key` matches the `--provider` |
| `javac` not found | Install a JDK or run `verify` from Android Studio's terminal |
| Build fails on apostrophes | Run `android-localise fix` before building |
| `%` crashes at runtime | Run `android-localise verify` — it catches bad format specifiers before release |
| Wrong folder translated | Use `--languages` to target exact locale codes instead of folder scan |

---

## Roadmap

- [ ] **iOS support** — translate `Localizable.strings` and `Localizable.xcstrings` for iOS/macOS apps. The LLM prompt and provider logic is already in place — it mainly needs a parser for Apple's strings format and the right folder structure (`<lang>.lproj/`). Good first contribution if you're familiar with iOS projects.
- [ ] **Smarter locale folder detection** — skip non-locale `values-*` qualifiers (`night`, `sw600dp`, `v21`, etc.) when scanning without `--languages`
- [ ] **Automated test suite** — unit tests for `fix`, XML parsing, and format-specifier edge cases
- [ ] **Cross-platform verification** — confirm `translate`, `fix`, and `verify` on macOS and Linux (Windows is maintainer-tested today)

---

## Contributing

Bug reports, pull requests, and **cross-platform testing** are all welcome. For larger changes, open an issue first.

**No code required** — if you are on macOS or Linux, running the tool and filing an issue (pass or fail) is a real contribution. See [Platform support](#platform-support).

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full development workflow, branch strategy, and release process.

```bash
git clone https://github.com/BharathKmalviya/android-llm-localization
cd android-llm-localization
git checkout dev
pip install -e .
```

Day-to-day work happens on the `dev` branch. Releases are merged to `master` via pull request, which triggers automated PyPI publishing.

---

## Security

To report a security vulnerability, see [SECURITY.md](SECURITY.md). Please do not open public issues for security-sensitive reports.

---

## License

[MIT](LICENSE)
