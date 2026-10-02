# Changelog

All notable changes to this project will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [1.2.0] - 2026-10-02

### Added
- `store-listing` translates a UTF-8 JSON Google Play app name, short description and full description into selected Play locales, using existing providers, key resolution, pinned models, fallback and timeout behavior.
- Validates all three required fields against 30/80/4,000-character limits and rejects invalid JSON, duplicate/extra/missing keys, blank fields, control characters and multiline names/short descriptions. Invalid model output receives up to two correction requests with feedback; rejected output leaves existing files intact.
- Atomic per-locale JSON saves, field character counts, per-locale results, nonzero failure exits, and source/output collision protection. Existing valid listings skip by default; `--overwrite` refreshes them, `--dry-run` previews diffs, and `--keep-app-name` preserves the source name exactly.
- Store-listing prompts incorporate the supplied metadata, Help Centre, programme-policy and advance-notice links with accurate-description and short-description guidance. They preserve factual disclosures and discourage invented claims, ranking/promotion language, keyword stuffing and misleading affiliations. Policy guidance remains a prompt instruction and manual review responsibility; the CLI does not upload listings or send advance notice.

---

## [1.1.3] - 2026-10-02

### Added
- `setup-path` detects this Python's installed Windows Scripts folder and adds it to user PATH without administrator access, preserving existing entries and registry type and avoiding duplicates. Virtual environments are left to normal activation.
- `python -m android_localisation` runs the full CLI when the console script is not yet on PATH, including the one-time setup command. Installation itself and ordinary commands do not modify PATH.

### Changed
- Root help now lists all five commands with workflow examples, Python launcher instructions and key/update environment variables. Each command's help explains its scope, defaults, examples and relevant failure behavior; verification no longer claims to guarantee app runtime safety.
- Running the unified CLI without arguments prints help and exits successfully without network requests or PATH changes. Direct translation-module flag descriptions are synchronized with the unified CLI.

---

## [1.1.2] - 2026-10-02

### Added
- Best-effort update notices for interactive CLI commands, using PyPI's stable release metadata and a 24-hour user cache. Notices show the upgrade command on stderr without waiting for the background lookup or installing updates.
- `ANDROID_LOCALISE_NO_UPDATE_CHECK=1` disables checks. CI, pipes, redirected output and help/version requests skip them; network/cache failures do not affect command results.

---

## [1.1.1] - 2026-10-02

### Changed
- Automatic model selection now uses only the latest general-purpose text-model lineup verified against official catalogs on 2026-10-02. Removed older-generation Gemini, GPT-5 and Haiku 4.5 entries.
- Gemini retains `gemini-3.8-flash` with no fallback. OpenAI retains `gpt-6-luna`, with `gpt-6.1-sol` and `gpt-6-astra` fallbacks. Anthropic now defaults to `claude-sonnet-5-5`, with `claude-opus-5-5` as its fallback.
- Documented higher-cost fallback tiers and the bundled catalog. Explicit `--model` choices and custom/local endpoints remain supported.

---

## [1.1.0] - 2026-10-02

### Added
- Shared XML/resource validation before saving and during `verify`: malformed XML, duplicate/missing/unexpected resources, changed attributes/markup, protected content, control escapes and dropped/changed format arguments are reported.
- Opt-in `--missing-only` preserves existing resource text and requests absent resources; complete locales skip API calls. No source-history cache or new default overwrite policy.
- Opt-in `--dry-run` generates a validated diff without writing files or creating directories; normal API charges still apply.
- Per-locale translation summary and nonzero exits for setup/API/validation/save failures, including partial failures.

### Fixed
- Validated locale detection skips configuration-only folders; explicit languages are checked before filesystem or API work.
- Atomic translation/fix writes preserve existing files when output is rejected or replacement fails.
- Namespace declarations are retained; protected values and inline markup/attributes cannot be silently changed by translation.
- Java verifier parses UTF-8 XML rather than regex matching and checks string-array/plural items, date/time formats and relative argument indices. Compilation uses a temporary directory rather than writing into the installed package.
- `fix` retains protected string values and inline markup attributes, supports single-quoted names, checks XML and reports failures.
- Incomplete/truncated provider responses are rejected; Gemini text parts and Anthropic text blocks are handled without treating thinking content as translated XML.
- Corrected README claims about automatic XML validity, fixer coverage and runtime safety.
- UTF-8 console/pipe output avoids Windows legacy-encoding crashes on status symbols and localized text.

### Changed
- Stable text-model catalog refreshed from official provider documentation on 2026-10-02: Gemini defaults to `gemini-3.8-flash` (fallbacks `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`); OpenAI defaults to `gpt-6-luna` (fallbacks `gpt-5.6-luna`, `gpt-5.4-mini`). Anthropic retains fastest-tier `claude-haiku-4-5`, with current `claude-sonnet-5-5` and `claude-opus-5-5` fallbacks. Explicit model selection/custom endpoints remain supported.
- Anthropic output allowance increased from 4,096 to 16,384 tokens; incomplete responses still fail safely.
- Existing commands and whole-file translation defaults remain; new preservation/preview behavior is optional. Resource verification is stricter than Android's fallback for missing translations.

---

## [1.0.7] - Unreleased (included in 1.1.0)

### Fixed
- **`cli.py` `--timeout` help drift**: attempt count now derives from `MAX_TIMEOUT_RETRIES` instead of a hard-coded "3 attempts"
- **`clean_xml_response()` single-quoted `xmlns`**: xmlns stripping now handles both `"` and `'` attribute values

---

## [1.0.6] - 2026-06-12

### Fixed
- **Timeout retries missed via `URLError`**: `urllib.request.urlopen()` often wraps `socket.timeout` in `urllib.error.URLError` — those are now retried like direct `TimeoutError`
- **Translation prompt dropping `formatted="false"`**: prompt now preserves the `formatted` attribute so literal `%` strings are not corrupted by `fix`
- **`clean_xml_response()` over-stripping `<resources>` attributes**: only `xmlns` declarations are removed now, not other attributes like `tools:ignore`
- **`fix.py` missing `formatted = "false"` variants**: detection now handles whitespace around `=` (consistent with the Java verifier)

### Changed
- README/CLI `--timeout` docs clarified: up to 3 attempts on timeout (2 retries)

---

## [1.0.5] - 2026-06-12

### Fixed
- **API timeout crash** ([#3](https://github.com/BharathKmalviya/android-llm-localization/issues/3)): `TimeoutError` and network errors no longer crash the CLI — they are caught, reported, and the locale is skipped
- Large `strings.xml` files timing out at 60s — default API timeout increased to 180s (3 minutes) with automatic retries (up to 3 attempts) on timeout

### Added
- `--timeout` flag on `translate` to configure per-request API timeout in seconds (default: 180)

### Changed
- Default models updated to latest fast tiers: `gemini-3.5-flash`, `gpt-5.4-mini`, `claude-haiku-4-5` (with newer fallbacks per provider)

---

## [1.0.4] - 2026-03-09

### Fixed
- **Verifier false positives**: `%%` (escaped percent) in strings like `%1$d%% completed` was misread as a `%c` format specifier — now stripped before regex scanning
- **Verifier type mismatch crashes**: type-aware argument building now correctly maps `%f`/`%e`/`%g` → Double, `%c` → Character, `%b` → Boolean, supporting any number of format args
- **Verifier `formatted="false"` strings**: strings with this attribute are now skipped — their `%` signs are literal, not format specifiers
- **`translate.py` NameError**: missing `import re` caused a crash in `clean_xml_response()` when stripping xmlns attributes from `<resources>` tag
- **`fix.py` corrupting `formatted="false"` strings**: the fixer now skips strings marked `formatted="false"` — previously it escaped their literal `%` signs to `%%`, corrupting the output

### Changed
- Translation prompt now explicitly forbids xmlns namespaces in `<resources>`, requires `\'` apostrophe escaping, and forbids CDATA
- `clean_xml_response()` strips any xmlns attributes from `<resources>` tag as a safety net

---

## [1.0.3] - 2026-03-08

### Fixed
- Translation failures now show exactly why they failed — API error, missing `<resources>` tag, or missing `</resources>` closing tag — with a response preview so you can debug without guessing

---

## [1.0.2] - 2026-03-08

### Added
- `--languages` flag: specify comma-separated language codes (e.g. `hi,es,fr,de`) to auto-create `values-<lang>/` folders and translate without any manual setup
- Auto-create `strings.xml` inside existing empty locale folders — no longer need to manually create the file before translating
- Clear log output: shows whether a file is being created (new) or updated (existing) per language

### Changed
- If no locale directories are found and `--languages` is not set, shows a helpful error message with an example command instead of silently exiting

---

## [1.0.1] - 2026-03-08

### Fixed
- Fully automated release pipeline via GitHub Actions (no local build or manual tagging needed)
- Auto-detect version bump on push to master, auto-tag, build, publish to PyPI, and create GitHub Release

---

## [1.0.0] - 2026-03-08

### Added
- `android-localise translate` — translate `strings.xml` into all locale directories using LLMs
- `android-localise fix` — fix XML escaping issues (apostrophes, quotes, `%` signs) in translated files
- `android-localise verify` — compile and run a Java verifier to catch format specifier crashes before they happen
- `android-localise models` — list all available models and fallbacks per provider
- Support for **Gemini**, **OpenAI**, **Anthropic (Claude)**, and any **custom OpenAI-compatible endpoint** (Ollama, LM Studio, etc.)
- Automatic model fallback chain — if the default model is unavailable, retries with the next in the list
- `--model` flag accepts any free-form model name for full control
- `--app-context` flag for better context-aware translations
- 60-second timeout on all API calls
- Zero external dependencies — uses Python stdlib only

[1.0.4]: https://github.com/BharathKmalviya/android-llm-localization/releases/tag/v1.0.4
[1.0.3]: https://github.com/BharathKmalviya/android-llm-localization/releases/tag/v1.0.3
[1.0.2]: https://github.com/BharathKmalviya/android-llm-localization/releases/tag/v1.0.2
[1.0.1]: https://github.com/BharathKmalviya/android-llm-localization/releases/tag/v1.0.1
[1.0.0]: https://github.com/BharathKmalviya/android-llm-localization/releases/tag/v1.0.0
