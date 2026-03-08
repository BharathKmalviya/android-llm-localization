# Changelog

All notable changes to this project will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/).

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

[1.0.0]: https://github.com/BharathKmalviya/android-llm-localization/releases/tag/v1.0.0
