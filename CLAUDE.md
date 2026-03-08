# CLAUDE.md

See [AGENTS.md](./AGENTS.md) for the full project guide — architecture, dev workflow, release process, commit format, and non-negotiable agent behaviour rules.

## Quick reminders for Claude Code

- Always work on the `dev` branch — never commit to `master`
- Never push unless the user explicitly says to push
- After any code change: update README.md, CHANGELOG.md, bump version in both pyproject.toml and __init__.py
- Commit after completing a task — push only when asked
- Zero external dependencies — Python stdlib only
