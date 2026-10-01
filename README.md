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

CLI output uses UTF-8, including when redirected to a file or pipe on Windows.

### Update notices

Interactive `android-localise` commands check PyPI for a newer stable release in
the background, at most once every 24 hours. When available, a note on stderr
shows `pip install --upgrade android-localisation`. The CLI never waits for the
lookup or installs an update automatically. A first short command may finish
before the lookup completes; a notice appears when a check completes during a
command or a later invocation can use its cached result.

Checks are skipped for help/version output, CI (`CI` set), redirected output and
pipes. Set `ANDROID_LOCALISE_NO_UPDATE_CHECK=1` to disable them, including when
using a local model offline. Lookup or cache failures stay silent and do not
change command exit codes. The small cache lives under
`%LOCALAPPDATA%/android-localisation` on Windows, or
`${XDG_CACHE_HOME:-~/.cache}/android-localisation` elsewhere. Only the package's
public release metadata is requested; API keys and Android resources are never
included.

---

## Quick start

```bash
# Step 1 — translate
android-localise translate --api-key YOUR_GEMINI_KEY

# Step 2 — fix any formatting issues the LLM may have introduced
android-localise fix

# Step 3 — check resources and Java formatting
android-localise verify
```

That's the full workflow. Run these three commands after every time you update your English strings.

---

## What happens when you run translate

When you run `android-localise translate --api-key YOUR_KEY`, here's exactly what it does:

1. Looks for `app/src/main/res/values/strings.xml` — this is your English source
2. If `--languages` is provided, selects those locales. Otherwise scans existing locale folders, skipping configuration-only folders such as `values-night`, `values-land`, `values-car`, and `values-sw600dp`
3. Sends your English XML to the LLM with app context and instructions to preserve resource structure, protected values, namespaces and format specifiers. With `--missing-only`, requests only resources absent from the target file; existing resources remain untouched, and complete locales make no API request
4. Parses the response and checks duplicate/unexpected/missing resources, attributes, inline markup, item structure, control escapes and format arguments. A valid result replaces the file atomically; new folders are created only when saving. `--dry-run` shows a diff without writing any files or creating folders
5. Waits 5 seconds between each language request to avoid hitting API rate limits

**Defaults used when you don't specify anything:**

| What | Default |
|---|---|
| Provider | Gemini |
| Model | `gemini-3.8-flash` |
| Source directory | `app/src/main/res` |
| Delay between requests | 5 seconds |
| App context | none (generic prompt) |

An invalid or incomplete response leaves the existing file unchanged. Other locales continue, and the final summary shows succeeded, failed and skipped counts. Exit code **0** means success; **1** means a setup, validation, API or save failure (including partial failure). Argument syntax errors use argparse's exit code **2**.

Normal translation still replaces the whole locale file. Use `--missing-only` to retain reviewed translations or combine it with `--dry-run` to preview additions. No cache, database or configuration file is needed.

---

## Setup

The only requirement is that `app/src/main/res/values/strings.xml` exists — your English source file.

For target languages, you have two options:

**Option A — let the tool create everything:**
```bash
android-localise translate --api-key YOUR_KEY --languages hi,es,fr,de
```
This translates into Hindi, Spanish, French and German, creating each folder and `strings.xml` when its translation passes validation.

**Option B — pre-create folders yourself:**
```
app/src/main/res/
├── values/               ← your English source (must exist)
│   └── strings.xml
├── values-hi/            ← empty folder is fine
├── values-es/
└── values-fr/
```
Run `android-localise translate --api-key YOUR_KEY` and it picks up locale folders, creating `strings.xml` inside each one after successful translation. Locale examples include `values-hi`, `values-es-rES`, `values-b+zh+Hans`, and `values-en-night`; qualifier-only folders are skipped. `--languages` accepts the same forms without the optional `values-` prefix and rejects path separators or non-locale names.

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
| `--missing-only` | Translate absent resources; retain existing translations | off (refresh whole file) |
| `--dry-run` | Generate and validate output, then print a diff without writing files | off |

**Preserve reviewed translations:**

```bash
android-localise translate --languages hi,es --missing-only
android-localise translate --languages hi --missing-only --dry-run
```

`--dry-run` still calls the selected provider and may incur API charges. It is a translation preview, not a no-network estimate. `--missing-only` keeps existing resources, comments and text, but validates them against the current source first. An invalid existing file is reported rather than silently repaired. It does not detect changed English text for an existing key; use the normal translation mode when you deliberately want to refresh those resources. Arrays and plurals count as whole resources: this mode does not fill individual missing items.

Validation permits positional placeholder reordering such as `%s %d` becoming `%2$d %1$s`, while checking argument identities, conversions, formatting options and occurrence counts. Non-translatable resources may be omitted from locale files to use Android's default fallback, but must remain unchanged if included.

---

### `fix`

```bash
android-localise fix
android-localise fix --res-dir path/to/res
```

This command scans locale `strings.xml` files, converts curly apostrophes, escapes raw apostrophes, and doubles bare percent signs while retaining recognized format patterns. It checks XML before and after changes and saves atomically. Inline markup attributes and non-translatable values are left alone. It handles single- and double-quoted resource names.

Strings marked `formatted="false"` are skipped — their `%` signs are literal, not format specifiers.

Always run this before `verify` and before building.

`fix` repairs `<string>` text only. It does not repair arbitrary malformed XML, double-quote handling, or array/plural items, and it does not prove a format pattern is valid. Review its changes and use `verify` and your Android build afterward.

---

### `verify`

```bash
android-localise verify
android-localise verify --res-dir path/to/res
```

First parses XML and compares localized resources with `values/strings.xml`, checking coverage, duplicates, protected content, attributes, inline markup and format-argument preservation. Then checks formatted strings and array/plural items with Java's actual `String.format()` runtime, including date/time and relative argument indexing. Both checks return nonzero on failure. Empty locale folders without a `strings.xml` are skipped.

Strings marked `formatted="false"` are skipped. Requires `javac` in your PATH. If you don't have it system-wide, run this from the Terminal tab inside Android Studio — it ships with a JDK.

`formatted="false"` skips formatting checks only; XML, resource coverage and attribute checks still apply. Java compilation uses a temporary directory, so installed package files are not modified. Verification is deliberately stricter than Android's missing-string fallback: missing translatable resources are reported. Passing these checks does not replace an Android build, native-speaker review or device layout checks.

---

### `models`

```bash
android-localise models                  # all providers
android-localise models --provider openai  # one provider
```

Lists this CLI's configured defaults and automatic fallbacks, not the provider's entire model catalog. Any supported model can still be selected with `--model`.

---

## Providers

By default the tool uses Gemini with `gemini-3.8-flash`. You can switch providers with `--provider` and optionally pin a specific model with `--model`. Configured defaults and fallbacks use only the latest general-purpose text-model lineup, with defaults favoring speed and cost within that lineup.

| Provider | Default model | Fallbacks | API key env var |
|---|---|---|---|
| `gemini` _(default)_ | `gemini-3.8-flash` | none | `GEMINI_API_KEY` |
| `openai` | `gpt-6-luna` | `gpt-6.1-sol` → `gpt-6-astra` | `OPENAI_API_KEY` |
| `anthropic` | `claude-sonnet-5-5` | `claude-opus-5-5` | `ANTHROPIC_API_KEY` |
| `custom` | set with `--model` | none | `OPENAI_API_KEY` (optional) |

If the default model returns a "model not found" error (e.g. it was deprecated), the tool automatically retries with the next fallback. If you pin a model with `--model`, no fallback is used.

Model IDs and compatibility checked against [Google's model catalog](https://ai.google.dev/gemini-api/docs/models), [OpenAI's model catalog](https://developers.openai.com/api/docs/models) and [Anthropic's model catalog](https://platform.claude.com/docs/en/models/overview) on **2026-10-02**. Older Gemini, GPT-5 and Haiku 4.5 models are excluded from automatic selection. Gemini has no fallback in its latest stable text generation. OpenAI and Anthropic fallbacks are higher-cost models; pin `--model` to avoid automatic tier changes. Explicit model selection and custom/local endpoints remain available. The catalog is bundled with each CLI release, rather than automatically discovering models at runtime.

OpenAI and local providers retain the Chat Completions request format. Provider replies indicating truncation or blocked/incomplete output are rejected. Anthropic allows up to 16,384 output tokens per request and text blocks are collected separately from thinking blocks. Large files can still exceed a model's limits; automatic batching is future work.

**Using OpenAI:**
```bash
android-localise translate --provider openai --api-key YOUR_KEY
android-localise translate --provider openai --model gpt-6-luna --api-key YOUR_KEY
# Optional stronger tier; different cost/latency
android-localise translate --provider openai --model gpt-6.1-sol --api-key YOUR_KEY
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
| `ANDROID_LOCALISE_NO_UPDATE_CHECK` | Set to `1` to disable update checks/notices |
| `CI` | When nonempty, skips update checks/notices |

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

After this, whenever you add or change strings in your English `strings.xml`, run the same three commands again. Existing translated strings are refreshed by default. For additions that should retain existing translations, run `translate --missing-only` instead; it does not detect changed source text for existing keys.

---

## Platform support

I develop and **manually test this project on Windows only** at the moment. It is written in pure Python (stdlib only) and should run on macOS and Linux, but I have **not verified** those platforms yet.

I especially need help testing on:

- **macOS** — `translate`, `fix`, `verify` (including `javac` / Android Studio terminal)
- **Linux** — same workflow, plus common CI environments

If you use another OS, please try the [quick start](#quick-start) workflow and report what you find:

- **Works?** — open a [GitHub issue](https://github.com/BharathKmalviya/android-llm-localization/issues) titled e.g. `Confirmed working on macOS 14` with your OS, Python version, and provider used
- **Broken?** — open a [bug report](https://github.com/BharathKmalviya/android-llm-localization/issues/new?template=bug_report.md) with the full error output
- **Want to help more?** — see [Contributing](#contributing) and [CONTRIBUTING.md](CONTRIBUTING.md)

PRs with cross-platform fixes and test notes are especially appreciated.

---

## Limitations

| Topic | Detail |
|---|---|
| **Platform testing** | I test on **Windows only** — macOS and Linux need community verification (see [Platform support](#platform-support)) |
| **Scope** | Reads `values/strings.xml` only. Strings, arrays and plurals within that file are checked; separate XML files are not scanned |
| **Plurals** | Preserves source quantities and item structure; does not generate target-language plural categories. Review plural completeness for each language |
| **Overwrite** | Normal runs refresh whole files. `--missing-only` retains existing resources but does not detect source changes |
| **Folder scan** | Recognizes language-first and Android `b+` locale forms, with optional trailing qualifiers. MCC/MNC-prefixed resource folders are not scanned |
| **Validation** | Requires source attributes, inline element order and formatting options to match. DTD/entity declarations are unsupported; checks do not replace Android compilation or language review |
| **Large files** | One request per locale; no automatic batching or resume cache. Incomplete output is rejected |
| **Network** | `translate` requires internet access to reach the LLM API (except local `custom` providers) |
| **JDK** | `verify` requires `javac` on your PATH |

---

## Troubleshooting

| Problem | What to try |
|---|---|
| `Could not find English strings.xml` | Check `--res-dir` points to your `res/` folder and `values/strings.xml` exists |
| `No locale directories found` | Add `--languages hi,es,fr` or create `values-<lang>/` folders manually |
| API auth errors | Confirm your key env var or `--api-key` matches the `--provider` |
| Resource validation fails | Read the named resource error; check source/target keys, attributes, placeholders and markup. Existing files are retained |
| `javac` not found | Install a JDK or run `verify` from Android Studio's terminal |
| Build fails on apostrophes | Run `android-localise fix` before building |
| `%` crashes at runtime | Run `android-localise verify` — it catches bad format specifiers before release |
| Wrong folder translated | Use `--languages` to target exact locale codes instead of folder scan |

---

## Roadmap

- [ ] **iOS support** — translate `Localizable.strings` and `Localizable.xcstrings` for iOS/macOS apps. The LLM prompt and provider logic is already in place — it mainly needs a parser for Apple's strings format and the right folder structure (`<lang>.lproj/`). Good first contribution if you're familiar with iOS projects.
- [ ] **Smarter locale folder detection** — skip non-locale `values-*` qualifiers (`night`, `sw600dp`, `v21`, etc.) when scanning without `--languages`
- [ ] **Automated test suite** — unit tests for `fix`, XML parsing, and format-specifier edge cases
- [ ] **Cross-platform verification** — confirm `translate`, `fix`, and `verify` on macOS and Linux (I currently test on Windows only)

---

## Contributing

I welcome bug reports, pull requests, and **cross-platform testing**. For larger changes, please open an issue first.

**No code required** — if you are on macOS or Linux, running the tool and filing an issue (pass or fail) is a real contribution. See [Platform support](#platform-support).

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow, branch strategy, and release process.

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
