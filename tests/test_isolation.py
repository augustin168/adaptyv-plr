"""Static boundaries: only compat.py imports pylabrobot; src/ never imports experiments/."""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "adaptyv_plr"


def _imported_modules(path: Path) -> set[str]:
  mods = set()
  for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
    if isinstance(node, ast.Import):
      mods.update(a.name for a in node.names)
    elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
      mods.add(node.module)
  return mods


def test_only_compat_imports_pylabrobot():
  offenders = [
    p.name
    for p in SRC.glob("*.py")
    if p.name != "compat.py"
    and any(m == "pylabrobot" or m.startswith("pylabrobot.") for m in _imported_modules(p))
  ]
  assert offenders == []


def test_src_does_not_import_experiments():
  offenders = [
    p.name for p in SRC.rglob("*.py") if any(m.split(".")[0] == "experiments" for m in _imported_modules(p))
  ]
  assert offenders == []


def test_demo_cli_runs_headless_on_both_machines(capsys):
  import asyncio

  import run_demo

  for machine in ("star", "starlet"):
    assert asyncio.run(run_demo.main(["--machine", machine])) == 0
  out = capsys.readouterr().out
  assert "machine=star channels=16" in out and "machine=starlet channels=8" in out
