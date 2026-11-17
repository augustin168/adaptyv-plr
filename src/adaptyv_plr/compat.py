"""The ONLY module in this package that imports PyLabRobot.

Pinned: pylabrobot==1.0.0b1. Every name below was checked against the installed package
(inspect / dir() / `python -W error::DeprecationWarning`) on 2026-11-17. See DECISIONS.md.

Verified import paths and notes:
- LiquidHandler                    pylabrobot.legacy.liquid_handling
- LiquidHandlerChatterboxBackend   pylabrobot.legacy.liquid_handling.backends   (num_channels: int = 8)
    NOT `ChatterBoxBackend`: in 1.0.0b1 it raises NotImplementedError ("deprecated").
- STARChatterboxBackend            pylabrobot.legacy.liquid_handling.backends.hamilton.STAR_chatterbox
    STAR-specific simulator (subclass of STARBackend, no I/O); builds STAR firmware commands.
- STARBackend                      pylabrobot.legacy.liquid_handling.backends   (re-exported only;
    the single construction site is backends.py, behind the PLR_LIVE gate)
- STARDeck (54 tracks), STARLetDeck (30 tracks), Deck   pylabrobot.resources
    Deck.assign_child_resource(..., track=N). `rails=` is DEPRECATED in favour of `track=`.
- hamilton_tip_carrier_L5, hamilton_plate_carrier_L5_ac   pylabrobot.resources.hamilton
    Replacements named by the DeprecationWarnings of TIP_CAR_480(_A00) / PLT_CAR_L5AC_A00.
- hamilton_96_tiprack_300uL, cor_96_wellplate_360uL_Fb, set_tip_tracking, set_volume_tracking
                                   pylabrobot.resources
- Visualizer                       pylabrobot.visualizer
    Visualizer(resource, host="127.0.0.1", ws_port=2121, fs_port=1337, open_browser=True); async setup/stop.
- Deprecated shim (do NOT use):    pylabrobot.liquid_handling -> warns, use pylabrobot.legacy.liquid_handling
"""

from pylabrobot.legacy.liquid_handling import LiquidHandler
from pylabrobot.legacy.liquid_handling.backends import (
  LiquidHandlerBackend,
  LiquidHandlerChatterboxBackend,
  STARBackend,
)
from pylabrobot.legacy.liquid_handling.backends.hamilton.STAR_chatterbox import (
  STARChatterboxBackend,
)
from pylabrobot.resources import (
  Container,
  Deck,
  Plate,
  STARDeck,
  STARLetDeck,
  TipRack,
  cor_96_wellplate_360uL_Fb,
  hamilton_96_tiprack_300uL,
  set_tip_tracking,
  set_volume_tracking,
)
from pylabrobot.resources.hamilton import (
  hamilton_plate_carrier_L5_ac,
  hamilton_tip_carrier_L5,
)
from pylabrobot.visualizer import Visualizer

__all__ = [
  "Container",
  "Deck",
  "LiquidHandler",
  "LiquidHandlerBackend",
  "LiquidHandlerChatterboxBackend",
  "Plate",
  "STARBackend",
  "STARChatterboxBackend",
  "STARDeck",
  "STARLetDeck",
  "TipRack",
  "Visualizer",
  "cor_96_wellplate_360uL_Fb",
  "hamilton_96_tiprack_300uL",
  "hamilton_plate_carrier_L5_ac",
  "hamilton_tip_carrier_L5",
  "set_tip_tracking",
  "set_volume_tracking",
]
