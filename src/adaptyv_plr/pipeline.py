"""Ordered pipeline: full static preflight, then setup, then steps. No auto-recovery.

Order in Pipeline.run:
  1. preflight every step against a PreflightLedger (static: no backend calls, no motion).
     Any problem -> PreflightError, and lh.setup() is never called (setup homes a real STAR).
  2. await lh.setup()
  3. run steps in order, logging each; the first exception stops the run and is re-raised.
     No retries, no "recovery" moves.
  4. finally: await lh.stop() if setup was started.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import AbstractAsyncContextManager, nullcontext
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol, Sequence

from . import compat

log = logging.getLogger(__name__)


class PreflightError(RuntimeError):
  def __init__(self, problems: list[str]):
    self.problems = problems
    super().__init__("Preflight failed:\n  - " + "\n  - ".join(problems))


@dataclass
class PreflightLedger:
  """Simulated deck state used during preflight, so step N sees the effect of steps 1..N-1.

  Reads initial values from PyLabRobot trackers; never mutates the real deck/trackers.
  """

  deck: compat.Deck
  num_channels: int
  _volume_ul: dict[str, float] = field(default_factory=dict)
  _has_tip: dict[str, bool] = field(default_factory=dict)

  def get(self, name: str) -> Any | None:
    try:
      return self.deck.get_resource(name)
    except Exception:  # ResourceNotFoundError; keep preflight collecting problems
      return None

  def volume_ul(self, container: compat.Container) -> float:
    if container.name not in self._volume_ul:
      self._volume_ul[container.name] = float(container.tracker.get_used_volume())
    return self._volume_ul[container.name]

  def free_volume_ul(self, container: compat.Container) -> float:
    return float(container.max_volume) - self.volume_ul(container)

  def add_volume_ul(self, container: compat.Container, delta_ul: float) -> None:
    self._volume_ul[container.name] = self.volume_ul(container) + delta_ul

  def has_tip(self, tip_spot: Any) -> bool:
    if tip_spot.name not in self._has_tip:
      self._has_tip[tip_spot.name] = bool(tip_spot.tracker.has_tip)
    return self._has_tip[tip_spot.name]

  def take_tip(self, tip_spot: Any) -> None:
    self._has_tip[tip_spot.name] = False


@dataclass
class RunContext:
  lh: compat.LiquidHandler
  num_channels: int
  delay_s: float = 0.0  # pause between steps (useful with the Visualizer)


class Step(Protocol):
  name: str

  def preflight(self, ledger: PreflightLedger) -> list[str]:
    """Static checks only. Return problems (empty list = OK) and update the ledger."""
    ...

  async def run(self, ctx: RunContext) -> None: ...


@dataclass
class Pipeline:
  steps: Sequence[Step]
  on_step: Callable[[int, Step], None] | None = None

  def preflight(self, deck: compat.Deck, num_channels: int) -> None:
    ledger = PreflightLedger(deck=deck, num_channels=num_channels)
    problems: list[str] = []
    for i, step in enumerate(self.steps, start=1):
      for p in step.preflight(ledger):
        problems.append(f"step {i} ({step.name}): {p}")
    if problems:
      raise PreflightError(problems)
    log.info("Preflight OK for %d step(s)", len(self.steps))

  async def run(
    self,
    lh: compat.LiquidHandler,
    num_channels: int,
    delay_s: float = 0.0,
    around: Callable[[compat.LiquidHandler], AbstractAsyncContextManager[Any]] | None = None,
    after_steps: Callable[[], Awaitable[None]] | None = None,
  ) -> None:
    """around: context entered after setup, exited before stop (e.g. the Visualizer).
    after_steps: awaited inside `around` once all steps succeeded (e.g. --hold)."""
    self.preflight(lh.deck, num_channels)  # raises before any setup/motion

    setup_started = False
    try:
      setup_started = True
      await lh.setup()
      ctx = RunContext(lh=lh, num_channels=num_channels, delay_s=delay_s)
      async with (around(lh) if around else nullcontext()):
        await self._run_steps(ctx)
        if after_steps:
          await after_steps()
    finally:
      if setup_started:
        await lh.stop()

  async def _run_steps(self, ctx: RunContext) -> None:
    for i, step in enumerate(self.steps, start=1):
      log.info("step %d/%d START %s", i, len(self.steps), step.name)
      if self.on_step:
        self.on_step(i, step)
      try:
        await step.run(ctx)
      except Exception:
        # No recovery: on hardware, a human inspects the deck before anything moves again.
        log.exception("step %d/%d FAILED %s — stopping run, no recovery", i, len(self.steps), step.name)
        raise
      log.info("step %d/%d DONE %s", i, len(self.steps), step.name)
      if ctx.delay_s > 0:
        await asyncio.sleep(ctx.delay_s)
