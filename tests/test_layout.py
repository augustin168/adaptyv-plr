import pytest

from adaptyv_plr import deck as deck_mod
from adaptyv_plr.backends import make_liquid_handler
from adaptyv_plr.config import RunConfig


def _names_and_locations(deck, skip_core_grippers=True):
  return {
    r.name: (r.location.x, r.location.y, r.location.z)
    for r in deck.get_all_resources()
    if not (skip_core_grippers and r.name.startswith("core_grippers"))
  }


@pytest.mark.xfail(
  strict=True,
  reason="PLR 1.0.0b1: Deck.save writes core_grippers but load_from_json_file drops them "
  "(observed 2026-11-17, see DECISIONS.md). strict=True: this test FAILS once PLR fixes it.",
)
def test_core_grippers_survive_round_trip(tmp_path):
  original = deck_mod.build_demo_deck("starlet")
  loaded = deck_mod.load_layout(deck_mod.save_layout(original, tmp_path / "l.json"))
  assert _names_and_locations(loaded, False) == _names_and_locations(original, False)


@pytest.mark.parametrize("machine", ["star", "starlet"])
def test_layout_round_trip(tmp_path, machine):
  original = deck_mod.build_demo_deck(machine)
  path = deck_mod.save_layout(original, tmp_path / "layout.json")
  assert path.exists() and (tmp_path / "layout.state.json").exists()

  loaded = deck_mod.load_layout(path, machine=machine)
  assert type(loaded) is type(original)
  assert loaded.num_tracks == deck_mod.TRACKS_BY_MACHINE[machine]
  assert _names_and_locations(loaded) == _names_and_locations(original)
  src = loaded.get_resource(deck_mod.SOURCE_PLATE_NAME).get_well("A1")
  assert src.tracker.get_used_volume() == pytest.approx(deck_mod.DEMO_SOURCE_START_VOLUME_UL)


def test_layout_file_used_via_deck_argument(tmp_path):
  path = deck_mod.save_layout(deck_mod.build_demo_deck("starlet"), tmp_path / "lab.json")
  lh = make_liquid_handler(RunConfig(machine="starlet"), deck=path)
  assert lh.deck.has_resource(deck_mod.TIP_RACK_NAME)


def test_layout_machine_mismatch_rejected(tmp_path):
  path = deck_mod.save_layout(deck_mod.build_demo_deck("starlet"), tmp_path / "lab.json")
  with pytest.raises(ValueError, match="num_tracks"):
    deck_mod.load_layout(path, machine="star")
