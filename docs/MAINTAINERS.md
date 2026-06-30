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

## Notes on automation under branch protection

- `.github/CODEOWNERS` is set to `@AKOrojo`. Update it if the maintainer changes.
- `build-deploy.yml` regenerates the README and commits it back to `main`. If you enable "Require a pull request before merging" on `main`, that direct push is rejected; the workflow treats this as non-fatal (a warning) and the Pages site still deploys with fresh data (data.json ships in the Pages artifact, not via commit). To keep the README table auto-updating on `main` under branch protection, allow the `github-actions` bot to bypass the rule, or accept that the README table refreshes only when a PR includes regenerated content.
