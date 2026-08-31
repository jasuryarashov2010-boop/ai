from pathlib import Path
import ast, compileall

ROOT = Path(__file__).parent
for p in (ROOT / "app").rglob("*.py"):
    ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
assert compileall.compile_dir(str(ROOT / "app"), quiet=1)
main = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
for x in ["include_router(start_router)", "include_router(menu_router)", "include_router(ai_router)",
          "include_router(support_router)", "include_router(admin_router)"]:
    assert x in main, x
print("V300 static verification: OK")
