"""Deck construction and layout persistence.

The demo deck is for SIMULATION only. Its carrier positions are named placeholders, not measured
positions on our instrument. For real runs, pass the lab-provided layout file via `deck=`.
"""

from __future__ import annotations

from pathlib import Path

from . import compat

# Track counts as defined by the installed PyLabRobot deck classes (STARDeck / STARLetDeck).
TRACKS_BY_MACHINE: dict[str, int] = {"star": 54, "starlet": 30}

# TODO(confirm on machine): placeholder tracks for the demo deck. Not our lab layout.
DEMO_TIP_CARRIER_TRACK = 1
DEMO_PLATE_CARRIER_TRACK = 7

# Demo resource names (used by tests, steps and the demo script).
TIP_RACK_NAME = "tips_300uL"
SOURCE_PLATE_NAME = "source_plate"
DEST_PLATE_NAME = "dest_plate"

DEMO_SOURCE_START_VOLUME_UL = 200.0  # pre-filled in SOURCE_PLATE A1 for the demo


def enable_tracking() -> None:
  """Tip + volume tracking are global switches in PyLabRobot; always on in this project."""
  compat.set_tip_tracking(True)
  compat.set_volume_tracking(True)


def build_demo_deck(machine: str) -> compat.Deck:
  if machine not in TRACKS_BY_MACHINE:
    raise ValueError(f"unknown machine {machine!r}")
  enable_tracking()
  deck = compat.STARDeck() if machine == "star" else compat.STARLetDeck()

  tip_carrier = compat.hamilton_tip_carrier_L5("tip_carrier")
  tip_carrier[0] = compat.hamilton_96_tiprack_300uL(TIP_RACK_NAME)

  plate_carrier = compat.hamilton_plate_carrier_L5_ac("plate_carrier")
  plate_carrier[0] = source = compat.cor_96_wellplate_360uL_Fb(SOURCE_PLATE_NAME)
  plate_carrier[1] = compat.cor_96_wellplate_360uL_Fb(DEST_PLATE_NAME)

  deck.assign_child_resource(tip_carrier, track=DEMO_TIP_CARRIER_TRACK)
  deck.assign_child_resource(plate_carrier, track=DEMO_PLATE_CARRIER_TRACK)

  source.get_well("A1").tracker.set_volume(DEMO_SOURCE_START_VOLUME_UL)
  return deck


def _state_path(path: Path) -> Path:
  return path.with_name(path.stem + ".state.json")


def save_layout(deck: compat.Deck, path: str | Path, include_state: bool = True) -> Path:
  """Write deck geometry to `path` (and tip/volume state to `<stem>.state.json`)."""
  path = Path(path)
  path.parent.mkdir(parents=True, exist_ok=True)
  deck.save(str(path), indent=2)
  if include_state:
    deck.save_state_to_file(str(_state_path(path)), indent=2)
  return path


def load_layout(path: str | Path, machine: str | None = None) -> compat.Deck:
  """Load a layout file; also loads `<stem>.state.json` if present."""
  path = Path(path)
  enable_tracking()
  deck = compat.Deck.load_from_json_file(str(path))
  if machine is not None:
    expected = TRACKS_BY_MACHINE[machine]
    actual = getattr(deck, "num_tracks", None)
    if actual != expected:
      raise ValueError(
        f"layout {path} has num_tracks={actual}, but machine={machine!r} expects {expected}"
      )
  state = _state_path(path)
  if state.exists():
    deck.load_state_from_file(str(state))
  return deck


def resolve_deck(machine: str, deck: compat.Deck | str | Path | None = None) -> compat.Deck:
  if deck is None:
    return build_demo_deck(machine)
  if isinstance(deck, (str, Path)):
    return load_layout(deck, machine=machine)
  return deck
