import json
import yaml
import jsonschema
import pytest
from conftest import DATA, SCHEMA


def load_schema():
    return json.loads(SCHEMA.read_text())


def load_data():
    return yaml.safe_load(DATA.read_text())


def good_entry(**over):
    e = {
        "id": "x", "name": "X", "organization": "Y",
        "category": "research-safety", "url": "https://x.com",
        "description": "d", "location": "Remote",
        "last_verified": "2026-06-30",
        "cycles": [{"cycle": "2026 Cohort", "deadline": "Rolling"}],
    }
    e.update(over)
    return e


def validate_entry(entry):
    jsonschema.validate({"fellowships": [entry]}, load_schema())


def test_seed_data_matches_schema():
    jsonschema.validate(load_data(), load_schema())


def test_good_entry_validates():
    validate_entry(good_entry())


def test_schema_rejects_unknown_key():
    with pytest.raises(jsonschema.ValidationError):
        validate_entry(good_entry(surprise="boom"))


def test_schema_rejects_bad_category():
    with pytest.raises(jsonschema.ValidationError):
        validate_entry(good_entry(category="internships"))


def test_schema_requires_cycles():
    e = good_entry()
    del e["cycles"]
    with pytest.raises(jsonschema.ValidationError):
        validate_entry(e)


def test_schema_rejects_empty_cycles():
    with pytest.raises(jsonschema.ValidationError):
        validate_entry(good_entry(cycles=[]))


def test_cycle_requires_deadline():
    with pytest.raises(jsonschema.ValidationError):
        validate_entry(good_entry(cycles=[{"cycle": "2026 Cohort"}]))


def test_cycle_rejects_unknown_key():
    with pytest.raises(jsonschema.ValidationError):
        validate_entry(good_entry(cycles=[{"cycle": "2026", "deadline": "Rolling", "x": 1}]))
