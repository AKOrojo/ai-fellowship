import yaml
from conftest import ROOT
import issue_to_entry as i2e

FORM = ROOT / ".github" / "ISSUE_TEMPLATE" / "new-fellowship.yml"


def test_form_labels_match_parser_headings():
    doc = yaml.safe_load(FORM.read_text())
    labels = {
        item["attributes"]["label"]
        for item in doc["body"]
        if item.get("type") in ("input", "dropdown", "textarea")
    }
    # Every form label must be a heading the parser understands.
    for label in labels:
        assert label in i2e.FIELD_HEADINGS, f"form label not handled by parser: {label}"


def test_form_autolabels_submission():
    doc = yaml.safe_load(FORM.read_text())
    assert "fellowship-submission" in doc.get("labels", [])
