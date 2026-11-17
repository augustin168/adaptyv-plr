"""Run configuration. No PyLabRobot import here."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Mode = Literal["sim", "live"]
Machine = Literal["star", "starlet"]
SimBackend = Literal["chatterbox", "star-chatterbox"]

# TODO(confirm on machine): channel counts are the common configurations, not read from OUR instrument.
CHANNELS_BY_MACHINE: dict[str, int] = {"star": 16, "starlet": 8}

LIVE_ENV_VAR = "PLR_LIVE"


@dataclass(frozen=True)
class RunConfig:
  mode: Mode = "sim"
  machine: Machine = "starlet"
  # "chatterbox" = generic LiquidHandlerChatterboxBackend (default).
  # "star-chatterbox" = STARChatterboxBackend: also builds STAR firmware commands, still no I/O.
  sim_backend: SimBackend = "chatterbox"
  num_channels: int | None = None  # None -> CHANNELS_BY_MACHINE[machine]

  def __post_init__(self) -> None:
    if self.mode not in ("sim", "live"):
      raise ValueError(f"mode must be 'sim' or 'live', got {self.mode!r}")
    if self.machine not in CHANNELS_BY_MACHINE:
      raise ValueError(f"machine must be one of {sorted(CHANNELS_BY_MACHINE)}, got {self.machine!r}")
    if self.sim_backend not in ("chatterbox", "star-chatterbox"):
      raise ValueError(f"unknown sim_backend {self.sim_backend!r}")

  @property
  def channels(self) -> int:
    return self.num_channels if self.num_channels is not None else CHANNELS_BY_MACHINE[self.machine]
