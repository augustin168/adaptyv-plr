"""Test-wide guards.

pyproject's `error::DeprecationWarning:adaptyv_plr.*` only catches warnings ATTRIBUTED to our
modules (stacklevel pointing at our frame, e.g. `rails=` or the `pylabrobot.liquid_handling`
import shim, both verified). A warning whose stacklevel points at a PyLabRobot frame (e.g. PLR
internally calling something deprecated on our behalf) slips past that filter.
This guard raises any DeprecationWarning whose call stack passes through src/adaptyv_plr,
including during test collection (imports). It does not silence anything.
"""

from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OUR_SRC = os.path.normcase(str(ROOT / "src" / "adaptyv_plr"))

_original_warn = warnings.warn


def _frame_in_our_package() -> str | None:
  f = sys._getframe(2)
  while f is not None:
    fn = os.path.normcase(os.path.realpath(f.f_code.co_filename))
    if fn.startswith(OUR_SRC):
      return f"{f.f_code.co_filename}:{f.f_lineno}"
    f = f.f_back
  return None


def _guarded_warn(message, category=None, stacklevel=1, source=None, **kwargs):
  cat = category
  if cat is None:
    cat = type(message) if isinstance(message, Warning) else UserWarning
  if issubclass(cat, DeprecationWarning):
    where = _frame_in_our_package()
    if where is not None:
      raise cat(f"{message}  [reached from our code at {where}]")
  return _original_warn(message, category, stacklevel + 1, source, **kwargs)


warnings.warn = _guarded_warn


@pytest.fixture(autouse=True)
def _no_live_env(monkeypatch):
  """Tests never run with the live gate open, whatever the developer's shell has."""
  monkeypatch.delenv("PLR_LIVE", raising=False)
