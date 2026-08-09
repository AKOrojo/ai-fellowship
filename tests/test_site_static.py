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


def test_theme_js_is_safe_and_referenced():
    # theme.js sets the theme before paint; it must be an external script (CSP)
    # and avoid dangerous sinks like the rest of the site.
    js = (SITE / "theme.js").read_text()
    assert "innerHTML" not in js
    assert "eval(" not in js
    html = (SITE / "index.html").read_text()
    assert 'src="theme.js"' in html


def test_index_has_theme_toggle():
    html = (SITE / "index.html").read_text()
    assert 'id="theme-toggle"' in html


def test_app_js_has_area_filter_and_countdown():
    js = (SITE / "app.js").read_text()
    # research-area chips drive the filter; every area in the taxonomy is offered
    for area in ("technical", "interpretability", "governance", "security",
                 "biosecurity", "societal", "generalist", "other"):
        assert f'"{area}"' in js
    assert "countdownText" in js
    assert "setInterval" in js


def test_index_has_area_chips_and_smart_sort():
    html = (SITE / "index.html").read_text()
    assert 'id="area-chips"' in html
    assert 'value="smart"' in html


def test_style_has_past_deadline_treatment():
    css = (SITE / "style.css").read_text()
    assert ".card.past" in css
    assert ".countdown" in css
