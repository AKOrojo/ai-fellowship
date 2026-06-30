from datetime import date
import json
import generate


def test_derive_status_rolling():
    assert generate.derive_status("Unknown", "Rolling", date(2026, 6, 30)) == "rolling"


def test_derive_status_closed():
    assert generate.derive_status("Unknown", "2026-01-01", date(2026, 6, 30)) == "closed"


def test_derive_status_open():
    assert generate.derive_status("Unknown", "2026-12-01", date(2026, 6, 30)) == "open"


def test_derive_status_upcoming():
    assert generate.derive_status("2026-09-01", "2026-12-01", date(2026, 6, 30)) == "upcoming"


def test_escape_md_pipes_and_newlines():
    assert generate.escape_md("a|b\nc") == "a\\|b c"


def test_escape_md_angle_brackets():
    assert generate.escape_md("<b>") == "&lt;b&gt;"


def sample_entry():
    return {
        "id": "x", "name": "X", "organization": "O", "category": "research-safety",
        "url": "https://x.example", "description": "d", "location": "Remote",
        "last_verified": "2026-06-30",
        "cycles": [
            {"cycle": "Summer 2026", "deadline": "2026-12-01"},
            {"cycle": "Winter 2026", "deadline": "2026-01-01"},
        ],
    }


def test_build_site_records_flattens_cycles():
    recs = generate.build_site_records([sample_entry()], date(2026, 6, 30))
    assert len(recs) == 2  # one record per cycle
    by_cycle = {r["cycle"] for r in recs}
    assert by_cycle == {"Summer 2026", "Winter 2026"}
    statuses = {r["cycle"]: r["status"] for r in recs}
    assert statuses["Summer 2026"] == "open"
    assert statuses["Winter 2026"] == "closed"
    assert "cycles" not in recs[0]  # nested list dropped from flattened record
    json.loads(json.dumps(recs))  # JSON-serializable


def test_render_tables_groups_escapes_and_shows_cycle():
    entry = sample_entry()
    entry["name"] = "Pipe|Name"
    md = generate.render_tables([entry], date(2026, 6, 30))
    assert "Research & Safety" in md
    assert "Pipe\\|Name" in md
    assert "Summer 2026" in md
    assert "Winter 2026" in md
    assert "Cycle" in md  # header column present
    assert "https://x.example" in md


def test_derive_status_closed_literal():
    # A cohort known to be closed but without an exact past date.
    assert generate.derive_status("Unknown", "Closed", date(2026, 6, 30)) == "closed"


def test_derive_status_closed_on_deadline_day():
    # The deadline day itself counts as closed (today >= deadline).
    assert generate.derive_status("Unknown", "2026-06-30", date(2026, 6, 30)) == "closed"
    assert generate.derive_status("Unknown", "2026-07-01", date(2026, 6, 30)) == "open"
