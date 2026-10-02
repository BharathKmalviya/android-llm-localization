# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| Latest release on PyPI | Yes |
| Older releases | Best-effort — upgrade to the latest version |

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security issue, report it privately via a [GitHub Security Advisory](https://github.com/BharathKmalviya/android-llm-localization/security/advisories/new).

Include:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

You should receive a response within 7 days. I'll work with you to understand and address the issue before any public disclosure.

## Scope

This tool:

- Sends your source XML or store listing text to the selected LLM API when you run `translate` or `store-listing`
- Reads source files and writes validated translations under your selected resource/output paths
- Optionally saves provider API keys in Windows Credential Manager for the current user through `credentials set`; ordinary commands only read saved entries
- Spawns `javac` and `java` locally when you run `verify`

**Out of scope for this project:** vulnerabilities in LLM provider APIs, Android Studio, or the JDK — report those to the respective vendors.

## Safe usage

- Never commit API keys or paste them into AI chats. On Windows, `credentials set --provider gemini` uses a hidden prompt and Windows Credential Manager; other platforms retain environment-variable support
- Saved keys are protected by the Windows user boundary, not isolated from AI agents or programs with unrestricted access as that user. They exist in process memory while used. A separately secured runner/proxy is required for stronger isolation
- Saved credentials are used only for built-in provider endpoints; custom endpoints require explicit or environment keys. Argument and environment keys take precedence over saved keys
- API request errors redact the active key. Gemini uses a header instead of a query-string key; provider requests reject redirects to avoid forwarding authentication headers
- `credentials status` reports presence only; `remove` deletes the local saved entry, without revoking the provider key or deleting environment overrides
- Review translated output before shipping to production
- Use `--res-dir` carefully — the tool writes `strings.xml` files under that path
- For local models (`--provider custom`), ensure your endpoint is trusted
