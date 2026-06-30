import re
import yaml
from conftest import ROOT

WF = ROOT / ".github" / "workflows"
SHA_PIN = re.compile(r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$")


def workflow_files():
    return sorted(WF.glob("*.yml"))


def test_workflows_exist():
    names = {f.name for f in workflow_files()}
    assert {"validate.yml", "build-deploy.yml", "maintenance.yml", "issue-to-pr.yml"} <= names


def test_no_pull_request_target():
    for f in workflow_files():
        assert "pull_request_target" not in f.read_text(), f


def test_every_action_is_sha_pinned():
    for f in workflow_files():
        for m in re.finditer(r"uses:\s*(\S+)", f.read_text()):
            ref = m.group(1).strip().strip("'\"")
            if ref.startswith("./") or ref.startswith("docker://"):
                continue
            assert SHA_PIN.match(ref), f"{f.name}: '{ref}' is not pinned to a 40-hex SHA"


def test_every_workflow_declares_permissions():
    for f in workflow_files():
        doc = yaml.safe_load(f.read_text())
        top = "permissions" in doc
        jobs = doc.get("jobs", {})
        per_job = jobs and all("permissions" in j for j in jobs.values())
        assert top or per_job, f"{f.name} must declare permissions"


def test_validate_is_read_only_and_pr_triggered():
    doc = yaml.safe_load((WF / "validate.yml").read_text())
    # 'on' may parse as the boolean True key in YAML; handle both.
    triggers = doc.get("on", doc.get(True))
    assert "pull_request" in triggers
    assert doc["permissions"].get("contents") == "read"
