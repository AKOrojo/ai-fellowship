import json
import yaml
import jsonschema
from conftest import DATA, SCHEMA


def load_schema():
    return json.loads(SCHEMA.read_text())


def load_data():
    return yaml.safe_load(DATA.read_text())


def test_seed_data_matches_schema():
    jsonschema.validate(load_data(), load_schema())


def test_schema_rejects_unknown_key():
    schema = load_schema()
    bad = {"fellowships": [{
        "id": "x", "name": "X", "organization": "Y",
        "category": "research-safety", "url": "https://x.com",
        "description": "d", "location": "Remote",
        "deadline": "Rolling", "last_verified": "2026-06-30",
        "surprise": "boom",
    }]}
    try:
        jsonschema.validate(bad, schema)
        assert False, "expected ValidationError for unknown key"
    except jsonschema.ValidationError:
        pass


def test_schema_rejects_bad_category():
    schema = load_schema()
    bad = {"fellowships": [{
        "id": "x", "name": "X", "organization": "Y",
        "category": "internships", "url": "https://x.com",
        "description": "d", "location": "Remote",
        "deadline": "Rolling", "last_verified": "2026-06-30",
    }]}
    try:
        jsonschema.validate(bad, schema)
        assert False, "expected ValidationError for bad category"
    except jsonschema.ValidationError:
        pass
