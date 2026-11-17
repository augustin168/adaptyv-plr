#!/usr/bin/env python3
"""PreToolUse guard for Bash|Edit|Write|MultiEdit. Standard library only (Windows/macOS/Linux).

Blocks (exit 2, reason on stderr, which Claude Code shows to the agent):
  (a) Bash commands that request live mode (`--mode live` / `--mode=live`) or set PLR_LIVE.
  (b) Edit/Write/MultiEdit that ADD a `STARBackend(` call to any file other than
      src/adaptyv_plr/backends.py.
Fails closed: unreadable input -> exit 2 (a crash with exit 1 would be treated as "allow").
"""

from __future__ import annotations

import json
import os
import re
import sys

ALLOWED_STAR_FILE = ("src", "adaptyv_plr", "backends.py")

# --mode live | --mode=live | "--mode", "live" (argv list in python -c / subprocess)
LIVE_MODE_RE = re.compile(r"--mode[\"']?(?:\s+|\s*=\s*|\s*,\s*)[\"']?live\b", re.IGNORECASE)
PLR_LIVE_SET_RES = [
  re.compile(r"\bPLR_LIVE\s*="),  # PLR_LIVE=1 cmd, export PLR_LIVE=1, env PLR_LIVE=1
  re.compile(r"\b(?:export|set|setx|setenv|typeset|declare)\s+(?:-\w+\s+)*PLR_LIVE\b", re.I),
  re.compile(r"\$env:PLR_LIVE\s*=", re.I),  # PowerShell
  re.compile(r"[\"']PLR_LIVE[\"']\s*\]\s*="),  # os.environ['PLR_LIVE'] = ...
  re.compile(r"[\"']PLR_LIVE[\"']\s*:"),  # os.environ.update({'PLR_LIVE': ...})
  re.compile(r"(?:setenv|putenv|setdefault)\s*\(\s*[\"']PLR_LIVE", re.I),
]
STAR_CALL_RE = re.compile(r"\bSTARBackend\s*\(")


def block(msg: str) -> None:
  sys.stderr.write(f"BLOCKED by .claude/hooks/guard_plr.py: {msg}\n")
  sys.exit(2)


def check_bash(cmd: object) -> None:
  if not isinstance(cmd, str):
    block("Bash tool_input.command missing or not a string.")
  if LIVE_MODE_RE.search(cmd):
    block(
      "live mode (--mode live) may only be started by the human operator in their own terminal. "
      "Use --mode sim."
    )
  for rx in PLR_LIVE_SET_RES:
    if rx.search(cmd):
      block(
        "setting PLR_LIVE opens the live-hardware gate; only the human operator may do that, "
        "in their own shell. Reading/grepping PLR_LIVE is fine."
      )


def _is_allowed_star_file(file_path: str) -> bool:
  parts = os.path.normpath(os.path.abspath(file_path)).replace("\\", "/").split("/")
  return tuple(parts[-3:]) == ALLOWED_STAR_FILE


def _count(text: object) -> int:
  return len(STAR_CALL_RE.findall(text)) if isinstance(text, str) else 0


def _existing(file_path: str) -> str:
  try:
    with open(file_path, encoding="utf-8", errors="replace") as fh:
      return fh.read()
  except OSError:
    return ""


def check_file_edit(tool: str, ti: dict) -> None:
  file_path = ti.get("file_path")
  if not isinstance(file_path, str) or not file_path:
    block(f"{tool} tool_input.file_path missing.")
  if _is_allowed_star_file(file_path):
    return
  if tool == "Write":
    added = _count(ti.get("content")) - _count(_existing(file_path))
  elif tool == "Edit":
    added = _count(ti.get("new_string")) - _count(ti.get("old_string"))
  else:  # MultiEdit
    edits = ti.get("edits")
    if not isinstance(edits, list):
      block("MultiEdit tool_input.edits missing.")
    added = sum(_count(e.get("new_string")) - _count(e.get("old_string")) for e in edits if isinstance(e, dict))
  if added > 0:
    block(
      f"adding a STARBackend( call in {file_path}. The only allowed construction site is "
      "src/adaptyv_plr/backends.py, behind the PLR_LIVE gate. Use make_liquid_handler(config)."
    )


def main() -> None:
  try:
    data = json.loads(sys.stdin.read() or "")
  except Exception as e:  # noqa: BLE001 - fail closed on anything unparseable
    block(f"could not parse hook input as JSON ({e.__class__.__name__}); failing closed.")
  if not isinstance(data, dict):
    block("hook input is not a JSON object; failing closed.")
  tool = data.get("tool_name")
  ti = data.get("tool_input")
  if not isinstance(ti, dict):
    ti = {}
  if tool == "Bash":
    check_bash(ti.get("command"))
  elif tool in ("Edit", "Write", "MultiEdit"):
    check_file_edit(tool, ti)
  sys.exit(0)


if __name__ == "__main__":
  main()
