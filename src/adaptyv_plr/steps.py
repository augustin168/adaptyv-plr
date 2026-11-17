"""Pipeline steps.

=====================================================================================
PLACEHOLDER: SingleChannelTransfer exists to exercise the harness (preflight, tracking,
logging, Visualizer). It is NOT the lab protocol. Liquid classes, flow rates, heights,
and tip strategy are PyLabRobot defaults and have not been validated on our instrument.
=====================================================================================
"""

from __future__ import annotations

from dataclasses import dataclass

from .pipeline import PreflightLedger, RunContext


@dataclass
class SingleChannelTransfer:
  """PLACEHOLDER: one channel: pick up tip -> aspirate -> dispense -> discard tip to trash."""

  tip_rack: str
  tip_well: str
  source_plate: str
  source_well: str
  dest_plate: str
  dest_well: str
  volume_ul: float
  channel: int = 0
  name: str = "single_channel_transfer"

  def preflight(self, ledger: PreflightLedger) -> list[str]:
    problems: list[str] = []
    if self.volume_ul <= 0:
      problems.append(f"volume_ul must be > 0, got {self.volume_ul}")
    if not 0 <= self.channel < ledger.num_channels:
      problems.append(f"channel {self.channel} out of range for {ledger.num_channels} channels")

    rack = ledger.get(self.tip_rack)
    src_plate = ledger.get(self.source_plate)
    dst_plate = ledger.get(self.dest_plate)
    for label, res in (("tip rack", rack), ("source plate", src_plate), ("dest plate", dst_plate)):
      if res is None:
        problems.append(f"{label} not on deck")
    if problems:
      return problems

    tip_spot = rack.get_item(self.tip_well)
    src = src_plate.get_well(self.source_well)
    dst = dst_plate.get_well(self.dest_well)

    if not ledger.has_tip(tip_spot):
      problems.append(f"no tip at {self.tip_rack}:{self.tip_well} (exhausted or already used)")
    else:
      tip_max_ul = float(tip_spot.get_tip().maximal_volume)
      if self.volume_ul > tip_max_ul:
        problems.append(f"volume_ul {self.volume_ul} exceeds tip max {tip_max_ul}")

    available_ul = ledger.volume_ul(src)
    if self.volume_ul > available_ul:
      problems.append(
        f"overdraw: {self.volume_ul} uL requested from {self.source_plate}:{self.source_well}, "
        f"{available_ul} uL available"
      )
    free_ul = ledger.free_volume_ul(dst)
    if self.volume_ul > free_ul:
      problems.append(
        f"overflow: {self.volume_ul} uL into {self.dest_plate}:{self.dest_well}, {free_ul} uL free"
      )

    if not problems:
      ledger.take_tip(tip_spot)
      ledger.add_volume_ul(src, -self.volume_ul)
      ledger.add_volume_ul(dst, self.volume_ul)
    return problems

  async def run(self, ctx: RunContext) -> None:
    deck = ctx.lh.deck
    rack = deck.get_resource(self.tip_rack)
    src_plate = deck.get_resource(self.source_plate)
    dst_plate = deck.get_resource(self.dest_plate)
    ch = [self.channel]
    # PyLabRobot indexing by well name returns a LIST of resources.
    await ctx.lh.pick_up_tips(rack[self.tip_well], use_channels=ch)
    await ctx.lh.aspirate(src_plate[self.source_well], vols=[self.volume_ul], use_channels=ch)
    await ctx.lh.dispense(dst_plate[self.dest_well], vols=[self.volume_ul], use_channels=ch)
    await ctx.lh.discard_tips(use_channels=ch)
