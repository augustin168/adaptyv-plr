# Safety rules (always loaded)

A wrong command on the real STAR can crash the pipetting head into labware. These rules apply to
every file and every answer in this project.

## No automatic recovery that moves the robot
- On any error during a run: stop, call `lh.stop()` in `finally`, report. Do not retry, re-home,
  re-pick tips, "move to safe height", or otherwise issue motion to recover.
- Never write `except ...: <motion command>` or retry loops around aspirate/dispense/pick-up/drop/move.
- Recovery on hardware is a human decision after inspecting the deck.

## No invented deck coordinates or tracks
- Positions (track, rail, x/y/z, offsets, heights) come ONLY from the lab layout file
  (`--deck`/`deck=`) or from an explicit instruction by the human in chat.
- Otherwise: a named module-level constant with `# TODO(confirm on machine)`, e.g.
  `DEMO_PLATE_CARRIER_TRACK = 7  # TODO(confirm on machine)`. Never an inline magic number.
- The same applies to channel counts, labware models, liquid classes, and tip types.

## Units in names
- Every physical quantity carries its unit in the variable/argument name:
  `volume_ul`, `z_mm`, `offset_x_mm`, `flow_rate_ul_s`, `delay_s`, `temperature_c`.
- PyLabRobot's own kwargs (e.g. `vols=`) are fine at the call site; wrap with unit-named locals.

## Live hardware
- Never set `PLR_LIVE`, never pass `--mode live`, never construct `STARBackend` outside
  `src/adaptyv_plr/backends.py`. The PreToolUse hook blocks these; do not try to route around it
  (e.g. writing a script that sets the variable). If a task seems to need live hardware, stop and
  ask the human.
