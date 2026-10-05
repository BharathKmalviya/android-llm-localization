# android-localisation

[![PyPI version](https://img.shields.io/pypi/v/android-localisation.svg)](https://pypi.org/project/android-localisation/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://pypi.org/project/android-localisation/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**PyPI:** [`android-localisation`](https://pypi.org/project/android-localisation/) · **CLI:** `android-localise` · **Repo:** [android-llm-localization](https://github.com/BharathKmalviya/android-llm-localization)

Translate your Android `strings.xml` and Google Play store listing into multiple languages using AI — Gemini, OpenAI, Anthropic, or a local model via Ollama.

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

### Windows PATH setup

If PowerShell cannot find `android-localise`, run this once using the same Python
that installed the package:

```powershell
python -m android_localisation setup-path
```

This detects the installed Scripts folder and adds it to your **user PATH**,
preserving existing entries and avoiding duplicates. No administrator access is
required. Close and reopen your terminal application afterward. Normal wheel
installation with `pip` does not run this setup automatically, and existing
PowerShell sessions cannot have their environment changed by the child Python
process. Virtual environments should be activated instead; their Scripts folders
are not persisted in user PATH.

The CLI also works immediately through Python on any platform:

```powershell
python -m android_localisation --help
python -m android_localisation translate --api-key YOUR_KEY
```

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

1. Reads `app/src/main/res/values/strings.xml` by default, or the XML file supplied with `--source`. `--source-language` identifies its language (default `en-US`)
2. Combines `--languages` and `--languages-file`, expands `all`, removes duplicates and applies `--exclude-languages`. Android qualifiers and conventional language tags are accepted. Without an explicit list, scans existing locale folders in the destination directory, skipping configuration-only folders such as `values-night`, `values-land`, `values-car`, and `values-sw600dp`. The destination defaults to `--res-dir`, or can be set with `--output-dir`
3. Sends the source XML to the LLM with its language, app context and instructions to preserve resource structure, protected values, namespaces and format specifiers. With `--missing-only`, requests only resources absent from the target file; existing resources remain untouched, and complete locales make no API request
4. Parses the response and checks duplicate/unexpected/missing resources, attributes, inline markup, item structure, control escapes and format arguments. A valid result replaces the file atomically; new folders are created only when saving. `--skip-existing` validates existing files and skips them without API calls. `--dry-run` shows a diff without writing any files or creating folders
5. Waits 5 seconds between each language request to avoid hitting API rate limits

Keys resolve from `--api-key`, then provider environment variables / `API_KEY`,
then saved Windows credentials for built-in provider endpoints. The CLI never
prompts for a key during translation; use `credentials set` yourself beforehand.

**Defaults used when you don't specify anything:**

| What | Default |
|---|---|
| Provider | Gemini |
| Model | `gemini-3.5-flash-lite` |
| Source directory | `app/src/main/res` |
| Delay between requests | 5 seconds |
| App context | none (generic prompt) |

An invalid or incomplete response leaves the existing file unchanged. Other locales continue, and the final summary shows succeeded, failed and skipped counts. Exit code **0** means success; **1** means a setup, validation, API or save failure (including partial failure). Argument syntax errors use argparse's exit code **2**.

Normal translation still replaces the whole locale file. Use `--missing-only` to retain reviewed translations or combine it with `--dry-run` to preview additions. No cache, database or configuration file is needed.

---

## Setup

Provide source XML at `app/src/main/res/values/strings.xml` by default, or supply
another file with `--source` and its language with `--source-language`.

For target languages, you have two options:

**Option A — let the tool create everything:**
```bash
android-localise translate --api-key YOUR_KEY --languages hi,es,fr,de
```
This translates into Hindi, Spanish, French and German, creating each folder and `strings.xml` when its translation passes validation.

To translate into the same 86-locale catalog used for store listings:

```bash
android-localise translate --api-key YOUR_KEY --languages all
```

`all` is case-insensitive and can be combined with extra languages. The bundled catalog is shared
with `store-listing` and mapped to [Android resource qualifiers](https://developer.android.com/guide/topics/resources/providing-resources#AlternativeResources):
`hi-IN` becomes `values-hi-rIN`, `pt-BR` becomes `values-pt-rBR`, `es-419`
becomes `values-b+es+419`, and `fil` becomes `values-b+fil`. Regional variants,
including English ones, remain separate; `values/strings.xml` remains the source.
This is the bundled Play locale set, not every possible Android locale.

The same XML validation, atomic saves, delay, `--missing-only` and `--dry-run`
behavior applies to each locale. Normal translation refreshes existing files;
use `--languages all --missing-only` to keep reviewed resources. Generating or
previewing all locales can use 86 translation requests plus provider retries;
complete locales in missing-only mode skip API calls. No folders are created
during previews or before their translation passes validation.

**Option B — pre-create folders yourself:**
```
app/src/main/res/
├── values/               ← your English source (must exist)
│   └── strings.xml
├── values-hi/            ← empty folder is fine
├── values-es/
└── values-fr/
```
Run `android-localise translate --api-key YOUR_KEY` and it picks up locale folders, creating `strings.xml` inside each one after successful translation. Locale examples include `values-hi`, `values-es-rES`, `values-b+zh+Hans`, and `values-en-night`; qualifier-only folders are skipped. `--languages` accepts the same forms without the optional `values-` prefix, plus conventional tags such as `es-ES` or `zh-Hant-TW`, and rejects path separators or non-locale names.

**Get a free API key:** [Google Gemini AI Studio](https://aistudio.google.com/) → Get API Key. The free tier handles most apps without hitting limits.

---

## Commands

Run `android-localise` or `android-localise --help` to see every command and the
typical workflow. Each command has detailed help with its options and examples:

```bash
android-localise translate --help
android-localise store-listing --help
android-localise fix --help
android-localise verify --help
android-localise models --help
python -m android_localisation setup-path --help
```

Use `android-localise --version` to check the installed version. Help/version
requests do not call providers, check for updates or modify files/PATH.

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
| `--api-key` | Explicit key override; omit for environment or saved Windows credentials | environment, then saved Windows key |
| `--provider` | Which AI to use: `gemini` `openai` `anthropic` `custom` | `gemini` |
| `--model` | Specific model to use | see [Providers](#providers) |
| `--languages` | Comma-separated Android/conventional codes and/or `all`, e.g. `all,zu` or `hi,es-ES,b+es+419` | scan existing destination locale folders |
| `--languages-file` | UTF-8 comma/newline language list; combines with `--languages` | none |
| `--exclude-languages` | Remove exact normalized locales after selection/discovery | none |
| `--source` | Read a custom XML source file | `RES_DIR/values/strings.xml` |
| `--source-language` | Language tag for source XML | `en-US` |
| `--output-dir` | Save translated XML into this Android res/ directory | `--res-dir` |
| `--skip-existing` | Validate and skip existing XML files without API calls | off; incompatible with `--missing-only` |
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

### `store-listing`

Translate an existing Google Play listing's **app name**, **short description**
and **full description**, using the same providers, keys, model defaults,
model-not-found fallbacks and timeout handling as `translate`.

Create a UTF-8 `listing.json` containing exactly these three nonempty strings:

```json
{
  "app_name": "Pocket Notes",
  "short_description": "Write and organize your notes",
  "full_description": "Write notes and organize them in folders.\n\nFind saved notes with search."
}
```

Use your actual app details. JSON represents paragraph breaks as `\n`; this
command translates supplied copy and does not infer features from Android XML.

```bash
# Translate every bundled Google Play listing locale
android-localise store-listing --source listing.json --languages all
# Or select languages manually
android-localise store-listing --source listing.json --languages hi,es-ES,pt-BR
# Keep the original brand/app name and preview translations
android-localise store-listing --source listing.json --languages ja,zh-TW --keep-app-name --dry-run
# Explicitly refresh reviewed files when the source changes
android-localise store-listing --source listing.json --languages hi --overwrite
```

Outputs are readable UTF-8 `store-listings/hi.json`, `store-listings/es-ES.json`,
etc., with the same three keys. Review the text and copy each field into its
language's Play Console listing; JSON is a local output format, not a Play
Console import file. The CLI does not upload or publish a listing.

| Flag | Description | Default |
|---|---|---|
| `--source` | UTF-8 JSON source listing | required |
| `--languages` | Play tags and/or `all`, e.g. `all,zu` or `hi-IN,es-ES` | required unless `--languages-file` supplies a list |
| `--languages-file` | UTF-8 comma/newline language list; combines with `--languages` | none |
| `--exclude-languages` | Remove exact normalized Play tags after selection | none |
| `--source-language` | Source listing language tag | `en-US` |
| `--output-dir` | Directory for `LOCALE.json` output | `store-listings` |
| `--keep-app-name` | Preserve the source app name exactly | off; name is localized with brand-preservation instructions |
| `--overwrite` | Replace existing locale files after validation | off; existing valid files are skipped |
| `--dry-run` | Generate, validate and display diffs without files/directories being written | off; API usage applies |
| `--provider` | `gemini`, `openai`, `anthropic`, `custom` | `gemini` |
| `--model` | Pin any supported model and disable fallbacks | provider default |
| `--api-key` | Explicit key override; omit for environment or saved Windows credentials | environment, then saved Windows key |
| `--base-url` | OpenAI-compatible endpoint; required for `custom` | provider endpoint |
| `--app-context` | Terminology context; source copy remains the source of facts | none |
| `--sleep` | Delay between requests, including correction/fallback requests | `5.0` seconds |
| `--timeout` | Per-response timeout; up to three attempts on timeout | `180` seconds |

**Validation:** source and translated fields must fit **30 / 80 / 4,000 characters**
respectively, as specified in [Google Play's product details guidance](https://support.google.com/googleplay/android-developer/answer/9859152).
Counts use Python Unicode code points, including spaces, punctuation, newlines
and any HTML markup, rather than UTF-8 bytes or visual glyphs. Check final counts
in Play Console too. Names and short descriptions must be single-line text.
Missing/extra/duplicate keys, blank fields, invalid JSON, unsupported controls
and unpaired surrogates are rejected. Overlong or otherwise invalid model output
gets up to **two correction requests**, with validation feedback; this can incur
additional API usage. Text is never blindly truncated. After validation the
complete listing is saved atomically. Rejected output preserves existing files;
other languages continue and any failure produces exit code 1.

Existing files are validated and skipped without translation API calls unless
`--overwrite` is set, including during a dry run. An invalid existing file fails
instead of being silently replaced; `--overwrite` explicitly regenerates it.
`--dry-run --overwrite` previews changes to existing files. Source/output path
collisions are rejected. Locale tags are syntax-checked and normalized (for
example `pt-br` becomes `pt-BR`); duplicate tags run once. This does not check
manual codes against Google Play's supported-language catalog. Choose tags available in your Console;
Android forms such as `values-hi`, `es-rES` and `b+zh+Hans` are not accepted here.

`--languages all` expands to the **86 store-listing locales** in
[Google Play's available-language list](https://support.google.com/googleplay/android-developer/answer/9844778?hl=en),
verified on **2026-10-02** and bundled with this release. It includes regional
variants and the source locale if present in the list. It does not fetch or
change the catalog at runtime. `all` is case-insensitive and can be combined with
manual additions. Use `--languages`, `--languages-file`, or both. Manual selection retains normalization and
duplicate removal. Each locale uses its own request, subject to existing-file
skips, correction/fallback requests and the configured delay. API usage applies
to all generated locales, including previews. Existing valid files still skip
unless `--overwrite` is set.

**Translation prompt:** includes the supplied [metadata policy](https://play.google.com/about/storelisting-promotional/metadata),
[Help Centre guidance](https://support.google.com/googleplay/android-developer/answer/9866151),
[programme policies](https://play.google.com/about/developer-content-policy) and
[advance-notice guidance](https://support.google.com/googleplay/android-developer/answer/6320428)
as publishing references, alongside text guidance reviewed on **2026-10-02**.
It asks for accurate, natural descriptions without invented claims, keyword
stuffing, misleading affiliations or anonymous testimonials. App names and
short descriptions avoid ranking/promotion language and decorative emoji;
short descriptions also avoid calls to action. Existing factual limitations,
URLs, brand names, required disclosures and full-description markup should be
preserved. Unsupported promotional wording should become factual copy.
These semantic rules are prompt instructions, not automated policy checks.
No policy pages are fetched by the CLI at runtime, so review the current linked
policies and translated claims before submitting. Advance notice remains a
separate developer step if eligible; no notice, permission or approval is implied.

**Manual check:** translate two languages, review all three fields with a native
speaker and check their counts in Play Console. Rerun to confirm existing files
skip, then use `--overwrite --dry-run` to review refreshes without saving.
Try a source name longer than 30 characters to confirm rejection before any
translation request.
For all-locale coverage, run `--languages all` into a separate output directory,
confirm 86 successful JSON outputs, then rerun and confirm 86 skips. Use a manual
list such as `hi-IN,es-ES` to confirm only those two outputs are generated.

---

### Composing translation commands

Both commands accept languages from the CLI, a UTF-8 file, or both. File entries
can be comma-separated or one per line, with blank lines and `#` comments.
For example, `languages.txt` can contain:

```text
# Shared targets; conventional tags work in both commands
hi-IN
es-ES,pt-BR
zh-Hant-TW
```

```bash
# All bundled locales plus an extra, excluding exact regional variants
android-localise translate --languages all,zu --exclude-languages en-US,en-GB
android-localise store-listing --source listing.json --languages all,zu --exclude-languages en-US,en-GB
# Reuse a language file and add more targets
android-localise translate --languages-file languages.txt --languages de-DE --dry-run
android-localise store-listing --source listing.json --languages-file languages.txt --languages de-DE --dry-run
# Translate another source language into a separate Android resource directory
android-localise translate --source source/strings.xml --source-language fr-FR --output-dir translated/res --languages hi-IN,es-ES --skip-existing
```

Ordering is CLI entries first, then file entries. `all` expands wherever it
appears; duplicates run once. XML equivalent qualifiers such as `es-ES`,
`es-rES` and `b+es+ES` run once, preserving the first selected folder spelling.
Exclusions apply after expansion and use exact locale identity: excluding `en`
does not exclude `en-US` or every English region. You can pass Android forms to
XML exclusions, and conventional tags to both commands. Listing language files
accept Play tags only. Manual tags are syntax-checked, not restricted to the
bundled Play catalog; verify Play Console supports any additional listing locale.
An empty final selection or invalid language/file fails before API calls or
folder creation. Source/output collisions, including linked source files, are
rejected. Provider, model, custom endpoint, context, delays, timeout and previews
remain independently configurable.

XML preservation choices are whole-file refresh (default), `--missing-only`
(fill missing resources) or `--skip-existing` (skip complete valid files).
The two preservation flags cannot be combined. Listing preservation remains
skip-by-default with explicit `--overwrite`. Preview flags can combine with any
valid mode and still use the provider for newly generated translations.
No setup, config file or language file is mandatory for existing commands.
`fix` and `verify` still use `--res-dir`; point them at a separate XML output
directory after placing the intended default source at `values/strings.xml` there.

Manual check: reuse one language file with both commands, combine `all` with an
extra locale and exclusions, preview before saving, and confirm existing files
are retained under the chosen preservation mode. Build the app and review the
actual translations; local validation does not prove linguistic quality.

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

### `setup-path` (Windows)

```powershell
python -m android_localisation setup-path
```

Adds the installed Scripts directory to Windows user PATH. See
[Windows PATH setup](#windows-path-setup) for terminal restart and virtual
environment behavior. All commands can also run through `python -m android_localisation`.

---

## Providers

By default the tool uses Gemini 3.5 Flash-Lite (`gemini-3.5-flash-lite`) for both XML and store listing translation. You can switch providers with `--provider` and optionally pin a specific model with `--model`.

| Provider | Default model | Fallback | API key env var |
|---|---|---|---|
| `gemini` _(default)_ | `gemini-3.5-flash-lite` | `gemini-3.8-flash` | `GEMINI_API_KEY` |
| `openai` | `gpt-6-luna` | `gpt-5.6-terra` | `OPENAI_API_KEY` |
| `anthropic` | `claude-haiku-4-5` | `claude-sonnet-5-5` | `ANTHROPIC_API_KEY` |
| `custom` | set with `--model` | none | `OPENAI_API_KEY` (optional) |

Each hosted provider has exactly one automatic fallback. If the default model returns a "model not found" error (e.g. it was deprecated), the tool retries with that fallback. Authentication, quota and network errors do not trigger a model fallback. If you pin a model with `--model`, no fallback is used.

These default/fallback pairs follow the selected configuration. Gemini model IDs were checked against [Flash-Lite](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite) and [3.8 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash) documentation; the OpenAI fallback against [GPT-5.6 Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra); and Anthropic's default/fallback against its [model migration guide](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide) on **2026-10-05**. The existing OpenAI default was checked on **2026-10-02**. Pin `--model` to avoid automatic model changes. Explicit model selection and custom/local endpoints remain available. The catalog is bundled with each CLI release, rather than automatically discovering models at runtime.

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

## Save a key once on Windows

Run this yourself in your terminal:

```bash
android-localise credentials set --provider gemini
```

Enter your key at the hidden prompt. It is stored in **Windows Credential
Manager**, for your Windows user on this computer, and persists across terminal
and computer restarts. The CLI does not write a plaintext key file or modify
environment variables. Running `set` again replaces that provider's saved key.
There is no key argument or piped-input option for this command; it requires an
interactive terminal and refuses a prompt that cannot hide input.

Then you or an AI assistant can run ordinary commands without including a key:

```bash
android-localise translate --languages hi,es
android-localise store-listing --source listing.json --languages hi-IN,es-ES
android-localise credentials status --provider gemini
android-localise credentials remove --provider gemini
```

`status` reports only `saved` or `not saved`; no command displays the saved value.
`remove` deletes only this CLI's saved entry for that provider; it does not revoke
the provider key or clear environment-variable overrides. The same commands also
work with `python -m android_localisation credentials ...`.

| Argument | Description | Default |
|---|---|---|
| `set`, `status`, `remove` | Hidden entry, presence check, or deletion | required action |
| `--provider` | `gemini`, `openai` or `anthropic` | `gemini` |

Both translation commands use this precedence: `--api-key` → provider-specific
environment variable → `API_KEY` → saved Windows key. Existing overrides retain
their behavior; if an old environment key is set, saving a new key does not
override it. Saved OpenAI keys load only for its default endpoint; `custom`
providers and other `--base-url` endpoints continue using explicit keys or
environment variables. Saved keys are not automatically sent to custom hosts.
Provider requests reject HTTP redirects, so use a custom endpoint's final URL.
Gemini authentication uses a header rather than a URL query parameter, and
API/network error messages redact the key used for that request before display.

This keeps keys out of chat, command arguments and routine CLI output. It
**does not isolate secrets from an AI or other program with unrestricted access
under your Windows account**: Windows permits programs running as that user to
read their credentials. The key is also present in memory during an API request.
For stronger separation, use a restricted runner or separately secured proxy.
See [Microsoft's credential API documentation](https://learn.microsoft.com/en-us/windows/win32/api/wincred/nf-wincred-credreadw).

Saved-key commands are Windows-only, with no plaintext fallback. Other platforms
keep using environment variables or `--api-key`.

Manual check: save a key yourself, confirm input is hidden, open a new terminal
and check `status`. Run a small XML and listing preview without `--api-key`,
review the output, then remove the entry and confirm `not saved`. Ensure any key
environment overrides are absent when checking saved-key behavior.

---

## Environment variables

Environment variables remain available on all platforms. For Windows saved
credentials, use the commands above instead of putting a key in shell history.
To use an environment variable:

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
| **Scope** | `translate` reads one XML source, defaulting to `values/strings.xml`; `--source` can select another file. Output remains `strings.xml` per locale, with no automatic scan of other XML files. `store-listing` translates a separate three-field JSON listing |
| **Plurals** | Preserves source quantities and item structure; does not generate target-language plural categories. Review plural completeness for each language |
| **Overwrite** | `translate` refreshes whole files; `--missing-only` retains existing resources but does not detect source changes. `store-listing` skips existing files unless `--overwrite` is set |
| **Folder scan** | Recognizes language-first and Android `b+` locale forms, with optional trailing qualifiers. MCC/MNC-prefixed resource folders are not scanned |
| **Validation** | XML checks require source attributes, inline element order and formatting options to match; DTD/entity declarations are unsupported. Listing checks cover structure and field limits. Checks do not replace Android compilation, language review or policy review |
| **Large files** | `translate` sends one XML document per locale; no automatic batching or resume cache. Listings have bounded field lengths and may use correction requests. Incomplete provider output is rejected |
| **Network** | `translate` and `store-listing` require access to the LLM API (local `custom` providers can work offline; disable update checks for fully offline use) |
| **JDK** | `verify` requires `javac` on your PATH |

---

## Troubleshooting

| Problem | What to try |
|---|---|
| `Could not find source XML` | Check `--source`, or ensure `--res-dir` contains `values/strings.xml` |
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
