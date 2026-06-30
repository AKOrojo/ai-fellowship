from conftest import ROOT

SITE = ROOT / "site"


def test_index_has_strict_csp():
    html = (SITE / "index.html").read_text()
    assert "Content-Security-Policy" in html
    assert "default-src 'self'" in html


def test_index_has_no_inline_script():
    html = (SITE / "index.html").read_text()
    # external app.js only; no inline <script>...code...</script>
    assert "<script src=" in html
    assert "<script>" not in html


def test_app_js_avoids_dangerous_sinks():
    js = (SITE / "app.js").read_text()
    assert "innerHTML" not in js
    assert "eval(" not in js
    assert "textContent" in js


def test_app_js_checks_url_scheme():
    js = (SITE / "app.js").read_text()
    assert "https:" in js
