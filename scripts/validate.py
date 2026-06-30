"""Validate data/fellowships.yaml: structural schema + security/integrity checks.

Security posture: parse with yaml.safe_load only; bound input size; reject
anything not matching the strict schema; then apply semantic hardening
(URL scheme allowlist, character policy, date sanity, dedupe) in Task 3.
"""
import json
import sys
from datetime import date, datetime
from pathlib import Path

import yaml
import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "data" / "schema.json"
DEFAULT_DATA_PATH = ROOT / "data" / "fellowships.yaml"

CATEGORIES = {"industry-residency", "research-safety", "academic-phd", "policy-grants"}
MAX_FILE_BYTES = 1_000_000
MAX_ENTRIES = 2000


class ValidationError(Exception):
    """Raised when the data file cannot be safely loaded."""


def _schema():
    return json.loads(SCHEMA_PATH.read_text())


def _coerce_dates(obj):
    """Recursively convert any date/datetime (PyYAML auto-parses unquoted ISO
    dates) to ISO strings, so downstream schema/string checks always see text."""
    if isinstance(obj, dict):
        return {k: _coerce_dates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_coerce_dates(v) for v in obj]
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj


def load_data(path):
    """Read + safely parse a YAML data file. Bounds size; requires a mapping.
    Dates are coerced to ISO strings so unquoted YAML dates can't break checks."""
    p = Path(path)
    raw = p.read_bytes()
    if len(raw) > MAX_FILE_BYTES:
        raise ValidationError(
            f"data file too large: {len(raw)} bytes > {MAX_FILE_BYTES}"
        )
    try:
        data = yaml.safe_load(raw.decode("utf-8"))
    except yaml.YAMLError as exc:
        raise ValidationError(f"YAML parse error: {exc}") from exc
    if not isinstance(data, dict) or "fellowships" not in data:
        raise ValidationError("top level must be a mapping with a 'fellowships' key")
    return _coerce_dates(data)


def schema_errors(data):
    """Return JSON Schema validation errors as a list of human-readable strings."""
    validator = jsonschema.Draft202012Validator(_schema())
    errors = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path) or "(root)"
        errors.append(f"schema: {loc}: {err.message}")
    return errors
