# Maintainers & repo setup

## One-time GitHub settings (do these after first push)

**Branch protection** (Settings → Branches → add rule for `main`):
- Require a pull request before merging; require **at least 1 approval**.
- Require status checks to pass: select the **Validate** check.
- Require branches to be up to date before merging.
- Do not allow force pushes or deletions.

**Actions permissions** (Settings → Actions → General):
- Set **Workflow permissions** to *Read repository contents and packages* (read-only default). Individual workflows request more via their `permissions:` blocks.

**Pages** (Settings → Pages):
- Source: **GitHub Actions**.

## Reviewing submissions
- Bot-opened PRs are **draft**; CI must be green and you must verify the official link before marking ready and merging. Nothing merges automatically.
