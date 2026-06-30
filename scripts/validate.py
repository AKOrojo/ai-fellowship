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
    for err in sorted(validator.iter_errors(data), key=lambda e: [str(p) for p in e.path]):
        loc = "/".join(str(p) for p in err.path) or "(root)"
        errors.append(f"schema: {loc}: {err.message}")
    return errors


import re
from urllib.parse import urlsplit

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_DEADLINE_LITERALS = {"Rolling", "Unknown", "Closed"}
_OPENS_LITERALS = {"Unknown"}


def is_iso_date(s):
    if not isinstance(s, str) or not _DATE_RE.match(s):
        return False
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


def is_safe_text(s, max_len):
    if not isinstance(s, str) or len(s) > max_len:
        return False
    if "<" in s or ">" in s:
        return False
    if _CONTROL_RE.search(s):
        return False
    return True


def is_safe_url(url):
    if not isinstance(url, str) or len(url) > 500:
        return False
    if _CONTROL_RE.search(url) or any(ch in url for ch in " \t\r\n|"):
        return False
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    if parts.scheme != "https":
        return False
    if not parts.netloc or "@" in parts.netloc:
        return False
    return True


def _date_field_ok(value, literals):
    return value in literals or is_iso_date(value)


def _cycle_errors(eid, cycles):
    """Validate each cohort/cycle: safe unique label, valid opens/deadline."""
    errs = []
    if not isinstance(cycles, list):
        return [f"semantic: {eid}: cycles must be a list"]
    seen_labels = set()
    for j, c in enumerate(cycles):
        if not isinstance(c, dict):
            errs.append(f"semantic: {eid}: cycle {j} is not a mapping")
            continue
        label = c.get("cycle", "")
        if not isinstance(label, str) or not label.strip() or not is_safe_text(label, 60):
            errs.append(f"semantic: {eid}: cycle {j} label is missing/unsafe/over-long")
        else:
            key = label.strip().lower()
            if key in seen_labels:
                errs.append(f"semantic: {eid}: duplicate cycle label '{label}'")
            seen_labels.add(key)
        if not _date_field_ok(c.get("deadline", ""), _DEADLINE_LITERALS):
            errs.append(f"semantic: {eid}: cycle '{label}' deadline must be YYYY-MM-DD, 'Rolling', or 'Unknown'")
        if "opens" in c and not _date_field_ok(c["opens"], _OPENS_LITERALS):
            errs.append(f"semantic: {eid}: cycle '{label}' opens must be YYYY-MM-DD or 'Unknown'")
    return errs


def semantic_errors(data):
    """Per-entry hardening + dedupe. Assumes schema already passed but is defensive."""
    errors = []
    entries = data.get("fellowships", [])
    if not isinstance(entries, list):
        return ["semantic: 'fellowships' must be a list"]
    if len(entries) > MAX_ENTRIES:
        errors.append(f"semantic: too many entries ({len(entries)} > {MAX_ENTRIES})")

    seen_ids, seen_urls, seen_nameorg = {}, {}, {}
    text_caps = {
        "name": 120, "organization": 120, "description": 500,
        "location": 80, "eligibility": 200, "funding": 120, "duration": 80,
    }
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            errors.append(f"semantic: entry {i} is not a mapping")
            continue
        eid = e.get("id", f"<index {i}>")

        if e.get("category") not in CATEGORIES:
            errors.append(f"semantic: {eid}: invalid category {e.get('category')!r}")

        for field, cap in text_caps.items():
            if field in e and not is_safe_text(e[field], cap):
                errors.append(f"semantic: {eid}: field '{field}' has unsafe or over-long text")

        if not is_safe_url(e.get("url", "")):
            errors.append(f"semantic: {eid}: url must be a plain https:// URL")

        if "source" in e and e["source"] != "community" and not is_safe_url(e["source"]):
            errors.append(f"semantic: {eid}: source must be 'community' or an https:// URL")

        if not is_iso_date(e.get("last_verified", "")):
            errors.append(f"semantic: {eid}: last_verified must be a real YYYY-MM-DD date")

        errors += _cycle_errors(eid, e.get("cycles", []))

        if "id" in e:
            if e["id"] in seen_ids:
                errors.append(f"semantic: duplicate id '{e['id']}'")
            seen_ids[e["id"]] = i
        url = e.get("url")
        if url:
            key = url.rstrip("/").lower()
            if key in seen_urls:
                errors.append(f"semantic: duplicate url '{url}'")
            seen_urls[key] = i
        no = (str(e.get("name", "")).strip().lower(), str(e.get("organization", "")).strip().lower())
        if no != ("", "") and no in seen_nameorg:
            errors.append(f"semantic: duplicate name+organization {no}")
        seen_nameorg[no] = i

    return errors


def validate_file(path):
    """Full validation pipeline. Returns [] if valid, else a list of error strings."""
    try:
        data = load_data(path)
    except ValidationError as exc:
        return [str(exc)]
    errors = schema_errors(data)
    # Run semantic checks even if schema fails — surfaces more issues at once.
    errors += semantic_errors(data)
    return errors


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    path = argv[0] if argv else str(DEFAULT_DATA_PATH)
    errors = validate_file(path)
    if errors:
        print(f"VALIDATION FAILED ({len(errors)} issue(s)) in {path}:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK: {path} is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
