import pytest
import validate


GOOD = {"fellowships": [{
    "id": "a", "name": "A", "organization": "Org",
    "category": "research-safety", "url": "https://a.example",
    "description": "desc", "location": "Remote",
    "cycles": [{"cycle": "2026", "deadline": "Rolling"}],
    "last_verified": "2026-06-30",
}]}


def test_load_data_reads_yaml(tmp_path):
    f = tmp_path / "d.yaml"
    f.write_text("fellowships: []\n")
    assert validate.load_data(str(f)) == {"fellowships": []}


def test_load_data_coerces_unquoted_dates(tmp_path):
    # PyYAML parses unquoted ISO dates as datetime.date; load_data must coerce
    # them back to ISO strings so the schema (type: string) and date checks hold.
    f = tmp_path / "d.yaml"
    f.write_text("fellowships:\n- last_verified: 2026-06-30\n")
    data = validate.load_data(str(f))
    assert data["fellowships"][0]["last_verified"] == "2026-06-30"
    assert isinstance(data["fellowships"][0]["last_verified"], str)


def test_load_data_rejects_oversize(tmp_path):
    f = tmp_path / "d.yaml"
    f.write_bytes(b"fellowships: []\n" + b"#" * (validate.MAX_FILE_BYTES + 1))
    with pytest.raises(validate.ValidationError):
        validate.load_data(str(f))


def test_load_data_rejects_non_mapping(tmp_path):
    f = tmp_path / "d.yaml"
    f.write_text("- just\n- a list\n")
    with pytest.raises(validate.ValidationError):
        validate.load_data(str(f))


def test_schema_errors_empty_for_good():
    assert validate.schema_errors(GOOD) == []


def test_schema_errors_flags_missing_required():
    bad = {"fellowships": [{"id": "a"}]}
    assert validate.schema_errors(bad) != []
