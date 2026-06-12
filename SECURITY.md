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

You should receive a response within 7 days. We will work with you to understand and address the issue before any public disclosure.

## Scope

This tool:

- Sends your `strings.xml` content to third-party LLM APIs when you run `translate`
- Reads and writes files under the `--res-dir` path you specify
- Spawns `javac` and `java` locally when you run `verify`

**Out of scope for this project:** vulnerabilities in LLM provider APIs, Android Studio, or the JDK — report those to the respective vendors.

## Safe usage

- Never commit API keys — use environment variables or local shell config
- Review translated output before shipping to production
- Use `--res-dir` carefully — the tool writes `strings.xml` files under that path
- For local models (`--provider custom`), ensure your endpoint is trusted
