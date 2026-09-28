from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_entrypoint_is_small_and_importable_syntax():
    path = ROOT / "bot.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    assert len(tree.body) <= 4


def test_modular_sections_exist():
    sections = sorted((ROOT / "app" / "sections").glob("s*.py"))
    assert len(sections) >= 60
    for section in sections:
        ast.parse(section.read_text(encoding="utf-8"))


def test_no_legacy_monolith():
    assert not (ROOT / "legacy_bot.py").exists()
