# Security Policy

This project accepts untrusted contributions, so input validation and CI
hardening are core to its design.

## Reporting a vulnerability

Please **do not** open a public issue for security problems. Use GitHub's
[private vulnerability reporting](../../security/advisories/new) for this repo,
or contact the maintainers listed in `docs/MAINTAINERS.md`.

We aim to acknowledge reports within 7 days.

## Hardening summary

- Data is parsed with `yaml.safe_load` and validated against a strict JSON Schema
  (`additionalProperties: false`) plus semantic checks (https-only URLs,
  length/character caps, dedupe).
- Generated Markdown is escaped; the website renders via `textContent` only and
  ships a strict Content-Security-Policy.
- Workflows are least-privilege, never use `pull_request_target`, pin all actions
  to commit SHAs, and pass untrusted issue/PR data only through environment
  variables.
