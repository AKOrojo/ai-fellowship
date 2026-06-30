import yaml
import issue_to_entry as i2e


FORM = """### Name

MATS

### Organization

ML Alignment & Theory Scholars

### Category

research-safety

### Application URL

https://www.matsprogram.org

### Short description

Independent AI safety research mentorship program.

### Location

Berkeley, CA

### Cycle

Summer 2026

### Deadline

2026-09-01

### Opens

_No response_

### Eligibility

_No response_

### Tags

safety, mentorship
"""


def test_parse_maps_headings():
    parsed = i2e.parse_issue_form(FORM)
    assert parsed["name"] == "MATS"
    assert parsed["category"] == "research-safety"
    assert parsed["url"] == "https://www.matsprogram.org"
    assert parsed["cycle"] == "Summer 2026"
    assert parsed["deadline"] == "2026-09-01"
    assert "opens" not in parsed  # _No response_ omitted
    assert "eligibility" not in parsed  # _No response_ omitted
    assert parsed["tags"] == ["safety", "mentorship"]


def test_entry_from_issue_valid():
    entry, errors = i2e.entry_from_issue(FORM)
    assert errors == []
    assert entry["id"] == "mats"
    assert entry["source"] == "community"
    assert entry["cycles"] == [{"cycle": "Summer 2026", "deadline": "2026-09-01"}]


def test_entry_from_issue_rejects_xss():
    bad = FORM.replace("MATS", "<script>alert(1)</script>")
    entry, errors = i2e.entry_from_issue(bad)
    assert errors  # name fails the character policy


def test_entry_from_issue_rejects_bad_url():
    bad = FORM.replace("https://www.matsprogram.org", "javascript:alert(1)")
    entry, errors = i2e.entry_from_issue(bad)
    assert errors


def test_append_entry_roundtrips(tmp_path):
    f = tmp_path / "f.yaml"
    f.write_text("fellowships: []\n")
    entry, errors = i2e.entry_from_issue(FORM)
    assert errors == []
    i2e.append_entry(str(f), entry)
    data = yaml.safe_load(f.read_text())
    assert data["fellowships"][0]["id"] == "mats"
    assert data["fellowships"][0]["cycles"][0]["cycle"] == "Summer 2026"
