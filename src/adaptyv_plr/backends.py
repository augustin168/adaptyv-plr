"""LiquidHandler factory. The only place in the repo allowed to construct a STARBackend.

The caller owns the lifecycle: `await lh.setup()` / `await lh.stop()` (Pipeline.run does this).
"""

from __future__ import annotations

import os
from pathlib import Path

from . import compat
from .config import LIVE_ENV_VAR, RunConfig
from .deck import enable_tracking, resolve_deck


class LiveModeNotAllowed(RuntimeError):
  """Raised when live mode is requested without the explicit human gate."""


def _make_backend(config: RunConfig) -> compat.LiquidHandlerBackend:
  if config.mode == "sim":
    if config.sim_backend == "star-chatterbox":
      return compat.STARChatterboxBackend(num_channels=config.channels)
    return compat.LiquidHandlerChatterboxBackend(num_channels=config.channels)

  # ---- live: real hardware --------------------------------------------------------------
  if os.environ.get(LIVE_ENV_VAR) != "1":
    raise LiveModeNotAllowed(
      f"Live mode requires {LIVE_ENV_VAR}=1, set by the operator in their own shell. "
      "Agents must never set it."
    )
  # Not executed during environment setup or tests. Default constructor args only;
  # TODO(confirm on machine): serial_number / device_address if more than one STAR is attached.
  return compat.STARBackend()


def make_liquid_handler(
  config: RunConfig,
  deck: compat.Deck | str | Path | None = None,
) -> compat.LiquidHandler:
  """Build (but do not set up) a LiquidHandler.

  deck: None -> demo deck for config.machine; a path -> lab layout JSON; or a Deck instance.
  """
  backend = _make_backend(config)  # live gate is checked before anything else is built
  enable_tracking()
  return compat.LiquidHandler(backend=backend, deck=resolve_deck(config.machine, deck))
