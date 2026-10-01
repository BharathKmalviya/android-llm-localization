# CLI improvement plan

The CLI stays small, uses Python 3.8+ and the standard library, and keeps the
existing `translate` -> `fix` -> `verify` workflow. Normal translation continues
to refresh entire locale files; preservation and previews are opt-in.

## Current implementation scope

- [x] Validate XML, resource coverage, attributes, inline markup, protected
  content and format arguments before saving.
- [x] Save atomically so rejected responses and failed writes preserve files.
- [x] Share resource validation with `verify`, retaining Java runtime checks.
- [x] Detect locale folders correctly and reject invalid language paths.
- [x] Add `--missing-only` and `--dry-run`, without a cache or configuration system.
- [x] Report per-locale outcomes and nonzero exits for failures.
- [x] Reject truncated provider responses and handle text response blocks.
- [x] Use only the latest general-purpose text-model lineup for defaults and
  fallbacks, checked against official docs on 2026-10-02; preserve custom endpoints
  and explicit model selection. No older-generation automatic fallbacks.
- [x] Synchronize user docs, version and local CLI guidance; verify and commit on dev.
- [x] Add optional interactive release notices using a 24-hour user cache and a
  nonblocking PyPI lookup; keep CI, pipes, help/version output and offline failures
  silent, with an environment opt-out and no automatic installation.
- [x] Add explicit Windows user PATH setup and a Python module launcher; keep
  pip installation and ordinary commands free of PATH changes.
- [x] Expand root and per-command help with every command, defaults, behavior,
  examples and Python launcher instructions; show help when no command is given.

## Follow-up scope

Glossaries and per-resource context, bounded batches/rate-limit backoff, source
hashes for changed-resource detection, and translation across multiple XML files.
Plural-category expansion requires a separate design: copying English categories
does not provide complete localization for every target language. No IDE plugin,
database, background service, third-party dependency or automatic publishing is
needed for these improvements.

## Compatibility and verification

- Existing command names, provider flags, environment variables and local-model
  endpoints remain supported. `--model` continues to disable fallback.
- `--missing-only` retains existing resource content; it does not infer source
  changes. `--dry-run` may call the provider but never creates folders/files.
- Failure exits are an intentional correction for CI: 0 succeeds, 1 fails.
- Verify with local CLI fixtures and simulated API replies, including invalid
  XML, missing/extra keys, duplicate names, protected content, argument reordering,
  namespaces, partial failures, missing-only preservation and read-only previews.
- Live API access and natural language quality need a real-provider manual run;
  structural checks do not prove translation quality or Android layout behavior.

## Local verification results (2026-10-02)

- 59 local checks passed using Python 3.14.7 and Java 21 on Windows. Fixtures
  covered successful and rejected CLI output, missing-only preservation,
  previews, provider text/truncation handling, fallbacks, fixer behavior,
  atomic-write failures, old Namespace callers and resource validation.
- Python modules parse with Python 3.8 grammar; execution on Python 3.8 and
  macOS/Linux remains unverified.
- The 1.1.0 wheel built and installed into an isolated local target. Its CLI
  and Java verifier ran, Java source was bundled, and metadata has no runtime
  dependencies. Local fixtures and tooling are excluded from the wheel.
- The 1.1.1 catalog update passed CLI version/models/help smoke checks and 11
  mocked model-selection/version checks: exact latest-only lists, fallback order,
  pinned selections, failure handling and synchronized version metadata.
- The 1.1.2 update notifier passed 22 local checks and the 33 CLI fixture checks.
  Its wheel/source archive built, installed CLI/Java smoke checks passed, and an
  installed-package notice example confirmed stderr instructions and unchanged
  stdout. Live PyPI metadata lookup succeeded; release notices were simulated.
- The 1.1.3 Windows setup/module launcher passed 26 checks, the 22 update-notice
  checks and the 33 CLI fixture checks. Registry writes were mocked; actual
  Windows setup confirmed the already configured Scripts directory without
  writing it again. Eight help/version smoke checks covered all five commands
  and bare invocation, with no update lookup or PATH writes.
- Provider replies were simulated. No paid translation requests, native-speaker
  accuracy assessment, Android builds or device-layout checks were performed.
- Prepared and committed on `dev`; publication remains a separate requested step.

## Manual real-provider check

With your provider key set as documented in README, use a disposable resource
copy that includes placeholders, inline markup, non-translatable strings and a
partially translated locale:

```bash
android-localise translate --res-dir path/to/res --languages hi,es --dry-run
android-localise translate --res-dir path/to/res --languages hi,es --missing-only
android-localise fix --res-dir path/to/res
android-localise verify --res-dir path/to/res
```

Check that the preview creates no files, approved text is retained, new resources
are translated naturally, placeholders still match, and your Android build passes.
Normal `translate` intentionally refreshes existing resources; test that mode on
another disposable copy. Review language and layout in your application before
using translations in production. Arrays/plurals in `strings.xml` are validated,
but `fix` still repairs only strings and plural categories are not expanded.
