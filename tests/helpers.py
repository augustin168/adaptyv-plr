from __future__ import annotations

from adaptyv_plr import deck as deck_mod
from adaptyv_plr.steps import SingleChannelTransfer


def transfer(volume_ul: float, tip_well: str = "A1", channel: int = 0, src="A1", dst="A1"):
  return SingleChannelTransfer(
    tip_rack=deck_mod.TIP_RACK_NAME,
    tip_well=tip_well,
    source_plate=deck_mod.SOURCE_PLATE_NAME,
    source_well=src,
    dest_plate=deck_mod.DEST_PLATE_NAME,
    dest_well=dst,
    volume_ul=volume_ul,
    channel=channel,
  )


def well(lh, plate_name: str, well_name: str):
  return lh.deck.get_resource(plate_name).get_well(well_name)
