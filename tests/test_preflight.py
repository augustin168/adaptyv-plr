import asyncio

import pytest

from adaptyv_plr import deck as deck_mod
from adaptyv_plr.backends import make_liquid_handler
from adaptyv_plr.config import RunConfig
from adaptyv_plr.pipeline import Pipeline, PreflightError
from helpers import transfer, well


def _lh_with_spies(machine="starlet"):
  """LiquidHandler whose setup and backend motion commands are recorded."""
  config = RunConfig(machine=machine)
  lh = make_liquid_handler(config)
  calls: list[str] = []

  async def no_setup():
    calls.append("setup")

  lh.setup = no_setup
  for name in ("pick_up_tips", "aspirate", "dispense", "drop_tips"):
    original = getattr(lh.backend, name)

    async def spy(*a, _n=name, _o=original, **kw):
      calls.append(_n)
      return await _o(*a, **kw)

    setattr(lh.backend, name, spy)
  return lh, config, calls


def _assert_rejected(steps, match, machine="starlet"):
  lh, config, calls = _lh_with_spies(machine)
  with pytest.raises(PreflightError, match=match):
    asyncio.run(Pipeline(steps=steps).run(lh, num_channels=config.channels))
  assert calls == [], f"motion/setup happened before preflight rejection: {calls}"
  # trackers untouched
  assert well(lh, deck_mod.SOURCE_PLATE_NAME, "A1").tracker.get_used_volume() == pytest.approx(
    deck_mod.DEMO_SOURCE_START_VOLUME_UL
  )


def test_overdraw_rejected_before_any_motion():
  _assert_rejected([transfer(deck_mod.DEMO_SOURCE_START_VOLUME_UL + 1)], "overdraw")


def test_cumulative_overdraw_rejected_before_first_step_moves():
  # each step alone is fine; together they exceed the source. Step 1 must not run either.
  _assert_rejected([transfer(150.0, tip_well="A1"), transfer(150.0, tip_well="B1")], "step 2.*overdraw")


def test_tip_reuse_rejected():
  _assert_rejected([transfer(10.0, tip_well="A1"), transfer(10.0, tip_well="A1")], "step 2.*no tip")


def test_volume_above_tip_rated_volume_rejected():
  # 300 uL tips report maximal_volume 400; 350 uL must still be rejected (rated 300).
  # Source start volume is raised so the overdraw check cannot be what rejects it.
  lh, config, calls = _lh_with_spies()
  well(lh, deck_mod.SOURCE_PLATE_NAME, "A1").tracker.set_volume(360)
  with pytest.raises(PreflightError, match="tip rated volume 300"):
    asyncio.run(Pipeline(steps=[transfer(350.0)]).run(lh, num_channels=config.channels))
  assert calls == []


def test_volume_equal_to_tip_rated_volume_allowed():
  config = RunConfig(machine="starlet")
  lh = make_liquid_handler(config)
  well(lh, deck_mod.SOURCE_PLATE_NAME, "A1").tracker.set_volume(300)
  asyncio.run(Pipeline(steps=[transfer(300.0)]).run(lh, num_channels=config.channels))
  assert well(lh, deck_mod.DEST_PLATE_NAME, "A1").tracker.get_used_volume() == pytest.approx(300.0)


def test_channel_out_of_range_for_starlet():
  _assert_rejected([transfer(10.0, channel=8)], "channel 8 out of range for 8")


def test_missing_resource_rejected():
  step = transfer(10.0)
  step.source_plate = "not_on_deck"
  _assert_rejected([step], "source plate not on deck")
