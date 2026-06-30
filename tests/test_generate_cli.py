from datetime import date
from pathlib import Path
import json
import generate


def test_inject_replaces_between_markers():
    text = f"top\n{generate.BEGIN_MARK}\nOLD\n{generate.END_MARK}\nbottom\n"
    out = generate.inject(text, "NEW")
    assert "OLD" not in out
    assert "NEW" in out
    assert out.startswith("top")
    assert out.strip().endswith("bottom")


def test_inject_missing_markers_raises():
    try:
        generate.inject("no markers here", "x")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_generate_all_writes_outputs(tmp_path):
    data = tmp_path / "f.yaml"
    data.write_text(
        "fellowships:\n"
        "  - id: a\n    name: A\n    organization: O\n    category: research-safety\n"
        "    url: https://a.example\n    description: d\n    location: Remote\n"
        "    last_verified: \"2026-06-30\"\n"
        "    cycles:\n"
        "      - cycle: \"Summer 2026\"\n        deadline: \"2026-12-01\"\n"
    )
    readme = tmp_path / "README.md"
    readme.write_text(f"# T\n{generate.BEGIN_MARK}\n{generate.END_MARK}\n")
    data_json = tmp_path / "site" / "data.json"
    generate.generate_all(str(data), str(readme), str(data_json), date(2026, 6, 30))

    body = readme.read_text()
    assert "Research & Safety" in body
    records = json.loads(data_json.read_text())
    assert records[0]["status"] == "open"
    assert records[0]["cycle"] == "Summer 2026"
