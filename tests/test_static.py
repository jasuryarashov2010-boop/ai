from pathlib import Path
import ast
ROOT = Path(__file__).resolve().parents[1]
def test_parse():
    for p in (ROOT / "app").rglob("*.py"):
        ast.parse(p.read_text(encoding="utf-8"))
def test_routers():
    t = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    assert all(x in t for x in [
        "include_router(start_router)", "include_router(menu_router)",
        "include_router(ai_router)", "include_router(support_router)",
        "include_router(admin_router)"
    ])
