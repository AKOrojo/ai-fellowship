"""Emit a Markdown maintenance report: link reachability + expired deadlines.

Pure-stdlib HTTP HEAD checks with a short timeout. Never modifies data — it only
reports, so a human decides what to change. Printed to stdout for the workflow.
"""
import sys
import urllib.request
from datetime import date

import validate
import generate


def check_url(url, timeout=8):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "ai-fellowships-bot"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status < 400
    except Exception:
        return False


def main():
    data = validate.load_data(str(validate.DEFAULT_DATA_PATH))
    today = date.today()
    dead, expired = [], []
    for e in data["fellowships"]:
        if not check_url(e["url"]):
            dead.append(e)
        for c in e.get("cycles", []):
            if generate.derive_status(c.get("opens"), c.get("deadline", ""), today) == "closed":
                expired.append((e, c))

    print("## Weekly maintenance report\n")
    print(f"_Generated {today.isoformat()} — {len(data['fellowships'])} fellowships._\n")
    print(f"### 🔴 Possibly dead links ({len(dead)})")
    for e in dead:
        print(f"- `{e['id']}` — {e['url']}")
    print(f"\n### ⏰ Past-deadline cycles ({len(expired)})")
    for e, c in expired:
        print(f"- `{e['id']}` — {c.get('cycle')} (deadline {c.get('deadline')})")
    if not dead and not expired:
        print("\nNothing needs attention. 🎉")
    return 0


if __name__ == "__main__":
    sys.exit(main())
