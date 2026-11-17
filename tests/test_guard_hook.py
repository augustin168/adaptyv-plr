"""Pipe JSON into the PreToolUse hook exactly like Claude Code does.

Forbidden strings are assembled by concatenation so that this file itself never contains them
literally (the hook would otherwise block the agent from editing this file).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "guard_plr.py"

LIVE = "--mode" + " live"
LIVE_EQ = "--mode" + "=live"
ENV = "PLR" + "_LIVE"
STAR_CALL = "STAR" + "Backend("
BACKENDS = str(ROOT / "src" / "adaptyv_plr" / "backends.py")
OTHER = str(ROOT / "src" / "adaptyv_plr" / "steps.py")


def run_hook(payload) -> subprocess.CompletedProcess:
  raw = payload if isinstance(payload, str) else json.dumps(payload)
  return subprocess.run([sys.executable, str(HOOK)], input=raw, capture_output=True, text=True, timeout=30)


def bash(cmd):
  return {"tool_name": "Bash", "tool_input": {"command": cmd}}


BLOCK = [
  ("bash live flag", bash(f"python scripts/run_demo.py {LIVE}")),
  ("bash live flag =", bash(f"python scripts/run_demo.py {LIVE_EQ} --machine star")),
  ("bash live argv list", bash("python -c \"run_demo.main(['--mode'" + ", 'live'])\"")),
  ("bash env prefix", bash(f"{ENV}=1 python scripts/run_demo.py")),
  ("bash export", bash(f"export {ENV}=1")),
  ("bash powershell", bash(f"$env:{ENV} = '1'")),
  ("bash python environ", bash(f"python -c \"import os; os.environ['{ENV}']='1'\"")),
  ("write star call", {"tool_name": "Write", "tool_input": {"file_path": OTHER, "content": f"b = {STAR_CALL})"}}),
  (
    "edit star call",
    {"tool_name": "Edit", "tool_input": {"file_path": OTHER, "old_string": "x", "new_string": f"{STAR_CALL})"}},
  ),
  (
    "multiedit star call",
    {"tool_name": "MultiEdit", "tool_input": {"file_path": OTHER, "edits": [{"old_string": "a", "new_string": STAR_CALL}]}},
  ),
  (
    "star call in fake backends.py elsewhere",
    {"tool_name": "Write", "tool_input": {"file_path": str(ROOT / "scripts" / "backends.py"), "content": STAR_CALL}},
  ),
  ("malformed json", "{not json"),
]

ALLOW = [
  ("bash sim", bash("python scripts/run_demo.py --mode sim --machine star")),
  ("bash pytest", bash("pytest -q")),
  ("bash grep env", bash(f"grep -rn {ENV} src/")),
  ("write backends.py", {"tool_name": "Write", "tool_input": {"file_path": BACKENDS, "content": f"{STAR_CALL})"}}),
  ("edit unrelated", {"tool_name": "Edit", "tool_input": {"file_path": OTHER, "old_string": "a", "new_string": "b"}}),
  (
    "edit keeps existing call count",
    {"tool_name": "Edit", "tool_input": {"file_path": OTHER, "old_string": STAR_CALL + "1)", "new_string": STAR_CALL + "2)"}},
  ),
  ("isinstance check", {"tool_name": "Write", "tool_input": {"file_path": OTHER, "content": "isinstance(b, STARBackend)"}}),
  ("chatterbox subclass", {"tool_name": "Write", "tool_input": {"file_path": OTHER, "content": "STARChatterboxBackend(num_channels=8)"}}),
  ("other tool", {"tool_name": "Read", "tool_input": {"file_path": OTHER}}),
]


@pytest.mark.parametrize("label,payload", BLOCK, ids=[b[0] for b in BLOCK])
def test_hook_blocks(label, payload):
  r = run_hook(payload)
  assert r.returncode == 2, (label, r.returncode, r.stderr)
  assert "BLOCKED" in r.stderr


@pytest.mark.parametrize("label,payload", ALLOW, ids=[a[0] for a in ALLOW])
def test_hook_allows(label, payload):
  r = run_hook(payload)
  assert r.returncode == 0, (label, r.stderr)
