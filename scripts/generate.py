"""Generate the README table and site/data.json from the validated data file.

Refuses to run unless validate.validate_file passes, so generated artifacts can
never contain content that failed the security checks. All values placed into
Markdown are escaped; data.json is emitted via json.dumps (no concatenation).
"""
import json
import sys
from datetime import date
from pathlib import Path

import validate

ROOT = Path(__file__).resolve().parent.parent

CATEGORY_ORDER = ["industry-residency", "research-safety", "academic-phd", "policy-grants"]
CATEGORY_TITLES = {
    "industry-residency": "Industry AI Residencies",
    "research-safety": "Research & Safety Fellowships",
    "academic-phd": "Academic & PhD Fellowships",
    "policy-grants": "Policy, Nonprofit & Grants",
}
STATUS_BADGE = {"open": "🟢 Open", "upcoming": "🔵 Upcoming", "closed": "🔴 Closed", "rolling": "🟡 Rolling"}


def derive_status(opens, deadline, today):
    if deadline == "Rolling":
        return "rolling"
    if deadline == "Closed":
        return "closed"
    if deadline and deadline not in ("Unknown", "Closed"):
        d = date.fromisoformat(deadline)
        if today >= d:  # deadline day or earlier counts as closed
            return "closed"
    if opens and opens not in ("Unknown", None):
        try:
            if today < date.fromisoformat(opens):
                return "upcoming"
        except ValueError:
            pass
    return "open"


def escape_md(s):
    s = str(s)
    s = s.replace("<", "&lt;").replace(">", "&gt;")
    s = s.replace("|", "\\|")
    s = s.replace("\r", " ").replace("\n", " ")
    return s


def _deadline_sort_key(cycle):
    d = cycle.get("deadline", "")
    # Real dates sort first (ascending); Rolling/Unknown go last.
    if d in ("Rolling", "Unknown", ""):
        return (1, "9999-12-31")
    return (0, d)


def build_site_records(entries, today):
    """Flatten cycles: emit one record per (fellowship, cycle) with derived status."""
    records = []
    for e in entries:
        program = {k: v for k, v in e.items() if k != "cycles"}
        for c in e.get("cycles", []):
            rec = dict(program)
            rec["cycle"] = c.get("cycle", "")
            rec["opens"] = c.get("opens", "Unknown")
            rec["deadline"] = c.get("deadline", "")
            rec["status"] = derive_status(c.get("opens"), c.get("deadline", ""), today)
            records.append(rec)
    return records


def render_tables(entries, today):
    by_cat = {c: [] for c in CATEGORY_ORDER}
    for e in entries:
        for c in e.get("cycles", []):
            by_cat.setdefault(e["category"], []).append((e, c))

    lines = []
    for cat in CATEGORY_ORDER:
        items = sorted(by_cat.get(cat, []), key=lambda pair: _deadline_sort_key(pair[1]))
        if not items:
            continue
        lines.append(f"### {CATEGORY_TITLES[cat]}")
        lines.append("")
        lines.append("| Fellowship | Organization | Cycle | Deadline | Status | Location |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for e, c in items:
            status = derive_status(c.get("opens"), c.get("deadline", ""), today)
            name = f"[{escape_md(e['name'])}]({e['url']})"
            lines.append(
                f"| {name} | {escape_md(e['organization'])} | {escape_md(c.get('cycle', ''))} "
                f"| {escape_md(c.get('deadline', ''))} | {STATUS_BADGE[status]} | {escape_md(e.get('location', ''))} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


BEGIN_MARK = "<!-- BEGIN AUTOGEN -->"
END_MARK = "<!-- END AUTOGEN -->"

DEFAULT_README = ROOT / "README.md"
DEFAULT_DATA_JSON = ROOT / "site" / "data.json"


def inject(readme_text, block):
    if BEGIN_MARK not in readme_text or END_MARK not in readme_text:
        raise ValueError("README is missing the AUTOGEN markers")
    pre = readme_text.split(BEGIN_MARK)[0]
    post = readme_text.split(END_MARK)[1]
    return f"{pre}{BEGIN_MARK}\n{block}\n{END_MARK}{post}"


def generate_all(data_path, readme_path, data_json_path, today):
    data = validate.load_data(data_path)
    entries = data["fellowships"]

    table_md = render_tables(entries, today)
    readme = Path(readme_path).read_text()
    Path(readme_path).write_text(inject(readme, table_md))

    records = build_site_records(entries, today)
    out = Path(data_json_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(records, indent=2, ensure_ascii=True, sort_keys=True) + "\n")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    data_path = argv[0] if argv else str(validate.DEFAULT_DATA_PATH)
    errors = validate.validate_file(data_path)
    if errors:
        print("Refusing to generate — data file is invalid:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    generate_all(data_path, str(DEFAULT_README), str(DEFAULT_DATA_JSON), date.today())
    print("Generated README table and site/data.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
