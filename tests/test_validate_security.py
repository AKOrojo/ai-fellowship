import validate


def base_entry(**over):
    e = {
        "id": "a", "name": "A", "organization": "Org",
        "category": "research-safety", "url": "https://a.example",
        "description": "desc", "location": "Remote",
        "last_verified": "2026-06-30",
        "cycles": [{"cycle": "2026 Cohort", "deadline": "Rolling"}],
    }
    e.update(over)
    return e


def errs(entry):
    return validate.semantic_errors({"fellowships": [entry]})


def test_https_url_ok():
    assert validate.is_safe_url("https://example.org/path?q=1")


def test_javascript_url_rejected():
    assert not validate.is_safe_url("javascript:alert(1)")


def test_http_url_rejected():
    assert not validate.is_safe_url("http://example.org")


def test_url_with_credentials_rejected():
    assert not validate.is_safe_url("https://user:pass@example.org")


def test_data_url_rejected():
    assert not validate.is_safe_url("data:text/html,<script>")


def test_text_rejects_html_tags():
    assert not validate.is_safe_text("<script>x</script>", 500)


def test_text_rejects_control_chars():
    assert not validate.is_safe_text("line\x00break", 500)


def test_text_rejects_overlength():
    assert not validate.is_safe_text("x" * 501, 500)


def test_iso_date_valid():
    assert validate.is_iso_date("2026-12-31")


def test_iso_date_invalid_calendar():
    assert not validate.is_iso_date("2026-02-30")


def test_semantic_flags_xss_name():
    assert errs(base_entry(name="<img src=x onerror=alert(1)>"))


def test_semantic_flags_js_url():
    assert errs(base_entry(url="javascript:alert(1)"))


def test_semantic_clean_entry_has_no_errors():
    assert errs(base_entry()) == []


def test_cycle_bad_deadline_literal_flagged():
    assert errs(base_entry(cycles=[{"cycle": "2026", "deadline": "soon"}]))


def test_cycle_accepts_rolling_and_dates():
    assert errs(base_entry(cycles=[{"cycle": "2026", "deadline": "Rolling"}])) == []
    assert errs(base_entry(cycles=[{"cycle": "2026", "deadline": "2026-09-01"}])) == []


def test_cycle_unsafe_label_flagged():
    assert errs(base_entry(cycles=[{"cycle": "<b>x</b>", "deadline": "Rolling"}]))


def test_duplicate_cycle_labels_flagged():
    assert errs(base_entry(cycles=[
        {"cycle": "2026", "deadline": "Rolling"},
        {"cycle": "2026", "deadline": "2026-09-01"},
    ]))


def test_cycle_bad_opens_flagged():
    assert errs(base_entry(cycles=[{"cycle": "2026", "deadline": "Rolling", "opens": "nope"}]))


def test_semantic_flags_duplicate_id():
    data = {"fellowships": [
        base_entry(id="dup"),
        base_entry(id="dup", url="https://b.example", name="B", organization="Org2"),
    ]}
    assert validate.semantic_errors(data)


def test_semantic_flags_duplicate_url():
    data = {"fellowships": [
        base_entry(id="one"),
        base_entry(id="two", name="B", organization="Org2"),
    ]}
    assert validate.semantic_errors(data)  # same url


def test_validate_file_passes_on_seed():
    assert validate.validate_file(str(validate.DEFAULT_DATA_PATH)) == []


def test_url_with_tab_rejected():
    assert not validate.is_safe_url("https://example.org/a\tb")


def test_url_with_pipe_rejected():
    assert not validate.is_safe_url("https://example.org/a|b")


def test_semantic_flags_duplicate_name_org():
    data = {"fellowships": [
        base_entry(id="one", url="https://a.example"),
        base_entry(id="two", url="https://b.example"),
    ]}
    assert any("name+organization" in e for e in validate.semantic_errors(data))
