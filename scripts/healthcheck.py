"""Static/runtime health check used by deployment tooling."""
from pathlib import Path
import ast
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

try:
    ast.parse((ROOT / "bot.py").read_text(encoding="utf-8"))
except Exception as exc:
    errors.append(f"bot.py syntax: {exc}")

sections = list((ROOT / "app" / "sections").glob("s*.py"))
if len(sections) < 60:
    errors.append(f"expected >=60 modular sections, found {len(sections)}")
for path in sections:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path.name}: {exc}")

if errors:
    print("HEALTHCHECK: FAIL")
    print("\n".join(f"- {e}" for e in errors))
    sys.exit(1)
print(f"HEALTHCHECK: OK ({len(sections)} sections)")
