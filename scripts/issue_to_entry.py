"""Convert a GitHub issue-form body into a validated fellowship entry.

Used by the issue-to-pr workflow. The untrusted issue body arrives via the
ISSUE_BODY environment variable (never interpolated into a shell command). The
parsed entry runs through the SAME validators as a hand-written PR before it is
appended, so an issue can never inject anything a PR couldn't.
"""
import os
import re
import sys

import yaml

import validate

# Issue-form section heading -> field key. MUST match .github/ISSUE_TEMPLATE/new-fellowship.yml
# cycle/opens/deadline are CYCLE-level; entry_from_issue assembles them into cycles[].
FIELD_HEADINGS = {
    "Name": "name",
    "Organization": "organization",
    "Category": "category",
    "Application URL": "url",
    "Short description": "description",
    "Location": "location",
    "Eligibility": "eligibility",
    "Funding": "funding",
    "Duration": "duration",
    "Tags": "tags",
    "Cycle": "cycle",
    "Opens": "opens",
    "Deadline": "deadline",
}

_NO_RESPONSE = "_No response_"
_CYCLE_KEYS = ("cycle", "opens", "deadline")


def _slugify(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:64] or "fellowship"


def parse_issue_form(body):
    """Parse '### Heading\\n\\nvalue' sections into an entry dict."""
    sections = re.split(r"^###[ \t]+", body, flags=re.MULTILINE)
    parsed = {}
    for sec in sections:
        if "\n" not in sec:
            continue
        heading, _, value = sec.partition("\n")
        heading = heading.strip()
        value = value.strip()
        field = FIELD_HEADINGS.get(heading)
        if not field or value == "" or value == _NO_RESPONSE:
            continue
        if field == "tags":
            tags = [t.strip().lower() for t in re.split(r"[,\n]", value) if t.strip()]
            parsed["tags"] = tags[:8]
        else:
            parsed[field] = value
    return parsed


def entry_from_issue(body):
    """Return (entry, errors). entry is None only if nothing parseable was found.
    Cycle-level fields (cycle/opens/deadline) are assembled into a single cycle."""
    parsed = parse_issue_form(body)
    if not parsed.get("name"):
        return None, ["Could not read a 'Name' from the issue form."]

    entry = {k: v for k, v in parsed.items() if k not in _CYCLE_KEYS}
    entry.setdefault("id", _slugify(parsed["name"]))
    entry.setdefault("source", "community")
    entry.setdefault("last_verified", _today_iso())

    cycle = {
        "cycle": parsed.get("cycle") or "Upcoming",
        "deadline": parsed.get("deadline") or "Unknown",
    }
    if parsed.get("opens"):
        cycle["opens"] = parsed["opens"]
    entry["cycles"] = [cycle]

    wrapped = {"fellowships": [entry]}
    errors = validate.schema_errors(wrapped) + validate.semantic_errors(wrapped)
    return entry, errors


def _today_iso():
    from datetime import date
    return date.today().isoformat()


def append_entry(data_path, entry):
    data = validate.load_data(data_path)
    data["fellowships"].append(entry)
    with open(data_path, "w", encoding="utf-8") as fh:
        fh.write("# AI Fellowships — source of truth. See CONTRIBUTING.md.\n")
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True, default_flow_style=False)


def main(argv=None):
    body = os.environ.get("ISSUE_BODY", "")
    if not body.strip():
        print("ISSUE_BODY is empty.")
        return 1
    entry, errors = entry_from_issue(body)
    if errors:
        print("Submission rejected by validation:")
        for e in errors:
            print(f"  - {e}")
        return 1
    append_entry(str(validate.DEFAULT_DATA_PATH), entry)
    print(f"Appended entry '{entry['id']}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
