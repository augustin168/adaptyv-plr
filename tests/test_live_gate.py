"""The live gate. These tests never open it (conftest removes PLR_LIVE for every test)."""

import asyncio
import os

import pytest

from adaptyv_plr import compat
from adaptyv_plr.backends import LiveModeNotAllowed, make_liquid_handler
from adaptyv_plr.config import RunConfig


@pytest.fixture
def star_backend_must_not_be_built(monkeypatch):
  def tripwire(*a, **kw):
    raise AssertionError("STARBackend was constructed")

  monkeypatch.setattr(compat, "STARBackend", tripwire)


def test_live_raises_without_env(star_backend_must_not_be_built):
  assert "PLR_LIVE" not in os.environ
  for machine in ("star", "starlet"):
    with pytest.raises(LiveModeNotAllowed, match="PLR_LIVE=1"):
      make_liquid_handler(RunConfig(mode="live", machine=machine))


def test_live_raises_with_wrong_value(monkeypatch, star_backend_must_not_be_built):
  monkeypatch.setenv("PLR_LIVE", "true")  # only the exact string "1" opens the gate
  with pytest.raises(LiveModeNotAllowed):
    make_liquid_handler(RunConfig(mode="live"))


def test_demo_cli_refuses_live_without_env(star_backend_must_not_be_built, capsys):
  import run_demo

  rc = asyncio.run(run_demo.main(["--mode", "live", "--machine", "star"]))
  assert rc == 3
  assert "REFUSED" in capsys.readouterr().err
