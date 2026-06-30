from conftest import ROOT


def test_required_governance_files_exist():
    for rel in ["CONTRIBUTING.md", "SECURITY.md", "LICENSE",
                ".github/CODEOWNERS", ".github/dependabot.yml",
                "docs/MAINTAINERS.md"]:
        assert (ROOT / rel).exists(), rel


def test_maintainers_doc_mentions_branch_protection():
    text = (ROOT / "docs" / "MAINTAINERS.md").read_text().lower()
    assert "branch protection" in text
    assert "require" in text
