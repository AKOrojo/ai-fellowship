# Contributing

Thanks for helping keep the AI fellowships list current!

## Two ways to add a fellowship

1. **Issue form (easiest):** open a [New fellowship](../../issues/new?template=new-fellowship.yml) issue. A bot converts valid submissions into a **draft PR**; a maintainer reviews and merges.
2. **Pull request:** edit `data/fellowships.yaml`, add an entry, open a PR. **Do not edit `README.md` or `site/data.json`** — they are generated.

## Entry fields

| Field | Required | Rule |
| --- | --- | --- |
| `id` | yes | lowercase slug `[a-z0-9-]`, unique |
| `name` | yes | ≤120 chars, no HTML |
| `organization` | yes | ≤120 chars |
| `category` | yes | `industry-residency` \| `research-safety` \| `academic-phd` \| `policy-grants` |
| `url` | yes | **https:// only**, ≤500 chars |
| `description` | yes | ≤500 chars, no HTML |
| `location` | yes | ≤80 chars |
| `cycles` | yes | list of 1+ cohorts; each cycle: `cycle` (label ≤60, e.g. "Summer 2026", unique within the fellowship) + `deadline` (`YYYY-MM-DD`, `Rolling`, `Closed`, or `Unknown`), and optional `opens` (`YYYY-MM-DD` or `Unknown`) |
| `last_verified` | yes | `YYYY-MM-DD` (quote all dates) |
| `eligibility`, `funding`, `duration`, `tags`, `source` | no | see schema |

## Validate locally

```bash
uv sync
uv run python scripts/validate.py      # must print OK
uv run pytest -q             # all tests pass
uv run python scripts/generate.py      # refresh README + site/data.json
```

CI runs the same checks. PRs cannot merge until validation passes **and** a maintainer approves.
