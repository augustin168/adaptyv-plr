"""Demo run of the pipeline harness. Simulation by default.

  python scripts/run_demo.py                                   # headless sim, STARlet
  python scripts/run_demo.py --machine star                    # headless sim, STAR (16 ch)
  python scripts/run_demo.py --viz --delay 2                   # watch at http://127.0.0.1:1337/
  python scripts/run_demo.py --save-layout layouts/demo.json   # write deck layout + state

Live mode is for the operator only: it needs PLR_LIVE=1 in the operator's shell AND typing RUN.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # allow running without install

from adaptyv_plr import deck as deck_mod  # noqa: E402
from adaptyv_plr.backends import LiveModeNotAllowed, make_liquid_handler  # noqa: E402
from adaptyv_plr.config import RunConfig  # noqa: E402
from adaptyv_plr.pipeline import Pipeline, PreflightError  # noqa: E402
from adaptyv_plr.steps import SingleChannelTransfer  # noqa: E402
from adaptyv_plr.viz import visualize  # noqa: E402

DEMO_TRANSFER_VOLUME_UL = 50.0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
  p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  p.add_argument("--mode", choices=["sim", "live"], default="sim")
  p.add_argument("--machine", choices=["star", "starlet"], default="starlet")
  p.add_argument("--sim-backend", choices=["chatterbox", "star-chatterbox"], default="chatterbox")
  p.add_argument("--deck", type=Path, default=None, help="lab layout JSON (default: demo deck)")
  p.add_argument("--viz", action="store_true", help="start the browser Visualizer")
  p.add_argument("--no-browser", action="store_true", help="with --viz: do not open a browser tab")
  p.add_argument("--hold", action="store_true", help="with --viz: keep it open until Enter")
  p.add_argument("--delay", type=float, default=0.0, help="seconds to pause after each step")
  p.add_argument("--save-layout", type=Path, default=None, help="write deck layout (+ state) here")
  return p.parse_args(argv)


def demo_steps() -> list[SingleChannelTransfer]:
  return [
    SingleChannelTransfer(
      tip_rack=deck_mod.TIP_RACK_NAME,
      tip_well="A1",
      source_plate=deck_mod.SOURCE_PLATE_NAME,
      source_well="A1",
      dest_plate=deck_mod.DEST_PLATE_NAME,
      dest_well="A1",
      volume_ul=DEMO_TRANSFER_VOLUME_UL,
    )
  ]


def confirm_live() -> bool:
  if not sys.stdin.isatty():
    print("Live mode needs an interactive terminal to type RUN. Refusing.", file=sys.stderr)
    return False
  answer = input("LIVE HARDWARE. Deck checked, area clear? Type RUN to continue: ")
  return answer.strip() == "RUN"


async def main(argv: list[str] | None = None) -> int:
  args = parse_args(argv)
  logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
  config = RunConfig(mode=args.mode, machine=args.machine, sim_backend=args.sim_backend)

  try:
    lh = make_liquid_handler(config, deck=args.deck)
  except LiveModeNotAllowed as e:
    print(f"REFUSED: {e}", file=sys.stderr)
    return 3

  pipeline = Pipeline(steps=demo_steps())
  try:
    pipeline.preflight(lh.deck, config.channels)
  except PreflightError as e:
    print(e, file=sys.stderr)
    return 2

  if config.mode == "live" and not confirm_live():
    print("Live run not confirmed. Nothing was set up.", file=sys.stderr)
    return 3

  async def hold() -> None:
    if args.viz and args.hold:
      await asyncio.to_thread(input, "Holding Visualizer open. Press Enter to stop... ")

  await pipeline.run(
    lh,
    num_channels=config.channels,
    delay_s=args.delay,
    around=lambda h: visualize(h, enabled=args.viz, open_browser=not args.no_browser),
    after_steps=hold,
  )

  src = lh.deck.get_resource(deck_mod.SOURCE_PLATE_NAME).get_well("A1")
  dst = lh.deck.get_resource(deck_mod.DEST_PLATE_NAME).get_well("A1")
  print(
    f"RESULT machine={config.machine} channels={config.channels} mode={config.mode} "
    f"source_A1_ul={src.tracker.get_used_volume():.1f} dest_A1_ul={dst.tracker.get_used_volume():.1f}"
  )
  if args.save_layout:
    path = deck_mod.save_layout(lh.deck, args.save_layout)
    print(f"Layout saved to {path}")
  return 0


if __name__ == "__main__":
  sys.exit(asyncio.run(main()))
