import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data" / "fellowships.yaml"
SCHEMA = ROOT / "data" / "schema.json"

# Make modules in scripts/ importable as top-level modules.
sys.path.insert(0, str(SCRIPTS))
