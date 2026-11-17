import asyncio

import pytest

from adaptyv_plr import deck as deck_mod
from adaptyv_plr.backends import make_liquid_handler
from adaptyv_plr.config import RunConfig
from adaptyv_plr.pipeline import Pipeline
from helpers import transfer, well


@pytest.mark.parametrize("machine,expected_channels", [("star", 16), ("starlet", 8)])
@pytest.mark.parametrize("sim_backend", ["chatterbox", "star-chatterbox"])
def test_volume_moves_in_simulation(machine, expected_channels, sim_backend):
  config = RunConfig(machine=machine, sim_backend=sim_backend)
  lh = make_liquid_handler(config)
  assert config.channels == expected_channels

  # Use the LAST channel to exercise the channel count of each machine.
  pipeline = Pipeline(steps=[transfer(50.0, channel=expected_channels - 1)])
  asyncio.run(pipeline.run(lh, num_channels=config.channels))

  assert lh.backend.num_channels == expected_channels
  src = well(lh, deck_mod.SOURCE_PLATE_NAME, "A1")
  dst = well(lh, deck_mod.DEST_PLATE_NAME, "A1")
  assert src.tracker.get_used_volume() == pytest.approx(deck_mod.DEMO_SOURCE_START_VOLUME_UL - 50.0)
  assert dst.tracker.get_used_volume() == pytest.approx(50.0)
  # Tip was discarded to trash, so the spot is now empty (tip tracking on).
  assert not lh.deck.get_resource(deck_mod.TIP_RACK_NAME).get_item("A1").tracker.has_tip


def test_two_steps_accumulate():
  config = RunConfig(machine="starlet")
  lh = make_liquid_handler(config)
  steps = [transfer(60.0, tip_well="A1", dst="A1"), transfer(40.0, tip_well="B1", dst="B1")]
  asyncio.run(Pipeline(steps=steps).run(lh, num_channels=config.channels))
  assert well(lh, deck_mod.SOURCE_PLATE_NAME, "A1").tracker.get_used_volume() == pytest.approx(100.0)
  assert well(lh, deck_mod.DEST_PLATE_NAME, "B1").tracker.get_used_volume() == pytest.approx(40.0)


def test_stop_called_when_step_fails():
  config = RunConfig(machine="starlet")
  lh = make_liquid_handler(config)
  calls = []
  original_stop = lh.stop

  async def spy_stop():
    calls.append("stop")
    await original_stop()

  lh.stop = spy_stop

  class Boom:
    name = "boom"

    def preflight(self, ledger):
      return []

    async def run(self, ctx):
      raise RuntimeError("simulated failure")

  with pytest.raises(RuntimeError, match="simulated failure"):
    asyncio.run(Pipeline(steps=[Boom(), transfer(10.0)]).run(lh, num_channels=config.channels))
  assert calls == ["stop"]
  # second step never ran: no volume moved
  assert well(lh, deck_mod.DEST_PLATE_NAME, "A1").tracker.get_used_volume() == 0
